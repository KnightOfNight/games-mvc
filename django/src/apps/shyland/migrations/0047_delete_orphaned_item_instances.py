# v24.27 (#234): pre-existing hard-delete orphans. Before 0046, deleting a
# character SET_NULL'd ItemInstance.owner, leaving rows with owner,
# current_room, and corpse all NULL — a state outside the exactly-one-location
# invariant and unreachable by any game path. Unconditional deletion is always
# correct by that definition (same logic as the #137 corpse-contents ruling).
# The reverse is a deliberate no-op: the orphans carry no recoverable state.

from django.db import migrations


def delete_orphans(apps, schema_editor):
    ItemInstance = apps.get_model('shyland', 'ItemInstance')
    deleted, _ = ItemInstance.objects.filter(
        owner__isnull=True,
        current_room__isnull=True,
        corpse__isnull=True,
    ).delete()
    print(f'0047: deleted {deleted} orphaned ItemInstance row(s)')


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('shyland', '0046_alter_iteminstance_owner'),
    ]

    operations = [
        migrations.RunPython(delete_orphans, reverse_noop),
    ]
