# V25.16 Brief 1 (#315): authored data migration — normalize any
# instance stranded in the instance-side incoherent posture (damaged or
# broken state on a non-wearing definition) before the door's shape-A
# refusal lands and removes the only recovery path. Forward pass resets
# such instances to healthy; reverse is a noop (reversing would
# re-create the unrecoverable state the release exists to eliminate).

from datetime import datetime, timezone

from django.db import migrations


def _utc_stamp():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def normalize_nonwearing_instances(apps, schema_editor):
    ItemInstance = apps.get_model('shyland', 'ItemInstance')

    stranded = ItemInstance.objects.filter(
        definition__takes_durability_loss=False).exclude(
        durability_current=100.0, is_broken=False)
    count = stranded.count()
    stranded.update(durability_current=100.0, is_broken=False)
    print(f'{_utc_stamp()} 0057_normalize_nonwearing_instances: '
          f'normalized {count} non-wearing instances')


class Migration(migrations.Migration):

    dependencies = [
        ('shyland', '0056_alter_itemdefinition_durability_table_and_more'),
    ]

    operations = [
        migrations.RunPython(normalize_nonwearing_instances,
                             migrations.RunPython.noop),
    ]
