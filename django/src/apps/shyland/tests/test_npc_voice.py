"""v23 B4 (#138, #40 code half, #146): voice machinery & transactions.

The get_sale_price zero floor, the reworked sell paths (worthless items
sell for 0, artifacts refused generically in both paths, the trailing
form for mixed bulk), the no-leak rule on vendor refusal speech, the
pool inventory guards (pity coverage, aggro lockstep, substitution
completeness), and the dead-flag field removal (#146)."""

import os

from asgiref.sync import sync_to_async

from django.test import SimpleTestCase, TransactionTestCase

from apps.shyland import npc_voice
from apps.shyland.combat_utils import npc_display
from apps.shyland.item_utils import get_sale_price, item_ref
from apps.shyland.models import Character, ItemInstance

from .test_command_revamp import (
    make_character, make_item_def, make_owned_item, make_stub_consumer,
    make_vendor, make_world, outputs,
)

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Built by concatenation so this file never trips the lockstep greps.
AGGRO_LITERAL = 'snarls and moves' + ' to attack'
FIELD_LITERAL = 'is_' + 'artifact'


def app_python_sources(exclude_dirs=()):
    for root, dirs, files in os.walk(APP_DIR):
        dirs[:] = [d for d in dirs if d not in exclude_dirs
                   and d != '__pycache__']
        for fname in files:
            if fname.endswith('.py'):
                yield os.path.join(root, fname)


def expected_set(pool, **fields):
    """Every pool line rendered with the call site's field values."""
    return {npc_voice.pick([line], **fields) for line in pool}


def make_artifact(defn, char):
    return ItemInstance.objects.create(
        definition=defn, owner=char, mk_tier=1, rarity='artifact',
        durability_current=100.0, is_identified=True,
    )


class ZeroFloorTests(TransactionTestCase):

    async def test_zero_floor_and_one_copper_case(self):
        def setup():
            zone, room = make_world('zfA')
            char = make_character('zfA', room)
            junk_def = make_item_def('zfA', 'Junk Scrap', base_value=0)
            one_def = make_item_def('zfA', 'Plain Cord', base_value=1)
            three_def = make_item_def('zfA', 'Sound Hide', base_value=3)
            return (make_owned_item(junk_def, char),
                    make_owned_item(one_def, char),
                    make_owned_item(three_def, char))
        junk, one, three = await sync_to_async(setup)()

        self.assertEqual(get_sale_price(junk), 0)      # worthless pays 0
        self.assertEqual(get_sale_price(one), 1)       # floor not over-corrected
        self.assertEqual(get_sale_price(three), 1)     # max(1, 3 // 3)


