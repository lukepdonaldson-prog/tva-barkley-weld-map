from django.urls import path
from . import views

urlpatterns = [
    path('', views.weld_list, name='weld_list'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('section-map/', views.section_map, name='section_map'),
    path('weld/<int:pk>/', views.weld_detail, name='weld_detail'),
    path('weld/<int:pk>/update/', views.weld_update, name='weld_update'),
    path('weld/<int:pk>/clear-validation/', views.weld_clear_validation, name='weld_clear_validation'),
    path('weld/<int:pk>/unclear-validation/', views.weld_unclear_validation, name='weld_unclear_validation'),
    path('export/excel/', views.export_welds_excel, name='export_welds_excel'),
    path('export/pdf/', views.export_welds_pdf, name='export_welds_pdf'),
    path('incomplete/', views.incomplete_records, name='incomplete_records'),
    path('incomplete/export/excel/', views.export_incomplete_excel, name='export_incomplete_excel'),
    path('bulk-clear-validation/', views.weld_bulk_clear_validation, name='weld_bulk_clear_validation'),
    path('bulk-clear-all-filtered/', views.weld_bulk_clear_all_filtered, name='weld_bulk_clear_all_filtered'),
    path('weld-id-key/', views.weld_id_key, name='weld_id_key'),
    path('weld-id-key/create/', views.weld_id_key_create, name='weld_id_key_create'),
    path('weld-id-key/<int:pk>/update/', views.weld_id_key_update, name='weld_id_key_update'),
    path('weld-id-key/<int:pk>/delete/', views.weld_id_key_delete, name='weld_id_key_delete'),
]
