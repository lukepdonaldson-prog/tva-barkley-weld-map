from django.contrib import admin
from .models import NDEReport


@admin.register(NDEReport)
class NDEReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'report_type', 'section', 'uploaded_at', 'uploaded_by']
    list_filter = ['report_type', 'section']
    search_fields = ['title', 'notes', 'section']
