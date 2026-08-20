from django.urls import path

from apps.shyship.consumers import ShyshipConsumer
from apps.shyland.consumers import SkylandConsumer
from apps.shyland.mc_consumer import MCEgressConsumer

websocket_urlpatterns = [
    path('ws/shyship/<uuid:game_id>/', ShyshipConsumer.as_asgi()),
    path('ws/shyland/', SkylandConsumer.as_asgi()),
    path('ws/shyland/mc/', MCEgressConsumer.as_asgi()),
]
