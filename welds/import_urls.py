from django.urls import path
from . import import_views

urlpatterns = [
    path('', import_views.import_page, name='import_page'),
    path('photos/', import_views.import_photo, name='import_photo'),
    path('welds/', import_views.import_welds_excel, name='import_welds_excel'),
]
