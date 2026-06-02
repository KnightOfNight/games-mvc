from django.apps import AppConfig


class ShyshipConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.shyship'

    def ready(self):
        from django.db.models.signals import post_migrate
        post_migrate.connect(_create_players_group, sender=self)


def _create_players_group(sender, **kwargs):
    from django.contrib.auth.models import Group
    Group.objects.get_or_create(name='players.shyship')
