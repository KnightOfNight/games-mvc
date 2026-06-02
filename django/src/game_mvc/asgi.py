import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'game_mvc.settings.production')

from django.core.asgi import get_asgi_application

# Must be called before any imports that touch the ORM or app registry.
django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from game_mvc.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
