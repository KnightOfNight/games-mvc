"""V24.7 Brief 1 (#195, #176, #194): equipment display.

The display says "two-handed" and shows its consequences. Bare `equip`
renders the Equipment paper-doll through the shared composition helper
(#195; its sole consumer since the v24.16 inv trim, #208); consumed
hand slots name their consumer, muted (#176);
handed-ness is disclosed in examine, the listing Slot cell, and the
hands-conflict refusal clause (#194). Zero mechanics changes — targeted
equip behavior is byte-identical outside the refusal clause; the combat
gate follows the act, not the verb (bare form allowed).
"""

from asgiref.sync import sync_to_async

from django.test import SimpleTestCase, TransactionTestCase
from django.utils import timezone

from apps.shyland.consumers import SkylandConsumer
from apps.shyland.models import (
    CombatSession, ItemDefinition, ItemInstance, NpcDefinition, NpcInstance,
)
from apps.shyland.tests.test_b2_amendment1 import line_texts
from apps.shyland.tests.test_command_revamp import (
    make_character, make_stub_consumer, make_world, outputs,
)


def make_weapon_def(prefix, name, valid_slots, two_handed=False,
                    ranged=False):
    return ItemDefinition.objects.create(
        name=name, slug=f'{prefix}-{name.lower().replace(" ", "-")}',
        item_type='weapon', genre_tag='fantasy', valid_slots=valid_slots,
        scaling_base=3.0, scaling_factor=1.0, base_value=10,
        takes_durability_loss=True, is_two_handed=two_handed,
        is_ranged=ranged,
        # v25.12 (#311): explicit all-worn band — preserves the
        # retired empty-table fallback these fixtures ran under.
        durability_table=[{'min': 0, 'max': 100, 'penalty': 1.0}],
    )


def make_armor_def(prefix, name, valid_slots):
    return ItemDefinition.objects.create(
        name=name, slug=f'{prefix}-{name.lower().replace(" ", "-")}',
        item_type='armor', genre_tag='fantasy', valid_slots=valid_slots,
        scaling_base=0.0, scaling_factor=0.0, base_value=5,
        takes_durability_loss=True,
        durability_table=[{'min': 0, 'max': 100, 'penalty': 1.0}],
    )


def make_instance(defn, char, slot=None, midpoint=None, spread=None):
    return ItemInstance.objects.create(
        definition=defn, owner=char, mk_tier=1, rarity='common',
        durability_current=100.0, is_identified=True,
        is_equipped=slot is not None, equipped_slot=slot or '',
        damage_midpoint=midpoint, damage_spread=spread,
    )


def report_lines(sent):
    """The raw lines of the first report message."""
    return next(m for m in sent if m.get('category') == 'report'
                and 'lines' in m)['lines']


def row_segs(lines, label):
    """The segs of the first table row whose text starts with `label`."""
    for entry in lines:
        if 'segs' in entry:
            text = ''.join(seg['t'] for seg in entry['segs'])
            if text.strip().startswith(label):
                return entry['segs'], text
    raise AssertionError(f'no row labelled {label!r}')


class BareEquipTests(TransactionTestCase):
    """#195: the bare form is the paper-doll, nothing else, shared."""

    async def test_bare_equip_is_the_paper_doll_only(self):
        zone, room = await sync_to_async(make_world)('e7a')
        char = await sync_to_async(make_character)('e7a', room)

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_equip('')
        lines, texts = line_texts(sent)

        self.assertEqual(texts[0], 'Equipment...')
        # 13 anatomical slots, RING twice = 14 slot rows after the
        # muted column-header line.
        slot_rows = [t for t in texts[2:] if t.strip()]
        self.assertEqual(len(slot_rows), 14)
        self.assertFalse(any('Inventory (' in t for t in texts))
        self.assertFalse(any('Wallet:' in t for t in texts))

    async def test_bare_equip_matches_paper_doll_helper_byte_identical(self):
        # v24.16 (#208) re-oracle: inv no longer renders the doll, so
        # the original intent — the paper-doll composition is pinned as
        # bare `equip`'s exact render — is asserted against
        # `_equipment_doll_lines(equipped)` rendered directly.
        zone, room = await sync_to_async(make_world)('e7b')

        def setup():
            char = make_character('e7b', room)
            axe = make_weapon_def('e7b', 'Battle Axe', ['MAIN_HAND'],
                                  two_handed=True)
            make_instance(axe, char, slot='MAIN_HAND', midpoint=5.0,
                          spread=1.0)
            return char
        char = await sync_to_async(setup)()

        bare_sent = []
        consumer = make_stub_consumer(char, bare_sent)
        await consumer.cmd_equip('   ')
        bare = report_lines(bare_sent)
        # The shared-composition guarantee: bare `equip` is the helper's
        # render, byte for byte — nothing added, nothing dropped.
        equipped = await consumer.get_equipped_items(char)
        expected = consumer._equipment_doll_lines(equipped)
        self.assertEqual(bare, expected)

    async def test_whitespace_only_args_are_bare(self):
        zone, room = await sync_to_async(make_world)('e7c')
        char = await sync_to_async(make_character)('e7c', room)
        sent = []
        await make_stub_consumer(char, sent).cmd_equip('  ')
        self.assertTrue(any(m.get('category') == 'report' for m in sent))


