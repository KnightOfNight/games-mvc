"""v26.3 Brief 1 (#297/#338): curses in the world.

Coverage per the brief's §12: the #338 regen pause (an active
dot_vitality pauses passive vitality regen — bar-scoped, source-blind,
inactive components and holds don't trigger it), the live wild chance
(1/3, gate and template semantics pinned), the cleanse command (happy
path through end_curse('cleansed'), the refusal family including the
byte-identical no-leak pool miss), the inspect sweep (charge arithmetic,
presence-only itemization, sets nothing, the refusal family), the
examine Cleansing price line, the registry (help rows, completion
scoping), and the seeded cleansers and prices.
"""

import io
import math
from unittest import mock

from asgiref.sync import sync_to_async

from django.core.management import call_command
from django.test import TestCase, TransactionTestCase

from apps.shyland import npc_voice
from apps.shyland.consumers import SkylandConsumer
from apps.shyland.currency import display_for_zone
from apps.shyland.curse_utils import spring_curse
from apps.shyland.effect_utils import apply_effect_definition
from apps.shyland.item_utils import (
    CURSE_INSPECT_PRICE_PER_ITEM, CURSE_WILD_CHANCE, compose_item_line,
    generate_item_instance,
)
from apps.shyland.models import (
    Character, CombatSession, CurseCandidate, EffectComponentInstance,
    EffectDefinition, EffectInstance, ItemDefinition, ItemInstance,
    NpcDefinition, NpcInstance, VITALITY_REGEN_SECS, LONGEVITY_REGEN_SECS,
)

from .test_command_revamp import (
    make_character, make_stub_consumer, make_world, outputs,
)
from .test_b2_amendment1 import line_texts
from .test_v243_regen import run_regen_engine
from .test_v26_2_brief1 import make_effect, make_latent_item, set_bars


def make_cleanser(prefix, room, slug=None):
    """A living cleanser NPC in the room (non-attackable fixture shape)."""
    definition = NpcDefinition.objects.create(
        name=f'{prefix} Cleanser', slug=slug or f'{prefix}-cleanser',
        description='A test cleanser.', genre_tag='fantasy',
        is_cleanser=True, attackable=False,
        base_vitality=10, base_str=1, base_dex=1, base_end=1,
        base_int=1, base_wis=1, base_per=1,
    )
    return NpcInstance.objects.create(
        definition=definition, current_room=room, spawn_room=room,
        vitality_current=10, vitality_max=10,
    )


def make_sprung_equipped(prefix, char, cleanse_price=60, mk_tier=1):
    """An equipped item with a live (sprung) stat-cut curse."""
    curse = make_effect(
        f'{prefix}-crs',
        [{'ctype': 'stat_cut_percent', 'magnitude': 0.25,
          'target_stat': 'str', 'no_expiry': True}],
        is_curse=True, memorial_text='A test scar remains.')
    curse.cleanse_price = cleanse_price
    curse.save(update_fields=['cleanse_price'])
    item = make_latent_item(prefix, char, curse)
    item.mk_tier = mk_tier
    item.is_equipped = True
    item.equipped_slot = 'MAIN_HAND'
    item.save(update_fields=['mk_tier', 'is_equipped', 'equipped_slot'])
    spring_curse(item, char)
    item.refresh_from_db()
    char.refresh_from_db()
    return item, curse


def get_char(char):
    return Character.objects.get(pk=char.pk)


def reload_char(char):
    """Re-fetch with the FK caches the stub consumer touches in async
    context (refresh_from_db drops the cached user relation)."""
    return Character.objects.select_related(
        'user', 'current_room__zone', 'current_room__area',
        'origin', 'archetype').get(pk=char.pk)


# ----------------------------------------------------------------------
# §12.1 — the #338 regen pause
# ----------------------------------------------------------------------

