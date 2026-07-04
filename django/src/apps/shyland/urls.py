from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'shyland'

urlpatterns = [
    path('play/', views.GameView.as_view(), name='game'),
    path('create/', views.CharacterCreateView.as_view(), name='create_character'),
    path('create/check-name/', views.CheckNameView.as_view(), name='check_name'),
    path('', RedirectView.as_view(url='/shyland/play/', permanent=False)),
]
