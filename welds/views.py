from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q
from welds.models import Weld

def weld_list(request):
    # Get filter parameters from GET request
    side = request.GET.get('side')
    section = request.GET.get('section')
    weld_id = request.GET.get('weld_id')
    weld_type = request.GET.get('weld_type')
    pass_fail = request.GET.get('pass_fail')
    report = request.GET.get('report')
    search = request.GET.get('search')

    # Start with all welds
    queryset = Weld.objects.all()

    # Apply filters
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