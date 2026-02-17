from django.contrib import admin
from .models import Weld, WeldPhoto

# Register your models here.
@admin.register(Weld)
class WeldAdmin(admin.ModelAdmin):
    list_display = ('section', 'weld_id4', 'side', 'weld_type', 'pass_fail', 'report', 'date')
    list_filter = ('side', 'pass_fail', 'weld_type', 'report')
    search_fields = ('section', 'weld_id', 'inspector')

@admin.register(WeldPhoto)
class WeldPhotoAdmin(admin.ModelAdmin):
    list_display = ('weld', 'report_number', 'photo')
