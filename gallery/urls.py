from django.urls import path
from . import views

urlpatterns = [
    path('', views.photo_gallery, name='photo_gallery'),
    path('qa-dashboard/', views.qa_dashboard, name='qa_dashboard'),
]
