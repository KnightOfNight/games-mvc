from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.profiles'

    def ready(self):
        from django.db.models.signals import post_save
        from django.contrib.auth.models import User
        post_save.connect(_create_profile, sender=User)


def _create_profile(sender, instance, created, **kwargs):
    if created:
        from apps.profiles.models import UserProfile
        UserProfile.objects.get_or_create(user=instance)