class ConsumedRowTests(TransactionTestCase):
    """#176: consumed hand slots name their consumer, muted."""

    async def test_two_hander_in_main_hand_consumes_off_hand(self):
        zone, room = await sync_to_async(make_world)('e7d')

        def setup():
            char = make_character('e7d', room)
            axe = make_weapon_def('e7d', 'Battle Axe', ['MAIN_HAND'],
                                  two_handed=True)
            make_instance(axe, char, slot='MAIN_HAND')
            return char
        char = await sync_to_async(setup)()

        sent = []
        await make_stub_consumer(char, sent).cmd_equip('')
        lines = report_lines(sent)

        # Home row: normal rendering — plain-string name cell (value
        # voice), real Details.
        main_segs, main_text = row_segs(lines, 'Main hand')
        self.assertIn('Battle Axe Mk 1', main_text)
        self.assertIn('100%', main_text)
        self.assertFalse(any(s['t'] == 'Battle Axe Mk 1'
                             and s['c'] == 'muted' for s in main_segs))

        # Consumed row: muted name-with-tier, muted (two-handed).
        off_segs, off_text = row_segs(lines, 'Off hand')
        self.assertTrue(any(s['t'] == 'Battle Axe Mk 1'
                            and s['c'] == 'muted' for s in off_segs))
        self.assertTrue(any(s['t'] == '(two-handed)'
                            and s['c'] == 'muted' for s in off_segs))

    async def test_two_hander_in_ranged_consumes_both_hand_rows(self):
        zone, room = await sync_to_async(make_world)('e7e')

        def setup():
            char = make_character('e7e', room)
            bow = make_weapon_def('e7e', 'Hunting Bow', ['RANGED'],
                                  two_handed=True, ranged=True)
            make_instance(bow, char, slot='RANGED')
            return char
        char = await sync_to_async(setup)()

        sent = []
        await make_stub_consumer(char, sent).cmd_equip('')
        lines = report_lines(sent)

        for label in ('Main hand', 'Off hand'):
            segs, _ = row_segs(lines, label)
            self.assertTrue(any(s['t'] == 'Hunting Bow Mk 1'
                                and s['c'] == 'muted' for s in segs), label)
            self.assertTrue(any(s['t'] == '(two-handed)'
                                and s['c'] == 'muted' for s in segs), label)

        ranged_segs, ranged_text = row_segs(lines, 'Ranged')
        self.assertIn('100%', ranged_text)
        self.assertFalse(any(s['t'] == '(two-handed)'
                             for s in ranged_segs))

    async def test_no_two_hander_keeps_muted_dashes(self):
        zone, room = await sync_to_async(make_world)('e7f')

        def setup():
            char = make_character('e7f', room)
            mace = make_weapon_def('e7f', 'Iron Mace', ['MAIN_HAND'])
            make_instance(mace, char, slot='MAIN_HAND')
            return char
        char = await sync_to_async(setup)()

        sent = []
        await make_stub_consumer(char, sent).cmd_equip('')
        lines = report_lines(sent)
        off_segs, _ = row_segs(lines, 'Off hand')
        self.assertTrue(any(s['t'] == '-' and s['c'] == 'muted'
                            for s in off_segs))
        self.assertFalse(any('two-handed' in s['t'] for s in off_segs))