class RegenPauseTests(TransactionTestCase):
    """Phase 4 on a non-round-boundary tick (4 % 3 != 0 — Phase 1 must
    not fire; 4 is the 274-bar longevity interval, so its arm fires)."""

    TICK = 4

    def _setup(self, prefix):
        zone, room = make_world(prefix)
        char = make_character(prefix, room)
        set_bars(char, vitality_max=718, vitality_current=100,
                 longevity_max=274, longevity_current=100)
        # The staging invariant: tick 4 is off the round boundary and on
        # the longevity interval.
        assert self.TICK % 3 != 0
        assert self.TICK % math.ceil(LONGEVITY_REGEN_SECS / 274) == 0
        return char

    async def test_active_dot_pauses_vitality_longevity_still_regens(self):
        def setup():
            char = self._setup('rpA')
            apply_effect_definition(
                make_effect('rpA-dot',
                            [{'ctype': 'dot_vitality', 'magnitude': 3.0}]),
                char, 1)
            return char
        char = await sync_to_async(setup)()

        cmd, sent = run_regen_engine()
        await cmd.process_effects(self.TICK)

        c = await sync_to_async(get_char)(char)
        self.assertEqual(c.vitality_current, 100)     # paused
        self.assertEqual(c.longevity_current, 101)    # bar-scoped: unaffected

    async def test_inactive_dot_component_does_not_pause(self):
        def setup():
            char = self._setup('rpB')
            apply_effect_definition(
                make_effect('rpB-dot',
                            [{'ctype': 'dot_vitality', 'magnitude': 3.0}]),
                char, 1)
            EffectComponentInstance.objects.filter(
                effect_instance__target=char,
                component__component_type='dot_vitality',
            ).update(is_active=False)
            return char
        char = await sync_to_async(setup)()

        cmd, sent = run_regen_engine()
        await cmd.process_effects(self.TICK)

        c = await sync_to_async(get_char)(char)
        self.assertEqual(c.vitality_current,
                         100 + math.ceil(718 / VITALITY_REGEN_SECS))

    async def test_hot_does_not_pause(self):
        def setup():
            char = self._setup('rpC')
            apply_effect_definition(
                make_effect('rpC-hot',
                            [{'ctype': 'hot_vitality', 'magnitude': 3.0}]),
                char, 1)
            return char
        char = await sync_to_async(setup)()

        cmd, sent = run_regen_engine()
        await cmd.process_effects(self.TICK)

        c = await sync_to_async(get_char)(char)
        self.assertEqual(c.vitality_current,
                         100 + math.ceil(718 / VITALITY_REGEN_SECS))

    async def test_floor_hold_does_not_pause_hold_caps_instead(self):
        def setup():
            char = self._setup('rpD')
            # Hold at ceil(0.5 × 718) = 359 — above current, so regen
            # works, capped by the hold (not the pause).
            apply_effect_definition(
                make_effect('rpD-hold',
                            [{'ctype': 'floor_hold_vitality',
                              'magnitude': 0.0, 'mag2': 0.5,
                              'no_expiry': True}]),
                char, 1)
            return char
        char = await sync_to_async(setup)()

        cmd, sent = run_regen_engine()
        await cmd.process_effects(self.TICK)

        c = await sync_to_async(get_char)(char)
        self.assertEqual(c.vitality_current,
                         100 + math.ceil(718 / VITALITY_REGEN_SECS))

    async def test_dot_longevity_does_not_pause_vitality(self):
        def setup():
            char = self._setup('rpE')
            apply_effect_definition(
                make_effect('rpE-dlon',
                            [{'ctype': 'dot_longevity', 'magnitude': 3.0}]),
                char, 1)
            return char
        char = await sync_to_async(setup)()

        cmd, sent = run_regen_engine()
        await cmd.process_effects(self.TICK)

        c = await sync_to_async(get_char)(char)
        # Bar-scoped: a longevity drain never pauses the vitality arm.
        self.assertEqual(c.vitality_current,
                         100 + math.ceil(718 / VITALITY_REGEN_SECS))


# ----------------------------------------------------------------------
# §12.2 — the wild chance, live and pinned
# ----------------------------------------------------------------------

class WildChanceTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.curse = EffectDefinition.objects.create(
            name='WC Curse', slug='wc-curse', is_curse=True)
        cls.pool_def = ItemDefinition.objects.create(
            name='WC Mace', slug='wc-mace', item_type='weapon',
            genre_tag='fantasy', valid_slots=['MAIN_HAND'],
            scaling_base=1.0, scaling_factor=1.0,
            takes_durability_loss=False, durability_table=[],
            is_cursed_template=True,
        )
        CurseCandidate.objects.create(
            item_definition=cls.pool_def, curse=cls.curse, weight=1)
        cls.plain_def = ItemDefinition.objects.create(
            name='WC Club', slug='wc-club', item_type='weapon',
            genre_tag='fantasy', valid_slots=['MAIN_HAND'],
            scaling_base=1.0, scaling_factor=1.0,
            takes_durability_loss=False, durability_table=[],
        )

    def test_constant_is_one_third(self):
        self.assertEqual(CURSE_WILD_CHANCE, 1 / 3)

    def test_roll_under_the_chance_curses_a_rare(self):
        with mock.patch('apps.shyland.item_utils.random.random',
                        return_value=0.2):
            item = generate_item_instance(self.pool_def, 1, 'rare')
        self.assertEqual(item.latent_curse, self.curse)
        self.assertTrue(item.is_cursed)

    def test_roll_over_the_chance_does_not(self):
        with mock.patch('apps.shyland.item_utils.random.random',
                        return_value=0.5):
            item = generate_item_instance(self.pool_def, 1, 'rare')
        self.assertIsNone(item.latent_curse)
        self.assertFalse(item.is_cursed)

    def test_common_never_rolls(self):
        with mock.patch('apps.shyland.item_utils.random.random',
                        return_value=0.0):
            item = generate_item_instance(self.pool_def, 1, 'common')
        self.assertIsNone(item.latent_curse)

    def test_non_template_never_rolls(self):
        with mock.patch('apps.shyland.item_utils.random.random',
                        return_value=0.0):
            item = generate_item_instance(self.plain_def, 1, 'rare')
        self.assertIsNone(item.latent_curse)


# ----------------------------------------------------------------------
# §12.3 / §12.4 — cleanse
# ----------------------------------------------------------------------

