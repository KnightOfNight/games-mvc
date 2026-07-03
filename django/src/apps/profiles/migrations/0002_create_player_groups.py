from django.db import migrations


PLAYER_GROUPS = [
    'players.shyship',
    'players.shydle',
    'players.shyland',
]


def create_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    for name in PLAYER_GROUPS:
        Group.objects.get_or_create(name=name)


def delete_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=PLAYER_GROUPS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_groups, delete_groups),
    ]