class HandsDisclosureTests(TransactionTestCase):
    """#194: examine's Hands: row and the listing Slot-cell word."""

    async def test_examine_two_handed_weapon(self):
        zone, room = await sync_to_async(make_world)('e7g')

        def setup():
            char = make_character('e7g', room)
            bow = make_weapon_def('e7g', 'Hunting Bow', ['RANGED'],
                                  two_handed=True, ranged=True)
            item = make_instance(bow, char, midpoint=5.0, spread=1.0)
            return char, item
        char, item = await sync_to_async(setup)()

        consumer = make_stub_consumer(char, [])
        lines = consumer._format_identified_item_lines(item)
        self.assertIn('  Hands:      Two-handed', lines)
        # Placed immediately after the Damage: row.
        damage_idx = next(i for i, l in enumerate(lines)
                          if l.startswith('  Damage:'))
        self.assertEqual(lines[damage_idx + 1], '  Hands:      Two-handed')

    async def test_examine_one_handed_weapon_and_no_damage_row(self):
        zone, room = await sync_to_async(make_world)('e7h')

        def setup():
            char = make_character('e7h', room)
            mace = make_weapon_def('e7h', 'Iron Mace', ['MAIN_HAND'])
            # No rolled damage fields: Hands follows Genre directly.
            item = make_instance(mace, char)
            return char, item
        char, item = await sync_to_async(setup)()

        consumer = make_stub_consumer(char, [])
        lines = consumer._format_identified_item_lines(item)
        self.assertIn('  Hands:      One-handed', lines)
        genre_idx = next(i for i, l in enumerate(lines)
                         if l.startswith('  Genre:'))
        self.assertEqual(lines[genre_idx + 1], '  Hands:      One-handed')

    async def test_examine_armor_has_no_hands_row(self):
        zone, room = await sync_to_async(make_world)('e7i')

        def setup():
            char = make_character('e7i', room)
            helm = make_armor_def('e7i', 'Iron Helm', ['HEAD'])
            item = make_instance(helm, char)
            return char, item
        char, item = await sync_to_async(setup)()

        consumer = make_stub_consumer(char, [])
        lines = consumer._format_identified_item_lines(item)
        self.assertFalse(any(l.startswith('  Hands:') for l in lines))


class SlotCellTests(TransactionTestCase):
    """#194: the Slot cell appends the word for two-handers only."""

    async def test_slot_cell_variants(self):
        def setup():
            bow = make_weapon_def('e7j', 'Hunting Bow', ['RANGED'],
                                  two_handed=True, ranged=True)
            axe = make_weapon_def('e7j', 'Battle Axe', ['MAIN_HAND'],
                                  two_handed=True)
            mace = make_weapon_def('e7j', 'Iron Mace', ['MAIN_HAND'])
            helm = make_armor_def('e7j', 'Iron Helm', ['HEAD'])
            hide = ItemDefinition.objects.create(
                name='Animal Hide', slug='e7j-animal-hide',
                item_type='material', genre_tag='fantasy', valid_slots=[],
                scaling_base=0.0, scaling_factor=0.0, base_value=1,
                durability_table=[{'min': 0, 'max': 100, 'penalty': 1.0}],
            )
            return bow, axe, mace, helm, hide
        bow, axe, mace, helm, hide = await sync_to_async(setup)()

        cell = SkylandConsumer._slot_cell
        self.assertEqual(cell(bow), 'Ranged (two-handed)')
        self.assertEqual(cell(axe), 'Main hand (two-handed)')
        self.assertEqual(cell(mace), 'Main hand')
        self.assertEqual(cell(helm), 'Head')
        self.assertEqual(cell(hide), [('-', 'muted')])


