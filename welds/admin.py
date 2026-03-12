from django.contrib import admin
from django.utils.html import format_html
from .models import Weld, WeldPhoto, WeldIdKey


@admin.register(Weld)
class WeldAdmin(admin.ModelAdmin):
    list_display = ('section', 'weld_id4', 'side', 'weld_type', 'pass_fail', 'report', 'date')
    list_filter = ('side', 'pass_fail', 'weld_type', 'report')
    search_fields = ('section', 'weld_id', 'inspector')


@admin.register(WeldPhoto)
class WeldPhotoAdmin(admin.ModelAdmin):
    list_display = ('photo_preview', 'section', 'subfolder', 'report_number', 'description')
    list_filter = ('report_number', 'section', 'subfolder')
    search_fields = ('section', 'description', 'original_filename', 'subfolder')
    readonly_fields = ('photo_preview_large', 'original_filename')
    list_per_page = 50

    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" style="max-height:60px;" />', obj.photo.url)
        return "No photo"
    photo_preview.short_description = 'Preview'

    def photo_preview_large(self, obj):
        if obj.photo:
            return format_html('<img src="{}" style="max-height:500px;" />', obj.photo.url)
        return "No photo"
    photo_preview_large.short_description = 'Photo'


@admin.register(WeldIdKey)
class WeldIdKeyAdmin(admin.ModelAdmin):
    list_display = ('code', 'meaning', 'created_at')
    search_fields = ('code', 'meaning')
    ordering = ('code',)