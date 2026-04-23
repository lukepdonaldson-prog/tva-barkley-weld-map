from django.urls import path
from . import views

urlpatterns = [
    path('', views.report_list, name='report_list'),
    path('upload/', views.report_upload, name='report_upload'),
    path('<int:pk>/view/', views.report_view, name='report_view'),
    path('<int:pk>/delete/', views.report_delete, name='report_delete'),
]
