from django.shortcuts import render
from welds.models import WeldPhoto
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required

@login_required
def qa_dashboard(request):
    return render(request, 'gallery/qa_dashboard.html', {}) 

def photo_gallery(request):
    photos = WeldPhoto.objects.all()

    # Filtering
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

    # Sorting (newest first)
    photos = photos.order_by('-uploaded_at')

    # Pagination
    paginator = Paginator(photos, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # For dropdowns
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