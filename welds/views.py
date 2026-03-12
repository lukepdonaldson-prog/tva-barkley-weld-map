import json
from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q
from welds.models import Weld
from welds.export_utils import generate_excel_response, generate_pdf_response

# Fields that may be edited via the inline-edit API
_WELD_EDITABLE_FIELDS = {
    'report', 'side', 'section', 'weld_id', 'weld_id2', 'weld_id3', 'weld_id4',
    'estimated_repair_length', 'total_weld_length',
    'table_6_1_criteria_1', 'table_6_1_criteria_2', 'table_6_1_criteria_3',
    'weld_type', 'weld_size', 'wps_number',
    'inspection_utsw', 'inspection_mt', 'inspector', 'date',
    'pass_fail', 'corrective_action_taken', 'repair_welder',
    'repair_inspection_date', 'weld_process', 'note',
}


def _apply_weld_filters(request):
    """Apply weld_list GET filters and return a queryset."""
    side = request.GET.get('side')
    section = request.GET.get('section')
    weld_id = request.GET.get('weld_id')
    weld_type = request.GET.get('weld_type')
    pass_fail = request.GET.get('pass_fail')
    report = request.GET.get('report')
    search = request.GET.get('search')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    inspector = request.GET.get('inspector')

    queryset = Weld.objects.all()
    if side:
        queryset = queryset.filter(side=side)
    if section:
        queryset = queryset.filter(section=section)
    if weld_id:
        queryset = queryset.filter(weld_id__icontains=weld_id)
    if weld_type:
        queryset = queryset.filter(weld_type=weld_type)
    if pass_fail:
        queryset = queryset.filter(pass_fail=pass_fail)
    if report:
        queryset = queryset.filter(report=report)
    if date_from:
        queryset = queryset.filter(date__gte=date_from)
    if date_to:
        queryset = queryset.filter(date__lte=date_to)
    if inspector:
        queryset = queryset.filter(inspector=inspector)
    if search:
        queryset = queryset.filter(
            Q(section__icontains=search) |
            Q(weld_id__icontains=search) |
            Q(weld_id4__icontains=search) |
            Q(inspector__icontains=search) |
            Q(note__icontains=search)
        )
    return queryset


def _build_filters_desc(request):
    """Return a human-readable string describing active filters."""
    parts = []
    for key, label in [('side', 'Side'), ('section', 'Section'), ('weld_type', 'Type'),
                       ('pass_fail', 'Status'), ('report', 'Report'), ('inspector', 'Inspector'),
                       ('date_from', 'From'), ('date_to', 'To'), ('search', 'Search')]:
        val = request.GET.get(key)
        if val:
            parts.append(f"{label}: {val}")
    return ", ".join(parts) if parts else "None"


@login_required
def weld_list(request):
    queryset = _apply_weld_filters(request)

    # Calculate aggregates, case-insensitive for pass/fail
    aggregates = queryset.aggregate(
        total_count=Count('id'),
        total_repair_length=Sum('estimated_repair_length'),
        total_weld_length=Sum('total_weld_length'),
        pass_count=Count('id', filter=Q(pass_fail__iexact='pass')),
        fail_count=Count('id', filter=Q(pass_fail__iexact='fail'))
    )

    # Get distinct values for filter dropdowns
    sides = Weld.objects.values_list('side', flat=True).distinct()
    weld_types = Weld.objects.values_list('weld_type', flat=True).distinct()
    reports = Weld.objects.values_list('report', flat=True).distinct()
    pass_fail_choices = Weld.objects.values_list('pass_fail', flat=True).distinct()
    sections = Weld.objects.values_list('section', flat=True).order_by('section').distinct()
    inspectors = Weld.objects.values_list('inspector', flat=True).order_by('inspector').distinct().exclude(inspector='')

    # Paginate results
    paginator = Paginator(queryset, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'welds': page_obj.object_list,
        'aggregates': aggregates,
        'sides': sides,
        'weld_types': weld_types,
        'reports': reports,
        'pass_fail_choices': pass_fail_choices,
        'sections': sections,
        'inspectors': inspectors,
    }

    return render(request, 'welds/weld_list.html', context)


@login_required
def weld_detail(request, pk):
    # Get single weld
    weld = get_object_or_404(Weld, pk=pk)

    # Get previous and next weld by pk
    previous_weld = Weld.objects.filter(pk__lt=pk).order_by('-pk').first()
    next_weld = Weld.objects.filter(pk__gt=pk).order_by('pk').first()

    context = {
        'weld': weld,
        'previous_weld': previous_weld,
        'next_weld': next_weld,
    }

    return render(request, 'welds/weld_detail.html', context)


@login_required
def export_welds_excel(request):
    queryset = _apply_weld_filters(request)
    filename = f"weld_data_export_{date.today().strftime('%Y-%m-%d')}.xlsx"
    return generate_excel_response(queryset, filename)


@login_required
def export_welds_pdf(request):
    queryset = _apply_weld_filters(request)
    filename = f"weld_report_{date.today().strftime('%Y-%m-%d')}.pdf"
    filters_desc = _build_filters_desc(request)
    return generate_pdf_response(
        queryset,
        filename,
        title="TVA Barkley Dam \u2014 Weld Inspection Report",
        filters_desc=filters_desc,
    )


@login_required
@require_POST
def weld_update(request, pk):
    """AJAX endpoint: update editable fields on a Weld record."""
    weld = get_object_or_404(Weld, pk=pk)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    for field, value in data.items():
        if field not in _WELD_EDITABLE_FIELDS:
            return JsonResponse(
                {'success': False, 'error': f'Field "{field}" is not editable'},
                status=400,
            )
        field_meta = Weld._meta.get_field(field)
        # Convert empty string to None for nullable fields
        if value == '' and getattr(field_meta, 'null', False):
            value = None
        setattr(weld, field, value)

    try:
        weld.full_clean()
        weld.save()
    except Exception as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)

    return JsonResponse({'success': True})