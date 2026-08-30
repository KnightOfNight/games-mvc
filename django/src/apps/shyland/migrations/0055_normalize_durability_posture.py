# V25.12 Brief 1 (#311, #314): authored data migration — normalize any
# row sitting in the incoherent durability posture before 0056's
# durability_posture_coherent CheckConstraint lands. Forward-only; the
# normalizations are idempotent and reversing them would re-create the
# broken states the release exists to eliminate.

from datetime import datetime, timezone

from django.db import migrations


def _utc_stamp():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def normalize_durability_posture(apps, schema_editor):
    ItemDefinition = apps.get_model('shyland', 'ItemDefinition')
    ItemInstance = apps.get_model('shyland', 'ItemInstance')

    # Definitions (#311): wear on + empty table is the broken default
    # pair — flip to the non-wearing posture (table stays []).
    broken = ItemDefinition.objects.filter(
        takes_durability_loss=True, durability_table=[])
    count = broken.count()
    broken.update(takes_durability_loss=False)
    print(f'{_utc_stamp()} 0055_normalize_durability_posture: '
          f'definitions flipped non-wearing (was wear-on + empty table): '
          f'{count}')

    # Instances (#314 completing move): durability is integral — any
    # fractional durability_current normalizes to the display's own
    # convention (int(round(...))), with is_broken re-derived.
    fixed = 0
    for item in ItemInstance.objects.all().iterator():
        if item.durability_current == int(item.durability_current):
            continue
        item.durability_current = float(int(round(item.durability_current)))
        item.is_broken = (item.durability_current == 0)
        item.save(update_fields=['durability_current', 'is_broken'])
        fixed += 1
    print(f'{_utc_stamp()} 0055_normalize_durability_posture: '
          f'instances normalized to integral durability: {fixed}')


class Migration(migrations.Migration):

    dependencies = [
        ('shyland', '0054_agentmemory'),
    ]

    operations = [
        migrations.RunPython(normalize_durability_posture,
                             migrations.RunPython.noop),
    ]
