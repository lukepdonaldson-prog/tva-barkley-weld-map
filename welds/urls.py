from django.urls import path
from . import views

urlpatterns = [
    path('', views.weld_list, name='weld_list'),
    path('weld/<int:pk>/', views.weld_detail, name='weld_detail'),
]
