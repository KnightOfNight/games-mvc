from django.urls import path

from apps.shyship.consumers import ShyshipConsumer
from apps.shyland.consumers import SkylandConsumer

websocket_urlpatterns = [
    path('ws/shyship/<uuid:game_id>/', ShyshipConsumer.as_asgi()),
    path('ws/shyland/', SkylandConsumer.as_asgi()),
]
