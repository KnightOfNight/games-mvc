"""v24.22 brief 1 (#225): acuity renders fixed two decimals, end to end.

The founding complaint: a character settled exactly on a two-decimal
band edge (1.15) rendered as 1.1. The settle tick itself prints the
numeral-free terminal line (#133 doctrine, unchanged by this brief),
and every other tick path stores round(..., 1) — so the edge value's
numeral surface is the stats sheet (and the status payload feeding the
stats pane). Pinned here: the engine stores the edge exactly, and the
stats render shows both decimals, trailing zeros kept on the baseline.
The tick suffixes' own two-decimal literals are pinned in
test_acuity_shifts."""

from asgiref.sync import sync_to_async

from django.test import TransactionTestCase

from apps.shyland.models import Character

from .test_acuity_shifts import SETTLES, make_shift_effect, set_acuity
from .test_command_revamp import make_character, make_stub_consumer, make_world
from .test_tick_expiry import run_effects_engine


class BandEdgeTwoDecimalTests(TransactionTestCase):

    async def test_band_edge_settle_renders_both_decimals(self):
        def setup():
            zone, room = make_world('a22')
            char = make_character('a22', room)
            set_acuity(char, current=1.0, band_high=1.15)
            make_shift_effect('a22', char, 'shift_acuity_high', 0.2)
            return char
        char = await sync_to_async(setup)()
        cmd, msgs = run_effects_engine()

        # One boundary tick: 1.0 + 0.2 overshoots the 1.15 edge — the
        # engine stores the edge EXACTLY and announces the terminal line.
        await cmd.process_effects(3)
        texts = [t for pk, t, c in msgs if pk == char.pk]
        self.assertEqual(texts, [SETTLES])

        def refetch():
            return Character.objects.select_related(
                'user', 'current_room').get(pk=char.pk)
        char = await sync_to_async(refetch)()
        self.assertEqual(char.acuity_current, 1.15)

        # The founding complaint, asserted forever: 1.15 renders as
        # 1.15 — never truncated to 1.1 — and the baseline keeps its
        # trailing zeros (1.00).
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_stats()
        lines = [line.get('v', '') for msg in sent
                 if msg.get('type') == 'output' and 'lines' in msg
                 for line in msg['lines'] if line]
        self.assertIn('  Acuity:     1.15 (baseline 1.00)', lines)
