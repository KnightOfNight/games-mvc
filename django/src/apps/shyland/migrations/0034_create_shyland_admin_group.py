# v22 brief 3 (#112/#88, DD §12): the in-game admin Group. Idempotent —
# get_or_create, no members seeded; membership is granted by the operator
# through the Django admin and checked live per attempt.
from django.db import migrations


def create_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name='admins.shyland')


def remove_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name='admins.shyland').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('shyland', '0033_character_home_cooldown_seconds_and_more'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_group, remove_group),
    ]