class CleanseCommandTests(TransactionTestCase):

    async def test_happy_path(self):
        def setup():
            zone, room = make_world('clA')
            char = make_character('clA', room)
            # The per-slug voice path: the test cleanser is Mother Tansy.
            cleanser = make_cleanser('clA', room, slug='mother-tansy')
            item, curse = make_sprung_equipped('clA', char, cleanse_price=60)
            str_cut = char.stat_str
            Character.objects.filter(pk=char.pk).update(copper=1000)
            char.refresh_from_db()
            return zone, reload_char(char), item, str_cut
        zone, char, item, str_before_cleanse = await sync_to_async(setup)()
        self.assertEqual(str_before_cleanse, 8)   # 10 cut by 25%

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_cleanse('mace')

        def check():
            c = get_char(char)
            i = ItemInstance.objects.get(pk=item.pk)
            instance = EffectInstance.objects.get(target=c)
            components = list(instance.component_instances.all())
            return c, i, instance, components
        c, i, instance, components = await sync_to_async(check)()

        self.assertEqual(c.copper, 1000 - 60)     # price × Mk 1
        self.assertEqual(c.stat_str, 10)          # stat restored
        self.assertFalse(i.is_cursed)
        self.assertIsNone(i.active_curse_id)
        self.assertIsNone(i.latent_curse_id)
        self.assertEqual(i.memorial_description, 'A test scar remains.')
        self.assertTrue(i.is_equipped)            # stays equipped
        self.assertFalse(instance.is_active)
        self.assertEqual(instance.removed_by, 'cleansed')
        for ci in components:
            self.assertEqual(ci.removed_by, 'cleansed')

        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['category'], 'success')
        # The line came from Mother Tansy's own pool.
        price = display_for_zone(60, zone.slug)
        pool = [line.replace('{item}', 'clA Mace Mk 1')
                    .replace('{price}', price)
                for line in npc_voice.CLEANSE_SUCCESS_LINES['mother-tansy']]
        self.assertIn(msgs[0]['text'], pool)
        # The pane resyncs after the reversal.
        self.assertTrue(any(m.get('type') == 'status' for m in sent))

    async def test_no_cleanser_fixed_line(self):
        def setup():
            zone, room = make_world('clB')
            char = make_character('clB', room)
            make_sprung_equipped('clB', char)
            return reload_char(char)
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_cleanse('mace')
        msgs = outputs(sent)
        self.assertEqual(msgs[0]['text'], 'There is no one here who can cleanse.')
        self.assertEqual(msgs[0]['category'], 'warn')

    async def test_poor_refusal_names_price_charges_nothing(self):
        def setup():
            zone, room = make_world('clC')
            char = make_character('clC', room)
            make_cleanser('clC', room)
            item, curse = make_sprung_equipped('clC', char, cleanse_price=75)
            Character.objects.filter(pk=char.pk).update(copper=10)
            char.refresh_from_db()
            return zone, reload_char(char), item
        zone, char, item = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_cleanse('mace')

        def check():
            return (get_char(char).copper,
                    ItemInstance.objects.get(pk=item.pk).is_cursed)
        copper, still_cursed = await sync_to_async(check)()
        self.assertEqual(copper, 10)              # nothing charged
        self.assertTrue(still_cursed)             # curse intact
        msgs = outputs(sent)
        self.assertEqual(msgs[0]['category'], 'warn')
        self.assertIn(display_for_zone(75, zone.slug), msgs[0]['text'])

    async def test_equipped_uncursed_gets_nothing_line_free(self):
        def setup():
            zone, room = make_world('clD')
            char = make_character('clD', room)
            make_cleanser('clD', room)
            curse = make_effect('clD-crs', [], is_curse=True)
            item = make_latent_item('clD', char, curse)
            # Equipped and clean: no latent, no active.
            item.is_cursed = False
            item.latent_curse = None
            item.is_equipped = True
            item.equipped_slot = 'MAIN_HAND'
            item.save()
            Character.objects.filter(pk=char.pk).update(copper=500)
            char.refresh_from_db()
            return reload_char(char)
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_cleanse('mace')
        copper = await sync_to_async(lambda: get_char(char).copper)()
        self.assertEqual(copper, 500)
        msgs = outputs(sent)
        self.assertEqual(msgs[0]['category'], 'warn')

    async def test_pool_miss_is_byte_identical_for_latent_and_clean(self):
        """The no-leak rule (4a): an unequipped latent-cursed item and an
        unequipped clean item answer the identical not_found refusal."""
        def setup():
            zone, room = make_world('clE')
            char = make_character('clE', room)
            make_cleanser('clE', room)
            curse = make_effect(
                'clE-crs', [{'ctype': 'stat_cut_percent', 'magnitude': 0.25,
                             'target_stat': 'str', 'no_expiry': True}],
                is_curse=True)
            make_latent_item('clE', char, curse)          # latent, unequipped
            clean_def = ItemDefinition.objects.create(
                name='clE Club', slug='cle-club', item_type='weapon',
                genre_tag='fantasy', valid_slots=['MAIN_HAND'],
                scaling_base=0.0, scaling_factor=0.0,
                takes_durability_loss=False, durability_table=[],
            )
            ItemInstance.objects.create(
                definition=clean_def, owner=char, mk_tier=1, rarity='common',
                durability_current=100.0, is_identified=True)
            return reload_char(char)
        char = await sync_to_async(setup)()

        sent1 = []
        consumer1 = make_stub_consumer(char, sent1)
        await consumer1.cmd_cleanse('mace')       # the latent-cursed one
        sent2 = []
        consumer2 = make_stub_consumer(char, sent2)
        await consumer2.cmd_cleanse('club')       # the clean one

        m1, m2 = outputs(sent1)[0], outputs(sent2)[0]
        self.assertEqual(m1['text'], "You don't have that equipped.")
        self.assertEqual(m1['text'], m2['text'])
        self.assertEqual(m1['category'], m2['category'])

    async def test_combat_refuses_with_the_authored_line(self):
        def setup():
            zone, room = make_world('clF')
            char = make_character('clF', room)
            make_cleanser('clF', room)
            session = CombatSession.objects.create(room=room, is_active=True)
            session.characters.add(char)
            return reload_char(char)
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer._dispatch('cleanse', 'mace')
        msgs = outputs(sent)
        self.assertEqual(
            msgs[0]['text'],
            "There's no lifting a curse in the middle of a fight!")
        self.assertEqual(msgs[0]['category'], 'warn')

    async def test_dying_refuses(self):
        def setup():
            zone, room = make_world('clG')
            char = make_character('clG', room)
            make_cleanser('clG', room)
            return reload_char(char)
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        consumer._character_is_dying = True
        await consumer.receive_json({'text': 'cleanse mace'})
        msgs = outputs(sent)
        self.assertEqual(msgs[0]['category'], 'echo')
        self.assertEqual(msgs[1]['category'], 'warn')
        self.assertIn('dying', msgs[1]['text'])


