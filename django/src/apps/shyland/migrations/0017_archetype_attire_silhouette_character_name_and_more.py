# Data migration: adds Character.name in three steps (nullable add → backfill
# from gamer_tag/username → non-null + case-insensitive unique constraint) so
# it applies safely on databases that already contain Character rows.

from django.db import migrations, models
from django.db.models.functions import Lower


def backfill_names(apps, schema_editor):
    """Give every existing Character the name the removed property computed:
    user.profile.gamer_tag falling back to user.username, truncated to 20
    chars and deduplicated case-insensitively."""
    Character = apps.get_model('shyland', 'Character')
    UserProfile = apps.get_model('profiles', 'UserProfile')

    used = set()
    for character in Character.objects.select_related('user').order_by('pk'):
        tag = (
            UserProfile.objects
            .filter(user_id=character.user_id)
            .values_list('gamer_tag', flat=True)
            .first()
        )
        base = (tag or character.user.username).strip()[:20] or f'Character{character.pk}'
        candidate = base
        counter = 2
        while candidate.lower() in used:
            suffix = str(counter)
            candidate = base[:20 - len(suffix)] + suffix
            counter += 1
        used.add(candidate.lower())
        character.name = candidate
        character.save(update_fields=['name'])


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0001_initial'),
        ('shyland', '0016_npcdefinition_combat_tier_room_no_exit_down_msg_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='archetype',
            name='attire_silhouette',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.AddField(
            model_name='origin',
            name='attire_material',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.AddField(
            model_name='character',
            name='name',
            field=models.CharField(max_length=20, null=True),
        ),
        migrations.RunPython(backfill_names, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='character',
            name='name',
            field=models.CharField(max_length=20),
        ),
        migrations.AddConstraint(
            model_name='character',
            constraint=models.UniqueConstraint(
                Lower('name'),
                name='shyland_character_name_ci_unique',
                violation_error_message='That name is already taken.',
            ),
        ),
    ]