class RefusalClauseTests(TransactionTestCase):
    """#194: hands-conflict refusals name the two-hander; everything
    else keeps its standing wording byte-identically."""

    async def test_two_hander_refusal_carries_the_clause(self):
        zone, room = await sync_to_async(make_world)('e7k')

        def setup():
            char = make_character('e7k', room)
            mace = make_weapon_def('e7k', 'Iron Mace', ['MAIN_HAND'])
            shield = make_armor_def('e7k', 'Wooden Buckler', ['OFF_HAND'])
            axe = make_weapon_def('e7k', 'Battle Axe', ['MAIN_HAND'],
                                  two_handed=True)
            make_instance(mace, char, slot='MAIN_HAND')
            make_instance(shield, char, slot='OFF_HAND')
            make_instance(axe, char)
            return char
        char = await sync_to_async(setup)()

        sent = []
        await make_stub_consumer(char, sent).cmd_equip('battle axe')
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['category'], 'warn')
        self.assertEqual(
            msgs[0]['text'],
            "You'd have to unequip your Iron Mace and your Wooden Buckler "
            "first — the Battle Axe Mk 1 needs both hands.",
        )

    async def test_rings_refusal_is_byte_identical(self):
        zone, room = await sync_to_async(make_world)('e7l')

        def setup():
            char = make_character('e7l', room)
            band = ItemDefinition.objects.create(
                name='Copper Band', slug='e7l-copper-band',
                item_type='accessory', genre_tag='fantasy',
                valid_slots=['RING'], scaling_base=0.0, scaling_factor=0.0,
                base_value=2,
                durability_table=[{'min': 0, 'max': 100, 'penalty': 1.0}],
            )
            signet = ItemDefinition.objects.create(
                name='Silver Signet', slug='e7l-silver-signet',
                item_type='accessory', genre_tag='fantasy',
                valid_slots=['RING'], scaling_base=0.0, scaling_factor=0.0,
                base_value=2,
                durability_table=[{'min': 0, 'max': 100, 'penalty': 1.0}],
            )
            third = ItemDefinition.objects.create(
                name='Gold Loop', slug='e7l-gold-loop',
                item_type='accessory', genre_tag='fantasy',
                valid_slots=['RING'], scaling_base=0.0, scaling_factor=0.0,
                base_value=2,
                durability_table=[{'min': 0, 'max': 100, 'penalty': 1.0}],
            )
            make_instance(band, char, slot='RING')
            make_instance(signet, char, slot='RING')
            make_instance(third, char)
            return char
        char = await sync_to_async(setup)()

        sent = []
        await make_stub_consumer(char, sent).cmd_equip('gold loop')
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(
            msgs[0]['text'],
            "Both ring slots are full — unequip your Copper Band or "
            "your Silver Signet first.",
        )


class CombatGateTests(TransactionTestCase):
    """#195 addendum: the gate follows the act — bare equip renders in
    combat; targeted equip keeps the standing refusal."""

    def _combat(self, char, room, prefix):
        definition = NpcDefinition.objects.create(
            name=f'{prefix} snarler', slug=f'{prefix}-snarler',
            description='x', genre_tag='fantasy', is_aggressive=True,
            base_vitality=10, base_str=1, base_dex=1, base_end=1,
            base_int=1, base_wis=1, base_per=1,
        )
        npc = NpcInstance.objects.create(
            definition=definition, current_room=room, spawn_room=room,
            vitality_current=10, vitality_max=10,
        )
        session = CombatSession.objects.create(
            room=room, last_tick_at=timezone.now(),
        )
        session.characters.add(char)
        session.npcs.add(npc)
        return session

    async def test_bare_equip_renders_in_combat(self):
        zone, room = await sync_to_async(make_world)('e7m')
        char = await sync_to_async(make_character)('e7m', room)
        await sync_to_async(self._combat)(char, room, 'e7m')

        for verb in ('equip', 'eq'):
            sent = []
            await make_stub_consumer(char, sent)._dispatch(verb, '')
            lines, texts = line_texts(sent)
            self.assertEqual(texts[0], 'Equipment...', verb)
            self.assertFalse(any(m.get('category') == 'warn'
                                 for m in sent), verb)

    async def test_targeted_equip_keeps_the_combat_refusal(self):
        zone, room = await sync_to_async(make_world)('e7n')
        char = await sync_to_async(make_character)('e7n', room)
        await sync_to_async(self._combat)(char, room, 'e7n')

        sent = []
        await make_stub_consumer(char, sent)._dispatch('equip', 'axe')
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['category'], 'warn')
        self.assertEqual(msgs[0]['text'],
                         "There's no time to fiddle with your gear mid-fight!")


class TableTests(SimpleTestCase):
    """The dispatch-table deltas: equip left PROMPT_VERBS; the help
    usage row shows the optional target."""

    def test_equip_left_prompt_verbs(self):
        self.assertNotIn('equip', SkylandConsumer.PROMPT_VERBS)
        self.assertNotIn('eq', SkylandConsumer.PROMPT_VERBS)

    def test_equip_still_in_grammar_verbs(self):
        self.assertEqual(SkylandConsumer.GRAMMAR_VERBS.get('equip'), 'equip')
        self.assertEqual(SkylandConsumer.GRAMMAR_VERBS.get('eq'), 'equip')

    def test_equip_still_combat_blocked_with_the_authored_line(self):
        for verb in ('equip', 'eq'):
            self.assertEqual(
                SkylandConsumer.COMBAT_BLOCKED[verb],
                "There's no time to fiddle with your gear mid-fight!")

    def test_help_row(self):
        action_rows = dict(SkylandConsumer.HELP_SECTIONS)['Action commands']
        self.assertIn(
            ('equip (eq)', 'equip [<item>]',
             'Equip an item from your inventory.'),
            action_rows)
