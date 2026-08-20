# v25.3 brief 1 (#267, GDD §10.11): the MC agent Group. Idempotent —
# get_or_create, no members seeded; agent service accounts are created
# operationally by the operator and membership is checked live at connect.
from django.db import migrations


def create_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name='agents.shyland')


def remove_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name='agents.shyland').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('shyland', '0050_mcevent'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_group, remove_group),
    ]
