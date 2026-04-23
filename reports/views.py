from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from .models import NDEReport, REPORT_TYPE_CHOICES
from .forms import NDEReportUploadForm


@login_required
def report_list(request):
    reports = NDEReport.objects.all()

    report_type = request.GET.get('report_type', '')
    section = request.GET.get('section', '')
    search = request.GET.get('search', '')

    if report_type:
        reports = reports.filter(report_type=report_type)
    if section:
        reports = reports.filter(section__icontains=section)
    if search:
        reports = reports.filter(
            Q(title__icontains=search) |
            Q(notes__icontains=search) |
            Q(section__icontains=search)
        )

    count_all = NDEReport.objects.count()
    count_filtered = reports.count()
    count_ut = NDEReport.objects.filter(report_type='UT').count()
    count_mt = NDEReport.objects.filter(report_type='MT').count()

    paginator = Paginator(reports, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    sections = NDEReport.objects.values_list('section', flat=True).order_by('section').distinct().exclude(section='')

    return render(request, 'reports/report_list.html', {
        'page_obj': page_obj,
        'count_all': count_all,
        'count_filtered': count_filtered,
        'count_ut': count_ut,
        'count_mt': count_mt,
        'report_types': REPORT_TYPE_CHOICES,
        'sections': sections,
        'selected_type': report_type,
        'selected_section': section,
        'search': search,
    })


@login_required
def report_upload(request):
    if request.method == 'POST':
        form = NDEReportUploadForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.uploaded_by = request.user.username
            report.save()
            return redirect('report_list')
    else:
        form = NDEReportUploadForm()

    return render(request, 'reports/report_upload.html', {'form': form})


@login_required
def report_view(request, pk):
    report = get_object_or_404(NDEReport, pk=pk)
    return render(request, 'reports/report_view.html', {'report': report})


@login_required
def report_delete(request, pk):
    report = get_object_or_404(NDEReport, pk=pk)
    if request.method == 'POST':
        report.report_file.delete(save=False)
        report.delete()
        return redirect('report_list')
    return render(request, 'reports/report_confirm_delete.html', {'report': report})
