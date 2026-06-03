from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import CancelView, ForfeitView, GameView, LobbyView, ShyshipLoginView, VsComputerView

app_name = 'shyship'

urlpatterns = [
    path('', LobbyView.as_view(), name='lobby'),
    path('<uuid:game_id>/', GameView.as_view(), name='game'),
    path('<uuid:game_id>/cancel/', CancelView.as_view(), name='cancel'),
    path('<uuid:game_id>/forfeit/', ForfeitView.as_view(), name='forfeit'),
    path('<uuid:game_id>/vs-computer/', VsComputerView.as_view(), name='vs_computer'),
    path('login/', ShyshipLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
]
