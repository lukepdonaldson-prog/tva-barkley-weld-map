from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from django.views.generic import RedirectView
from welds.user_views import (
    user_list, user_create, user_update, user_delete, user_reset_password
)

urlpatterns = [
    path('', login_required(RedirectView.as_view(url='/welds/dashboard/', permanent=False))),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/users/', user_list, name='user_management'),
    path('accounts/users/create/', user_create, name='user_create'),
    path('accounts/users/<int:pk>/update/', user_update, name='user_update'),
    path('accounts/users/<int:pk>/delete/', user_delete, name='user_delete'),
    path('accounts/users/<int:pk>/reset-password/', user_reset_password, name='user_reset_password'),
    path('gallery/', include('gallery.urls')),
    path('reports/', include('reports.urls')),
    path('welds/', include('welds.urls')),
    path('import/', include('welds.import_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
