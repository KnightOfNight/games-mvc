from .base import *

DEBUG = False

ALLOWED_HOSTS = [env('DOMAIN')]

# nginx terminates SSL and sets this header
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
