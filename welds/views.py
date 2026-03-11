from datetime import date

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q
from welds.models import Weld
from welds.export_utils import generate_excel_response, generate_pdf_response


def _apply_weld_filters(request):
    """Apply weld_list GET filters and return a queryset."""
    side = request.GET.get('side')
    section = request.GET.get('section')
    weld_id = request.GET.get('weld_id')
    weld_type = request.GET.get('weld_type')
    pass_fail = request.GET.get('pass_fail')
    report = request.GET.get('report')
    search = request.GET.get('search')

    queryset = Weld.objects.all()
    if side:
        queryset = queryset.filter(side=side)
    if section:
        queryset = queryset.filter(section__icontains=section)
    if weld_id:
        queryset = queryset.filter(weld_id__icontains=weld_id)
    if weld_type:
        queryset = queryset.filter(weld_type=weld_type)
    if pass_fail:
        queryset = queryset.filter(pass_fail=pass_fail)
    if report:
        queryset = queryset.filter(report=report)
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
                       ('pass_fail', 'Status'), ('report', 'Report'), ('search', 'Search')]:
        val = request.GET.get(key)
        if val:
            parts.append(f"{label}: {val}")
    return ", ".join(parts) if parts else "None"


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
    }

    return render(request, 'welds/weld_list.html', context)


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


def export_welds_excel(request):
    queryset = _apply_weld_filters(request)
    filename = f"weld_data_export_{date.today().strftime('%Y-%m-%d')}.xlsx"
    return generate_excel_response(queryset, filename)


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