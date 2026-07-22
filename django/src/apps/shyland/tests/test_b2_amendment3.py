"""v22 brief 2 amendment 3: pane recolors (source conformance) and the
per-zone travel listing with harvested stone sentences."""

import re
from pathlib import Path

from asgiref.sync import sync_to_async
from django.test import SimpleTestCase, TransactionTestCase

from apps.shyland import consumers
from apps.shyland.models import (
    Room, RoomVisit, TravelNode, Zone,
)
from apps.shyland.tests.test_command_revamp import (
    make_character, make_stub_consumer,
)


class PaneRecolorConformanceTests(SimpleTestCase):
    """Step 2/3 CSS reads, pinned at the source (pure CSS by design)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        path = (Path(consumers.__file__).parent
                / 'templates' / 'shyland' / 'game.html')
        cls.html = path.read_text()

    def _decl(self, selector):
        m = re.search(re.escape(selector) + r'\s*\{([^}]*)\}', self.html)
        self.assertIsNotNone(m, selector)
        return m.group(1)

    def test_fight_panel_reads_error_and_value(self):
        self.assertIn('var(--error)', self._decl('.fight-focus'))
        self.assertIn('border: 1px solid var(--error)', self._decl('.fight-bar'))
        self.assertIn('background: var(--error)', self._decl('.fight-fill'))
        self.assertIn('var(--value-color)', self._decl('.fight-name'))
        self.assertIn('var(--value-color)', self._decl('.fight-nums'))

    def test_stats_pane_reads_value_and_error(self):
        self.assertIn('var(--value-color)', self._decl('#stats-name '))
        self.assertIn('var(--error)',
                      self._decl('#side-stats.in-combat #stats-name'))
        self.assertIn('var(--value-color)', self._decl('.bar-label'))
        self.assertIn('var(--value-color)', self._decl('.bar-num'))

    def test_gauge_tick_geometry_16_by_4(self):
        decl = self._decl('.gauge-tick')
        self.assertIn('top: -4px', decl)
        self.assertIn('bottom: -4px', decl)
        self.assertIn('width: 4px', decl)
        self.assertIn('margin-left: -2px', decl)
        self.assertIn('var(--say-color)', decl)

    def test_no_text_var_among_the_changed_selectors(self):
        for selector in ('.fight-focus', '.fight-name', '.fight-bar',
                         '.fight-fill', '.fight-nums', '#stats-name ',
                         '.bar-label', '.bar-num'):
            self.assertNotIn('var(--text)', self._decl(selector), selector)


class TravelListingTests(TransactionTestCase):
    """Step 4: per-zone blocks, hardness order, harvested sentences."""

    def _network(self):
        convergence = Zone.objects.create(
            name='The Convergence', slug='the-convergence',
            genre_tone='Test', danger_level='sanctuary',
            description='x', theme_color='#CCAA77',
        )
        verdant = Zone.objects.create(
            name='The Verdant Reach', slug='the-verdant-reach',
            genre_tone='Test', danger_level='beginner',
            description='x', theme_color='#40B58C',
        )

        def room(zone, name, x, y):
            return Room.objects.create(
                zone=zone, name=name, description='Long.',
                brief_description='Brief.', coord_x=x, coord_y=y,
            )

        heart = room(convergence, 'Heart', 0, 0)
        crown = room(verdant, 'Crown', 0, 58)
        ford = room(verdant, 'Fordwatch', 0, 5)

        TravelNode.objects.create(
            room=heart, travel_name='The Convergence', node_type='obelisk',
            listing_description='At the center of everything stands the Obelisk.',
        )
        TravelNode.objects.create(
            room=crown, travel_name='The Verdant Crown', node_type='obelisk',
            listing_description='Eden on the roof of the world, and a green sphere in an obelisk.',
        )
        TravelNode.objects.create(
            room=ford, travel_name='Fordwatch', node_type='checkpoint',
            listing_description='A green shard drifts above the crossing where the fog gives way.',
        )

        char = make_character('tl', crown)
        for r in (heart, crown, ford):
            RoomVisit.objects.create(character=char, room=r)
        return char, convergence, verdant

    async def test_listing_blocks_order_columns_and_sentences(self):
        char, convergence, verdant = await sync_to_async(self._network)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_travel('')

        report = next(m for m in sent if m.get('category') == 'report')
        lines = report['lines']

        def flat(entry):
            if 'segs' in entry:
                return ''.join(seg['t'] for seg in entry['segs'])
            return (entry.get('k', '') or '') + (entry.get('v', '') or '')

        texts = [flat(entry) for entry in lines]
        self.assertEqual(texts[0], 'The Obelisk offers passage to...')

        # Hardness order: Convergence block before Verdant Reach block.
        conv_idx = texts.index('Zone: The Convergence')
        verd_idx = texts.index('Zone: The Verdant Reach')
        self.assertLess(conv_idx, verd_idx)

        # The zone name seg carries the zone's theme color (the licensed
        # hex exception).
        conv_heading = lines[conv_idx]['segs']
        self.assertEqual(conv_heading[0], {'t': 'Zone: ', 'c': 'key'})
        self.assertEqual(conv_heading[1]['x'], convergence.theme_color)

        # Columns, capitalized types, harvested sentences verbatim.
        headers = [t for t in texts
                   if 'Type' in t and 'Destination' in t and 'Description' in t]
        self.assertEqual(len(headers), 2)
        # Identical column x-geometry across both tables.
        self.assertEqual(len(set(headers)), 1)

        joined = '\n'.join(texts)
        self.assertIn('Sphere', joined)
        self.assertIn('Shard', joined)
        self.assertNotIn('sphere)', joined)
        self.assertIn('At the center of everything stands the Obelisk.', joined)
        self.assertIn(
            'A green shard drifts above the crossing where the fog gives way.',
            joined,
        )

    def test_listing_description_field_and_seed_pin(self):
        # Migration surface: the field exists with a blank default.
        field = TravelNode._meta.get_field('listing_description')
        self.assertTrue(field.blank)
        self.assertEqual(field.default, '')
        # Seed pin: the harvested sentences live in the seed verbatim
        # (the enforce-exact check runs in seed-verify on reseed).
        import inspect
        from apps.shyland.management.commands import seed_world
        source = inspect.getsource(seed_world)
        for sentence in (
            'At the center of everything stands the Obelisk.',
            'A green shard drifts above the crossing where the fog gives way.',
            'A green shard rides the wind above a trodden waystation.',
            "A green shard warms itself by a fire at the mountains' feet.",
            'Eden on the roof of the world, and a green sphere in an obelisk.',
        ):
            self.assertIn(sentence, source)
        self.assertIn(
            'TravelNode listing_descriptions match the harvested stone sentences',
            source,
        )
