from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# Override with a safe default for local dev if not set in .env
SECRET_KEY = env('DJANGO_SECRET_KEY', default='local-dev-key-not-for-production')

# Use in-memory channel layer for local dev without Redis
# Remove this block to use Redis (requires Redis container to be running)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}
