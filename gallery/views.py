from django.shortcuts import render
from welds.models import Weld, WeldPhoto
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required

@login_required
def qa_dashboard(request):
    welds = Weld.objects.all()

    # Filtering
    section = request.GET.get('section', '')
    report = request.GET.get('report', '')
    pass_fail = request.GET.get('pass_fail', '')
    search = request.GET.get('search', '')

    if section:
        welds = welds.filter(section=section)
    if report:
        welds = welds.filter(report=report)
    if pass_fail:
        welds = welds.filter(pass_fail=pass_fail)
    if search:
        welds = welds.filter(
            Q(weld_id4__icontains=search) |
            Q(inspector__icontains=search) |
            Q(note__icontains=search)
        )

    count_all = Weld.objects.count()
    count_filtered = welds.count()

    pass_count = welds.filter(pass_fail__iexact='pass').count()
    fail_count = welds.filter(pass_fail__iexact='fail').count()

    welds = welds.order_by('section', 'weld_id4')

    paginator = Paginator(welds, 50)
    page_number = request.GET.get('page')
    welds_page = paginator.get_page(page_number)

    sections = Weld.objects.values_list('section', flat=True).order_by('section').distinct()
    reports = Weld.objects.values_list('report', flat=True).order_by('report').distinct()
    statuses = Weld.objects.values_list('pass_fail', flat=True).order_by('pass_fail').distinct().exclude(pass_fail='')

    return render(request, 'gallery/qa_dashboard.html', {
        'welds': welds_page,
        'count_all': count_all,
        'count_filtered': count_filtered,
        'pass_count': pass_count,
        'fail_count': fail_count,
        'sections': sections,
        'reports': reports,
        'statuses': statuses,
        'selected_section': section,
        'selected_report': report,
        'selected_status': pass_fail,
        'search': search,
    })

def photo_gallery(request):
    photos = WeldPhoto.objects.all()

    section = request.GET.get('section', '')
    report = request.GET.get('report_number', '')
    subfolder = request.GET.get('subfolder', '')
    search = request.GET.get('search', '')

    if section:
        photos = photos.filter(section__icontains=section)
    if report:
        photos = photos.filter(report_number__icontains=report)
    if subfolder:
        photos = photos.filter(subfolder__icontains=subfolder)
    if search:
        photos = photos.filter(
            Q(description__icontains=search) |
            Q(original_filename__icontains=search)
        )

    photos = photos.order_by('-uploaded_at')

    paginator = Paginator(photos, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    sections = WeldPhoto.objects.values_list('section', flat=True).order_by('section').distinct()
    reports = WeldPhoto.objects.values_list('report_number', flat=True).order_by('report_number').distinct()
    subfolders = WeldPhoto.objects.values_list('subfolder', flat=True).order_by('subfolder').distinct()

    return render(request, 'gallery/gallery.html', {
        'page_obj': page_obj,
        'count_all': WeldPhoto.objects.count(),
        'count_filtered': photos.count(),
        'sections': sections,
        'reports': reports,
        'subfolders': subfolders,
        'selected_section': section,
        'selected_report': report,
        'selected_subfolder': subfolder,
        'search': search,
    })
