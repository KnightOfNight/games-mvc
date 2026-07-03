from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'shyland'

urlpatterns = [
    path('play/', views.GameView.as_view(), name='game'),
    path('', RedirectView.as_view(url='/shyland/play/', permanent=False)),
]
