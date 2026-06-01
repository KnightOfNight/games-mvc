from django.conf import settings


def site_settings(request):
    return {
        'SITE_TITLE': getattr(settings, 'SITE_TITLE', 'game-mvc'),
    }
