from .base import *

DEBUG = False

_domain   = env('DOMAIN')
_port     = env('HOST_PORT', default='443')

ALLOWED_HOSTS = [_domain]
CSRF_TRUSTED_ORIGINS = [
    f"https://{_domain}",
    f"https://{_domain}:{_port}",
]

# nginx terminates SSL and sets this header
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
