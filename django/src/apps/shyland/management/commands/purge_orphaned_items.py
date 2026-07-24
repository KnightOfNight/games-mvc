from django.core.management.base import BaseCommand, CommandError

from apps.shyland.models import ItemInstance


class Command(BaseCommand):
    help = (
        'v23 B2 (#137): one-time purge of orphaned ItemInstances — rows '
        'with owner, current_room, and corpse all NULL (corpse-decay '
        'leftovers from the pre-CASCADE on_delete=SET_NULL era). The '
        'count is checked at run time, never assumed. After deleting, '
        'the orphan query is re-run and must count zero — the command '
        'fails loudly otherwise. Idempotent: a second run finds zero '
        'orphans and deletes nothing.'
    )

    def _orphans(self):
        return ItemInstance.objects.filter(
            owner__isnull=True,
            current_room__isnull=True,
            corpse__isnull=True,
        )

    def handle(self, *args, **options):
        found = self._orphans().count()
        self.stdout.write(f'{found} orphaned item instance(s) found.')

        deleted = 0
        if found:
            _, deleted_map = self._orphans().delete()
            deleted = deleted_map.get('shyland.ItemInstance', 0)

        remaining = self._orphans().count()
        self.stdout.write(f'{deleted} deleted; {remaining} remaining.')

        if remaining != 0:
            raise CommandError(
                f'Post-run orphan count is {remaining}, expected 0 — '
                'the database is NOT clean.'
            )
        self.stdout.write(self.style.SUCCESS(
            'Post-run orphan count is 0 — database clean.'
        ))
