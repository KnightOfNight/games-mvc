# Shyland v23.4 brief 1 (#162): home cooldown 15 minutes -> 5 minutes.
#
# The default change (0038) reaches only new characters — the field is a
# per-player override. Set every existing row to 300 unconditionally,
# admin-overridden values included (operator ruling 2026-07-29: "then we
# know they're right"). Reverse is a no-op — the pre-migration per-row
# values are deliberately not preserved.

from django.db import migrations


def reset_home_cooldowns(apps, schema_editor):
    Character = apps.get_model('shyland', 'Character')
    Character.objects.update(home_cooldown_seconds=300)


class Migration(migrations.Migration):

    dependencies = [
        ('shyland', '0038_alter_character_home_cooldown_seconds'),
    ]

    operations = [
        migrations.RunPython(reset_home_cooldowns, migrations.RunPython.noop),
    ]
