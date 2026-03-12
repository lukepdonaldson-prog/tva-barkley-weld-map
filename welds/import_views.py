import re
import os
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from .models import Weld, WeldPhoto


# ---------------------------------------------------------------------------
# Helper utilities (ported from management commands)
# ---------------------------------------------------------------------------

def _normalize_section(section):
    """Insert dash between letters and digits, e.g. AX6 -> AX-6."""
    fixed = re.sub(r'^([A-Za-z]+)(\d)', r'\1-\2', section)
    return fixed.upper()


def _extract_section_from_filename(filename):
    """Try to pull a section like AX-6.3 from the start of the filename."""
    name = os.path.splitext(filename)[0]
    # Strip leading numbers (e.g., "01 AX-6.3 ...")
    name = re.sub(r'^\d+\s+', '', name)

    match = re.match(
        r'^([A-Za-z]{1,3}[-.]?\d+(?:\.\d+)?(?:\([A-Za-z0-9]+\))?)\s*(.*)',
        name,
    )
    if match:
        section = _normalize_section(match.group(1))
        description = match.group(2).strip()
        return section, description

    return '', name


def _shorten_filename(filename, max_base=80):
    """Shorten long filenames to avoid Django's max_length issues."""
    name, ext = os.path.splitext(filename)
    if len(name) > max_base:
        name = name[:max_base]
    return name + ext


# ---------------------------------------------------------------------------
# Excel helper utilities (openpyxl-based, no pandas)
# ---------------------------------------------------------------------------

def _to_int_or_default(val, default=0):
    if val is None or val == '':
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def _to_float_or_none(val):
    if val is None or val == '':
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _to_string(val):
    if val is None:
        return ''
    return str(val).strip()


def _to_date(val):
    if val is None or val == '':
        return None
    if isinstance(val, datetime):
        return val.date()
    from datetime import date as _date
    if isinstance(val, _date):
        return val
    if isinstance(val, str):
        for fmt in ('%m/%d/%Y', '%Y-%m-%d', '%m/%d/%y'):
            try:
                return datetime.strptime(val.strip(), fmt).date()
            except ValueError:
                continue
    return None


# ---------------------------------------------------------------------------
# Import page view
# ---------------------------------------------------------------------------

@login_required
def import_page(request):
    return render(request, 'welds/import.html')


# ---------------------------------------------------------------------------
# Photo import endpoint
# ---------------------------------------------------------------------------

@login_required
@csrf_protect
@require_POST
def import_photo(request):
    photo_file = request.FILES.get('photo')
    if not photo_file:
        return JsonResponse({'status': 'error', 'message': 'No photo file provided.'}, status=400)

    # Validate file type
    allowed_extensions = {'.jpg', '.jpeg', '.png'}
    _, ext = os.path.splitext(photo_file.name.lower())
    if ext not in allowed_extensions:
        return JsonResponse(
            {'status': 'error', 'message': f'Invalid file type "{ext}". Only .jpg, .jpeg, .png are allowed.'},
            status=400,
        )

    original_filename = request.POST.get('original_filename', photo_file.name)
    subfolder = request.POST.get('subfolder', '')
    report_number = request.POST.get('report_number', '')
    section = request.POST.get('section', '')
    description = request.POST.get('description', '')

    # If section not provided, try to derive it from the filename
    if not section:
        section, derived_desc = _extract_section_from_filename(original_filename)
        if not description:
            description = derived_desc

    # If report_number not provided by client, try to extract from subfolder
    # e.g. subfolder "Report 29" → "29"
    if not report_number and subfolder:
        m = re.match(r'^report\s+(\d+[A-Za-z]?)$', subfolder, re.IGNORECASE)
        if m:
            report_number = m.group(1)

    # If still no section, try from subfolder
    if not section and subfolder:
        match = re.match(r'^([A-Za-z]{1,3}[-.]?\d+(?:\.\d+)?)', subfolder)
        if match:
            section = _normalize_section(match.group(1))

    safe_filename = _shorten_filename(original_filename)

    # Detect duplicate: same original_filename + report_number → replace
    existing = WeldPhoto.objects.filter(
        original_filename=original_filename[:500],
        report_number=report_number,
    ).first()

    if existing:
        existing.section = section
        existing.subfolder = subfolder
        existing.description = description
        if existing.photo:
            existing.photo.delete(save=False)
        existing.photo.save(safe_filename, ContentFile(photo_file.read()), save=True)
        weld_photo = existing
        replaced = True
    else:
        weld_photo = WeldPhoto(
            section=section,
            report_number=report_number,
            subfolder=subfolder,
            description=description,
            original_filename=original_filename[:500],
        )
        weld_photo.photo.save(safe_filename, ContentFile(photo_file.read()), save=True)
        replaced = False

    return JsonResponse({'status': 'ok', 'id': weld_photo.pk, 'replaced': replaced})


