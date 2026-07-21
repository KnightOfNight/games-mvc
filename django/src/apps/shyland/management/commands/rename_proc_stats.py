from django.core.management.base import BaseCommand

from apps.shyland.models import ItemInstance


class Command(BaseCommand):
    help = (
        'v22 B5 (#100): one-time rename of the proc-factor stats stored on '
        'existing ItemInstances — bleed_chance -> bleed_factor, stun_chance '
        '-> stun_factor, poison_chance -> poison_factor. Ruled: the *_chance '
        'names lie under the B5 semantics (the rolled value is a factor '
        'driving both frequency and size). Walks every instance\'s '
        'rolled_primary_stats and rolled_secondary_stats and renames the '
        'three keys in place; no value changes. Idempotent: a second run '
        'finds no old-named entries. Deploy-time, operator-directed — the '
        'reseed renames the definition pools; this command renames the '
        'already-rolled instances.'
    )

    RENAMES = {
        'bleed_chance': 'bleed_factor',
        'stun_chance': 'stun_factor',
        'poison_chance': 'poison_factor',
    }

    def handle(self, *args, **options):
        items_scanned = 0
        items_changed = 0
        entries_renamed = 0

        for item in ItemInstance.objects.select_related(
                'definition', 'owner').iterator():
            items_scanned += 1
            changed_fields = []

            for field in ('rolled_primary_stats', 'rolled_secondary_stats'):
                entries = getattr(item, field) or []
                field_changed = False
                for entry in entries:
                    new_name = self.RENAMES.get(entry.get('stat'))
                    if new_name is None:
                        continue
                    owner = item.owner.name if item.owner else 'unowned'
                    self.stdout.write(
                        f'  {item.definition.name} #{item.pk} '
                        f'(Mk {item.mk_tier} {item.rarity}, {owner}): '
                        f'{entry["stat"]} -> {new_name}'
                    )
                    entry['stat'] = new_name
                    entries_renamed += 1
                    field_changed = True
                if field_changed:
                    changed_fields.append(field)

            if changed_fields:
                item.save(update_fields=changed_fields)
                items_changed += 1

        self.stdout.write(self.style.SUCCESS(
            f'{items_scanned} instances scanned; {entries_renamed} '
            f'entr{"y" if entries_renamed == 1 else "ies"} renamed on '
            f'{items_changed} item(s).'
        ))