class SellReworkTests(TransactionTestCase):

    async def test_worthless_sell_succeeds(self):
        def setup():
            zone, room = make_world('swA')
            char = make_character('swA', room)
            defn = make_item_def('swA', 'Junk Scrap', base_value=0)
            vendor = make_vendor('swA', room, [(defn, 9)])
            item = make_owned_item(defn, char)
            return char, vendor, item, item_ref(item), char.copper
        char, vendor, item, display, copper_before = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_sell('scrap')

        texts = [(m['text'], m.get('category')) for m in outputs(sent)]
        vendor_name = npc_display(vendor, capitalize=True)
        expected = expected_set(
            npc_voice.SELL_WORTHLESS_SINGLE, vendor=vendor_name, name=display)
        self.assertIn(texts[0][0], expected)
        self.assertEqual(texts[0][1], 'success')

        def state():
            return (ItemInstance.objects.filter(pk=item.pk).exists(),
                    Character.objects.get(pk=char.pk).copper)
        exists, copper_after = await sync_to_async(state)()
        self.assertFalse(exists)
        self.assertEqual(copper_after, copper_before)

    async def test_bound_worthless_sell_succeeds(self):
        # The #138 trap: bound starter-kit junk must open.
        def setup():
            zone, room = make_world('swB')
            char = make_character('swB', room)
            defn = make_item_def('swB', 'Junk Scrap', base_value=0)
            make_vendor('swB', room, [(defn, 9)])
            return char, make_owned_item(defn, char, bound=True)
        char, item = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_sell('scrap')

        exists = await sync_to_async(
            lambda: ItemInstance.objects.filter(pk=item.pk).exists())()
        self.assertFalse(exists)

    async def test_artifact_refused_single(self):
        def setup():
            zone, room = make_world('swC')
            char = make_character('swC', room)
            defn = make_item_def('swC', 'Sound Hide', base_value=3)
            vendor = make_vendor('swC', room, [(defn, 9)])
            return char, vendor, make_artifact(defn, char)
        char, vendor, item = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_sell('hide')

        texts = [(m['text'], m.get('category')) for m in outputs(sent)]
        vendor_name = npc_display(vendor, capitalize=True)
        expected = expected_set(
            npc_voice.SELL_REFUSAL_SINGLE, vendor=vendor_name)
        self.assertIn(texts[0][0], expected)
        self.assertEqual(texts[0][1], 'warn')

        exists = await sync_to_async(
            lambda: ItemInstance.objects.filter(pk=item.pk).exists())()
        self.assertTrue(exists)

    async def test_artifact_refused_bulk_partial(self):
        def setup():
            zone, room = make_world('swD')
            char = make_character('swD', room)
            defn = make_item_def('swD', 'Sound Hide', base_value=3)
            vendor = make_vendor('swD', room, [(defn, 9)])
            paying = [make_owned_item(defn, char) for _ in range(2)]
            artifact = make_artifact(defn, char)
            return char, vendor, paying, artifact
        char, vendor, paying, artifact = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_sell('all hide')

        texts = [(m['text'], m.get('category')) for m in outputs(sent)]
        vendor_name = npc_display(vendor, capitalize=True)
        partial_expected = expected_set(
            npc_voice.SELL_REFUSAL_PARTIAL, vendor=vendor_name)
        partial_lines = [t for t, c in texts if t in partial_expected]
        self.assertEqual(len(partial_lines), 1)

        def state():
            return (ItemInstance.objects.filter(pk=artifact.pk).exists(),
                    ItemInstance.objects.filter(
                        pk__in=[i.pk for i in paying]).count())
        artifact_exists, paying_left = await sync_to_async(state)()
        self.assertTrue(artifact_exists)
        self.assertEqual(paying_left, 0)

    async def test_artifact_refused_bulk_total(self):
        def setup():
            zone, room = make_world('swE')
            char = make_character('swE', room)
            defn = make_item_def('swE', 'Sound Hide', base_value=3)
            vendor = make_vendor('swE', room, [(defn, 9)])
            return char, vendor, [make_artifact(defn, char) for _ in range(2)]
        char, vendor, artifacts = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_sell('all hide')

        texts = [(m['text'], m.get('category')) for m in outputs(sent)]
        vendor_name = npc_display(vendor, capitalize=True)
        none_expected = expected_set(
            npc_voice.SELL_REFUSAL_NONE, vendor=vendor_name)
        partial_expected = expected_set(
            npc_voice.SELL_REFUSAL_PARTIAL, vendor=vendor_name)
        self.assertEqual(len([t for t, c in texts if t in none_expected]), 1)
        self.assertEqual(len([t for t, c in texts if t in partial_expected]), 0)

        count = await sync_to_async(
            lambda: ItemInstance.objects.filter(
                pk__in=[a.pk for a in artifacts]).count())()
        self.assertEqual(count, 2)

    async def test_mixed_bulk_trailing_form(self):
        def setup():
            zone, room = make_world('swF')
            char = make_character('swF', room)
            pay_def = make_item_def('swF', 'Sound Hide', base_value=3)
            junk_def = make_item_def('swF', 'Junk Scrap', base_value=0)
            vendor = make_vendor('swF', room, [(pay_def, 9)])
            for _ in range(2):
                make_owned_item(pay_def, char)
            for _ in range(2):
                make_owned_item(junk_def, char)
            return char, vendor
        char, vendor = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        # 'sell all common' — the rarity form sweeps across definitions.
        await consumer.cmd_sell('all common')

        texts = [m['text'] for m in outputs(sent)]
        vendor_name = npc_display(vendor, capitalize=True)
        trailing_expected = expected_set(
            npc_voice.SELL_WORTHLESS_TRAILING, vendor=vendor_name)
        trailing_idx = [i for i, t in enumerate(texts)
                        if t in trailing_expected]
        self.assertEqual(len(trailing_idx), 1)
        # The payment aggregate precedes the trailing remark.
        payment_idx = [i for i, t in enumerate(texts)
                       if 'Sound Hide' in t and '×2' in t]
        self.assertEqual(len(payment_idx), 1)
        self.assertLess(payment_idx[0], trailing_idx[0])


