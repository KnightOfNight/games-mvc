from django.urls import path

from apps.shyship.consumers import ShyshipConsumer

websocket_urlpatterns = [
    path('ws/shyship/<uuid:game_id>/', ShyshipConsumer.as_asgi()),
]
