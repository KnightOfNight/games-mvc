from django.contrib import admin
from django.urls import path, include
from .views import HomeView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('api/auth/', include('rest_framework.urls')),
    # Game apps register their URL patterns here.
    # Example:
    #   path('battleship/', include('apps.battleship.urls')),
    path('shydle/', include('apps.shydle.urls')),
]