class NoLeakInvariantTests(SimpleTestCase):

    def test_refusal_pools_never_name_a_rarity(self):
        forbidden = ('artifact', 'legendary', 'epic', 'rare',
                     'uncommon', 'common', 'mk')
        lines = (npc_voice.SELL_REFUSAL_SINGLE
                 + npc_voice.SELL_REFUSAL_PARTIAL
                 + npc_voice.SELL_REFUSAL_NONE
                 + [npc_voice.SELL_REFUSAL_FALLBACK])
        for line in lines:
            lowered = line.lower()
            for word in forbidden:
                self.assertNotIn(word, lowered,
                                 f'no-leak violation: {word!r} in {line!r}')


class PoolInventoryTests(SimpleTestCase):

    def test_pity_pool_coverage(self):
        required = {'morra', 'pella', 'ferwick', 'repairbot-prime',
                    'maro-the-mender', 'tavik-the-mender', 'old-brammel'}
        self.assertEqual(set(npc_voice.PITY_REPAIR_LINES) & required, required)
        for slug, pool in npc_voice.PITY_REPAIR_LINES.items():
            self.assertGreaterEqual(len(pool), 3, slug)

    def test_aggro_lockstep(self):
        self.assertGreater(len(npc_voice.AGGRO_ENGAGE), 1)
        offenders = []
        for path in app_python_sources():
            if os.path.basename(path) == 'npc_voice.py':
                continue
            with open(path, encoding='utf-8') as fh:
                if AGGRO_LITERAL in fh.read():
                    offenders.append(path)
        self.assertEqual(offenders, [])

    def test_substitution_completeness(self):
        # Pool -> the exact field names its call sites supply.
        table = {
            'SELL_REFUSAL_SINGLE': {'vendor'},
            'SELL_REFUSAL_PARTIAL': {'vendor'},
            'SELL_REFUSAL_NONE': {'vendor'},
            'SELL_SINGLE': {'vendor', 'name', 'amount'},
            'SELL_BULK': {'vendor', 'name', 'qty', 'amount'},
            'SELL_WORTHLESS_SINGLE': {'vendor', 'name'},
            'SELL_WORTHLESS_TRAILING': {'vendor'},
            'BUY_SINGLE': {'vendor', 'name', 'amount'},
            'BUY_BULK': {'vendor', 'name', 'qty', 'amount'},
            'SOLD_OUT': {'vendor'},
            'PITY_REPAIR_FALLBACK': {'name'},
            'REPAIR_SUCCESS_BULK': {'name', 'cost'},
            'REPAIR_SUCCESS_SINGLE': {'repairer', 'name', 'cost'},
            'REPAIR_FAIL_BULK': {'name', 'cost'},
            'REPAIR_FAIL_SINGLE': {'repairer', 'name', 'cost'},
            'REPAIR_POOR_BULK': {'name', 'cost'},
            'REPAIR_POOR_SINGLE': {'name', 'cost'},
            'KIBITZ_LINES': {'other'},
            'AGGRO_ENGAGE': {'name'},
        }
        for pool_name, fields in table.items():
            pool = getattr(npc_voice, pool_name)
            for line in pool:
                rendered = npc_voice.pick(
                    [line], **{f: 'X' for f in fields})
                self.assertNotIn('{', rendered,
                                 f'{pool_name}: unfilled placeholder in {line!r}')
        # The per-NPC pity pools take no substitution at all.
        for slug, pool in npc_voice.PITY_REPAIR_LINES.items():
            for line in pool:
                self.assertNotIn('{', line, f'{slug}: {line!r}')


class FieldRemovalTests(SimpleTestCase):

    def test_dead_flag_field_is_gone(self):
        field_names = [f.name for f in ItemInstance._meta.get_fields()]
        self.assertNotIn(FIELD_LITERAL, field_names)
        offenders = []
        for path in app_python_sources(exclude_dirs=('migrations',)):
            if os.path.abspath(path) == os.path.abspath(__file__):
                continue
            with open(path, encoding='utf-8') as fh:
                if FIELD_LITERAL in fh.read():
                    offenders.append(path)
        self.assertEqual(offenders, [])
