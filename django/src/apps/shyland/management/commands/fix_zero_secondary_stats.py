from django.core.management.base import BaseCommand

from apps.shyland.item_utils import _roll_stat
from apps.shyland.models import ItemInstance


class Command(BaseCommand):
    help = (
        'v21 B3 (#68 Q4): one-time cleanup of zero-value secondary stats '
        'stored on existing ItemInstances. Each zero entry is re-rolled '
        'through the same _roll_stat math using the definition\'s current '
        '(corrected) pool parameters at the instance\'s own Mk tier and '
        'rarity. The stat identity is kept; only the value changes. '
        'Idempotent: the corrected proc curves (0.5/0.2) roll >= 1 at '
        'every Mk tier and rarity, so a second run finds nothing to fix.'
    )

    def handle(self, *args, **options):
        items_scanned = 0
        items_fixed = 0
        entries_fixed = 0
        entries_left = 0

        for item in ItemInstance.objects.select_related(
                'definition', 'owner').iterator():
            items_scanned += 1
            if not any(e.get('value') == 0 for e in item.rolled_secondary_stats):
                continue

            pool = {e['stat']: e for e in item.definition.secondary_stat_pool}
            owner = item.owner.name if item.owner else 'unowned'
            label = (f'{item.definition.name} #{item.pk} '
                     f'(Mk {item.mk_tier} {item.rarity}, {owner})')
            changed = False

            for entry in item.rolled_secondary_stats:
                if entry.get('value') != 0:
                    continue
                params = pool.get(entry['stat'])
                if params is None:
                    entries_left += 1
                    self.stdout.write(self.style.WARNING(
                        f'  {label}: {entry["stat"]} is no longer in the '
                        'definition pool — left at 0.'
                    ))
                    continue
                new_value = _roll_stat(
                    params['base'], params['factor'], item.mk_tier, item.rarity)
                if new_value == 0:
                    # This stat's authored curve still permits a zero at this
                    # Mk/rarity (it is not one of the #68-corrected stats).
                    # Leave the stored entry untouched so repeated runs never
                    # flap values.
                    entries_left += 1
                    self.stdout.write(self.style.WARNING(
                        f'  {label}: {entry["stat"]} re-rolled 0 under its '
                        'authored curve — left at 0.'
                    ))
                    continue
                self.stdout.write(
                    f'  {label}: {entry["stat"]} 0 -> {new_value}')
                entry['value'] = new_value
                entries_fixed += 1
                changed = True

            if changed:
                item.save(update_fields=['rolled_secondary_stats'])
                items_fixed += 1

        self.stdout.write(self.style.SUCCESS(
            f'{items_scanned} instances scanned; {entries_fixed} zero '
            f'entr{"y" if entries_fixed == 1 else "ies"} re-rolled on '
            f'{items_fixed} item(s); {entries_left} left at 0.'
        ))
