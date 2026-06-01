import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'game_mvc.settings.production')

application = get_wsgi_application()