# ----------------------------------------------------------------------
# §12.5 — inspect
# ----------------------------------------------------------------------

class InspectCommandTests(TransactionTestCase):

    async def test_sweep_charges_finds_and_sets_nothing(self):
        def setup():
            zone, room = make_world('inA')
            char = make_character('inA', room)
            make_cleanser('inA', room)
            # A mix: one sprung equipped, one latent in inventory
            # (curse_identified False), one clean equipped, one clean
            # carried — four instances.
            sprung, _ = make_sprung_equipped('inA', char)
            latent_curse = make_effect(
                'inA-crs2', [{'ctype': 'stat_cut_percent', 'magnitude': 0.25,
                              'target_stat': 'str', 'no_expiry': True}],
                is_curse=True)
            latent = make_latent_item('inA2', char, latent_curse)
            clean_def = ItemDefinition.objects.create(
                name='inA Helm', slug='ina-helm', item_type='armor',
                genre_tag='fantasy', valid_slots=['HEAD'],
                scaling_base=0.0, scaling_factor=0.0,
                takes_durability_loss=False, durability_table=[],
            )
            ItemInstance.objects.create(
                definition=clean_def, owner=char, mk_tier=1, rarity='common',
                durability_current=100.0, is_identified=True,
                is_equipped=True, equipped_slot='HEAD')
            ItemInstance.objects.create(
                definition=clean_def, owner=char, mk_tier=1, rarity='common',
                durability_current=100.0, is_identified=True)
            Character.objects.filter(pk=char.pk).update(copper=1000)
            char.refresh_from_db()
            return zone, reload_char(char), latent
        zone, char, latent = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        items = await consumer.get_carried_items(char)
        self.assertEqual(len(items), 4)           # equipped included
        expected_lines = await sync_to_async(
            lambda: ['  ' + compose_item_line(i) for i in items
                     if i.is_cursed])()
        self.assertEqual(len(expected_lines), 2)  # latent AND sprung alike

        await consumer.cmd_inspect()

        def check():
            return (get_char(char).copper,
                    ItemInstance.objects.get(pk=latent.pk).curse_identified)
        copper, identified = await sync_to_async(check)()
        self.assertEqual(copper, 1000 - CURSE_INSPECT_PRICE_PER_ITEM * 4)
        self.assertFalse(identified)              # the sweep sets nothing

        msgs = outputs(sent)
        self.assertEqual(msgs[0]['category'], 'warn')
        self.assertIn(str(2), msgs[0]['text'])    # the found count
        self.assertEqual([m['text'] for m in msgs[1:]], expected_lines)
        self.assertTrue(all(m['category'] == 'warn' for m in msgs[1:]))

    async def test_clean_pack_gets_the_all_clear(self):
        def setup():
            zone, room = make_world('inB')
            char = make_character('inB', room)
            make_cleanser('inB', room)
            clean_def = ItemDefinition.objects.create(
                name='inB Helm', slug='inb-helm', item_type='armor',
                genre_tag='fantasy', valid_slots=['HEAD'],
                scaling_base=0.0, scaling_factor=0.0,
                takes_durability_loss=False, durability_table=[],
            )
            ItemInstance.objects.create(
                definition=clean_def, owner=char, mk_tier=1, rarity='common',
                durability_current=100.0, is_identified=True)
            Character.objects.filter(pk=char.pk).update(copper=100)
            char.refresh_from_db()
            return reload_char(char)
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_inspect()
        copper = await sync_to_async(lambda: get_char(char).copper)()
        self.assertEqual(copper, 100 - CURSE_INSPECT_PRICE_PER_ITEM)
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['category'], 'success')

    async def test_poor_charges_nothing(self):
        def setup():
            zone, room = make_world('inC')
            char = make_character('inC', room)
            make_cleanser('inC', room)
            make_sprung_equipped('inC', char)
            Character.objects.filter(pk=char.pk).update(copper=2)
            char.refresh_from_db()
            return reload_char(char)
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_inspect()
        copper = await sync_to_async(lambda: get_char(char).copper)()
        self.assertEqual(copper, 2)
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['category'], 'warn')

    async def test_empty_pack_nothing_charged(self):
        def setup():
            zone, room = make_world('inD')
            char = make_character('inD', room)
            make_cleanser('inD', room)
            Character.objects.filter(pk=char.pk).update(copper=100)
            char.refresh_from_db()
            return reload_char(char)
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_inspect()
        copper = await sync_to_async(lambda: get_char(char).copper)()
        self.assertEqual(copper, 100)
        msgs = outputs(sent)
        self.assertEqual(msgs[0]['text'], 'You carry nothing to inspect.')

    async def test_no_cleanser_fixed_line(self):
        def setup():
            zone, room = make_world('inE')
            char = make_character('inE', room)
            return reload_char(char)
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_inspect()
        msgs = outputs(sent)
        self.assertEqual(msgs[0]['text'], 'There is no one here who can cleanse.')

    async def test_combat_refuses(self):
        def setup():
            zone, room = make_world('inF')
            char = make_character('inF', room)
            make_cleanser('inF', room)
            session = CombatSession.objects.create(room=room, is_active=True)
            session.characters.add(char)
            return reload_char(char)
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer._dispatch('inspect', '')
        msgs = outputs(sent)
        self.assertEqual(
            msgs[0]['text'],
            "There's no time for that in the middle of a fight!")
        self.assertEqual(msgs[0]['category'], 'warn')


