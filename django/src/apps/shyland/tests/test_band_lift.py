"""v24.14 Brief 1 (#130): the gear-stat band-lift doctrine.

Every seeded stat entry carries the band-lift shape from GDD §6: full-lift
entries author `base = 0.25 × m1, factor = 0.75 × m1` (so factor = 3 ×
base), the proc-factor family authors half-power `0.625 × m1 / 0.375 × m1`
(so factor = 0.6 × base), floor pairs take the full lift, and crit_chance
is exempt and keeps its shallow pre-lift curves. This pins the doctrine
shape for every current and future authored item — not today's literals.
"""

import io

from django.core.management import call_command
from django.test import TestCase

from apps.shyland.combat_utils import PROC_FACTOR_STATS
from apps.shyland.models import ItemDefinition

TOL = 1e-6


class BandLiftDoctrineTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command('seed_world', stdout=io.StringIO())

    def iter_entries(self):
        for defn in ItemDefinition.objects.all():
            for entry in (defn.primary_stats or []):
                yield defn.slug, 'primary', entry
            for entry in (defn.secondary_stat_pool or []):
                yield defn.slug, 'secondary', entry

    def test_every_entry_carries_its_class_shape(self):
        seen = 0
        for slug, kind, entry in self.iter_entries():
            seen += 1
            stat = entry['stat']
            base, factor = entry['base'], entry['factor']
            where = f'{slug} {kind} {stat} ({base}/{factor})'
            if stat == 'crit_chance':
                # Exempt: must NOT carry the full-lift shape — crit keeps
                # its shallow authored curves.
                self.assertGreater(abs(factor - 3 * base), TOL, where)
            elif stat in PROC_FACTOR_STATS:
                # Half-power lift: 0.625/0.375 × m1 → factor = 0.6 × base.
                self.assertAlmostEqual(factor, 0.6 * base, delta=TOL,
                                       msg=where)
            else:
                # Full lift: 0.25/0.75 × m1 → factor = 3 × base.
                self.assertAlmostEqual(factor, 3 * base, delta=TOL,
                                       msg=where)
        # The seeded world authors stat entries; an empty iteration would
        # mean the seed changed shape out from under this test.
        self.assertGreater(seen, 0)

    def test_floor_pairs_take_the_full_lift(self):
        seen = 0
        for slug, kind, entry in self.iter_entries():
            if 'floor_base' not in entry and 'floor_factor' not in entry:
                continue
            seen += 1
            fb, ff = entry['floor_base'], entry['floor_factor']
            self.assertAlmostEqual(
                ff, 3 * fb, delta=TOL,
                msg=f"{slug} {kind} {entry['stat']} floor ({fb}/{ff})")
        # v24.10's two identity-proc weapons are the only floored entries.
        self.assertEqual(seen, 2)
