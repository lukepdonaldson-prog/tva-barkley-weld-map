from django.urls import path
from . import views

urlpatterns = [
    path('', views.weld_list, name='weld_list'),
    path('weld/<int:pk>/', views.weld_detail, name='weld_detail'),
    path('export/excel/', views.export_welds_excel, name='export_welds_excel'),
    path('export/pdf/', views.export_welds_pdf, name='export_welds_pdf'),
]
