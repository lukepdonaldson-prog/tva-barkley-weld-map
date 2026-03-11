from django.urls import path
from . import views

urlpatterns = [
    path('', views.photo_gallery, name='photo_gallery'),
    path('export/excel/', views.export_photos_excel, name='export_photos_excel'),
    path('export/zip/', views.export_photos_zip, name='export_photos_zip'),
    path('qa-dashboard/', views.qa_dashboard, name='qa_dashboard'),
    path('qa-dashboard/export/excel/', views.export_qa_excel, name='export_qa_excel'),
    path('qa-dashboard/export/pdf/', views.export_qa_pdf, name='export_qa_pdf'),
]