# ---------------------------------------------------------------------------
# Excel weld import endpoint
# ---------------------------------------------------------------------------

@login_required
@csrf_protect
@require_POST
def import_welds_excel(request):
    excel_file = request.FILES.get('file')
    if not excel_file:
        return JsonResponse({'status': 'error', 'message': 'No file provided.'}, status=400)

    _, ext = os.path.splitext(excel_file.name.lower())
    if ext != '.xlsx':
        return JsonResponse(
            {'status': 'error', 'message': f'Invalid file type "{ext}". Only .xlsx files are allowed.'},
            status=400,
        )

    # Import mode: "replace_all" deletes all existing welds first; "update_add" (default) only updates/adds
    mode = request.POST.get('mode', 'update_add')

    try:
        import openpyxl
        wb = openpyxl.load_workbook(excel_file, read_only=True, data_only=True)
        ws = wb.active
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Could not read Excel file: {e}'}, status=400)

    # Read header row
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return JsonResponse({'status': 'error', 'message': 'Excel file is empty.'}, status=400)

    headers = [str(h).strip() if h is not None else '' for h in rows[0]]

    # Build column-index lookup
    col_index = {h: i for i, h in enumerate(headers)}

    # Find MT column (any column containing "MT" in its name)
    mt_col_name = None
    for h in headers:
        if 'MT' in h.upper():
            mt_col_name = h
            break

    def get(row, col_name, default=None):
        idx = col_index.get(col_name)
        if idx is None:
            return default
        val = row[idx] if idx < len(row) else default
        return val

    # If Replace All mode, delete all existing weld records first
    deleted_count = 0
    if mode == 'replace_all':
        deleted_count, _ = Weld.objects.all().delete()

    created_count = 0
    updated_count = 0
    skipped_count = 0
    errors = []

    for row_num, row in enumerate(rows[1:], start=2):
        section_raw = get(row, 'Section')
        section = _to_string(section_raw)
        if not section:
            skipped_count += 1
            continue

        weld_id4 = _to_string(get(row, 'Weld ID4'))

        weld_data = {
            'report': _to_int_or_default(get(row, 'Report'), 0),
            'side': _to_string(get(row, 'Side')),
            'section': section,
            'weld_id': _to_string(get(row, 'Weld ID')),
            'weld_id2': _to_string(get(row, 'Weld ID2')),
            'weld_id3': _to_string(get(row, 'Weld ID3')),
            'weld_id4': weld_id4,
            'estimated_repair_length': _to_float_or_none(get(row, 'Estimated Repair Length')),
            'total_weld_length': _to_float_or_none(get(row, 'Total Weld Length')),
            'table_6_1_criteria_1': _to_string(get(row, 'Table 6.1 AWS Visual Inspection Criteria 1')),
            'table_6_1_criteria_2': _to_string(get(row, 'Table 6.1 AWS Visual Inspection Criteria 2')),
            'table_6_1_criteria_3': _to_string(get(row, 'Table 6.1 AWS Visual Inspection Criteria 3')),
            'weld_type': _to_string(get(row, 'Weld Type')),
            'weld_size': _to_string(get(row, 'Weld Size')),
            'wps_number': _to_string(get(row, 'WPS #')) or 'DWPS-SM-Special-B-3-N Rev 0',
            'inspection_utsw': _to_string(get(row, 'Inspection UTSW')),
            'inspection_mt': _to_string(get(row, mt_col_name)) if mt_col_name else '',
            'inspector': _to_string(get(row, 'Inspector')),
            'date': _to_date(get(row, 'Date')),
            'pass_fail': _to_string(get(row, 'Pass_Fail')),
            'corrective_action_taken': _to_string(get(row, 'Corrective Action Taken')),
            'repair_welder': _to_string(get(row, 'Repair Welder')),
            'repair_inspection_date': _to_date(get(row, 'Repair Inspection Date')),
            'weld_process': _to_string(get(row, 'Weld Process')),
            'note': _to_string(get(row, 'Note')),
        }

        try:
            _, created = Weld.objects.update_or_create(
                section=weld_data['section'],
                weld_id4=weld_data['weld_id4'],
                defaults=weld_data,
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
        except Exception as e:
            errors.append(f'Row {row_num}: {e}')

    return JsonResponse({
        'status': 'ok',
        'created': created_count,
        'updated': updated_count,
        'deleted': deleted_count,
        'skipped': skipped_count,
        'errors': errors,
    })