# ----------------------------------------------------------------------
# §12.6 — the examine price line
# ----------------------------------------------------------------------

class ExamineCleansePriceTests(TransactionTestCase):

    async def test_identified_curse_shows_tier_scaled_price(self):
        def setup():
            zone, room = make_world('exA')
            char = make_character('exA', room)
            item, curse = make_sprung_equipped(
                'exA', char, cleanse_price=60, mk_tier=3)
            return zone, reload_char(char), item
        zone, char, item = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        def build():
            fresh = ItemInstance.objects.select_related(
                'active_curse__definition', 'definition').get(pk=item.pk)
            # The unwrapped DB helper (the spring_curse_if_latent pattern).
            info = SkylandConsumer.__dict__['get_curse_examine_info'].func(
                consumer, fresh, get_char(char))
            return fresh, info
        fresh, info = await sync_to_async(build)()

        self.assertEqual(len(info), 4)
        expected = display_for_zone(60 * 3, zone.slug)
        self.assertEqual(info[3], expected)
        lines = consumer._format_identified_item_lines(fresh, curse_info=info)
        self.assertIn(f'  Cleansing:  {expected}', lines)

    async def test_unidentified_curse_has_no_price_line(self):
        def setup():
            zone, room = make_world('exB')
            char = make_character('exB', room)
            curse = make_effect('exB-crs', [], is_curse=True)
            item = make_latent_item('exB', char, curse)
            return reload_char(char), item
        char, item = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        def build():
            fresh = ItemInstance.objects.select_related(
                'definition').get(pk=item.pk)
            unidentified = consumer._format_identified_item_lines(fresh)
            # Identified but with no pre-fetched info: the generic row
            # stands, still priceless.
            fresh.curse_identified = True
            generic = consumer._format_identified_item_lines(fresh)
            return unidentified, generic
        unidentified, generic = await sync_to_async(build)()
        # Unidentified: the curse is hidden entirely — no row, no price.
        self.assertFalse(any('Curse' in ln for ln in unidentified))
        self.assertFalse(any('Cleansing' in ln for ln in unidentified))
        # The generic veiled row is unchanged and carries no price.
        self.assertIn('  Curse:      This item carries a curse.', generic)
        self.assertFalse(any('Cleansing' in ln for ln in generic))


