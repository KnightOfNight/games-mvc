from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from .views import HomeView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('admin/', admin.site.urls),
    path('admin/defender/', include('defender.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('api/auth/', include('rest_framework.urls')),
    # Game apps register their URL patterns here.
    # Example:
    #   path('battleship/', include('apps.battleship.urls')),
    path('shydle', include('apps.shydle.urls')),
    path('shydle/', RedirectView.as_view(url='/shydle', permanent=True)),
    path('shyship/', include('apps.shyship.urls')),
    path('shyland/', include('apps.shyland.urls')),
    path('shyland', RedirectView.as_view(url='/shyland/play/', permanent=False)),
]