# ----------------------------------------------------------------------
# §12.7 — the registry
# ----------------------------------------------------------------------

class RegistryTests(TransactionTestCase):

    async def test_help_renders_both_rows_for_non_admin(self):
        def setup():
            zone, room = make_world('rgA')
            return make_character('rgA', room)
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_help()
        lines, texts = line_texts(sent)
        joined = '\n'.join(texts)
        self.assertIn('cleanse <item>', joined)
        self.assertIn('Pay a cleanser to sweep everything you carry', joined)

    async def test_cleanse_completion_is_exactly_the_equipped_pool(self):
        def setup():
            zone, room = make_world('rgB')
            char = make_character('rgB', room)
            item, _ = make_sprung_equipped('rgB', char)
            # A carried, unequipped item must not complete.
            clean_def = ItemDefinition.objects.create(
                name='rgB Helm', slug='rgb-helm', item_type='armor',
                genre_tag='fantasy', valid_slots=['HEAD'],
                scaling_base=0.0, scaling_factor=0.0,
                takes_durability_loss=False, durability_table=[],
            )
            ItemInstance.objects.create(
                definition=clean_def, owner=char, mk_tier=1, rarity='common',
                durability_current=100.0, is_identified=True)
            return reload_char(char), item
        char, item = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        pool = await consumer._completion_candidates('cleanse')
        self.assertEqual([i.pk for i in pool], [item.pk])

    def test_inspect_is_a_bare_verb(self):
        self.assertIn('inspect', SkylandConsumer.COMMAND_TABLE)
        self.assertFalse(SkylandConsumer.COMMAND_TABLE['inspect'][1])
        self.assertNotIn('inspect', SkylandConsumer.PROMPT_VERBS)
        self.assertNotIn('inspect', SkylandConsumer.GRAMMAR_VERBS)
        self.assertIn('cleanse', SkylandConsumer.GRAMMAR_VERBS)
        self.assertIn('cleanse', SkylandConsumer.PROMPT_VERBS)


# ----------------------------------------------------------------------
# §12.8 — the seed
# ----------------------------------------------------------------------

class SeededCleanserTests(TestCase):

    EXPECTED_PRICES = {
        'curse-leaden-arm': 75,
        'curse-craven-edge': 60,
        'curse-copper-tithe': 90,
        'curse-moth-eaten-ward': 75,
        'curse-whisper-string': 120,
        'curse-hollowing': 5000,
        'curse-gravekeepers-hold': 8000,
        'curse-threefold-ruin': 15000,
    }

    @classmethod
    def setUpTestData(cls):
        call_command('seed_world', stdout=io.StringIO())

    def test_exactly_the_four_cleansers(self):
        slugs = set(NpcDefinition.objects.filter(
            is_cleanser=True).values_list('slug', flat=True))
        self.assertEqual(slugs, {'mother-tansy', 'maro-the-mender',
                                 'tavik-the-mender', 'old-brammel'})

    def test_the_eight_cleanse_prices(self):
        priced = dict(EffectDefinition.objects.filter(
            is_curse=True).values_list('slug', 'cleanse_price'))
        self.assertEqual(priced, self.EXPECTED_PRICES)

    def test_no_non_curse_carries_a_price(self):
        self.assertFalse(EffectDefinition.objects.filter(
            is_curse=False).exclude(cleanse_price=0).exists())

    def test_curse_candidate_pool_unchanged(self):
        self.assertEqual(CurseCandidate.objects.count(), 26)
