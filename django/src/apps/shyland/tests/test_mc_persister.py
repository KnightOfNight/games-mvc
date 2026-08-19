"""v25.1 (#37): the MC persister — entry-to-row mapping, ts derivation
from the stream id, idempotent replay, and malformed-entry survival."""

from datetime import datetime, timezone as dt_timezone
from unittest import mock

from django.test import SimpleTestCase, TransactionTestCase

from apps.shyland.management.commands.run_mc_persister import (
    Command, GROUP, entry_to_row,
)
from apps.shyland.mc import MC_STREAM_KEY
from apps.shyland.models import MCEvent


WELL_FORMED = {
    b'kind': b'out',
    b'actor_id': b'7',
    b'actor_name': b'Tess',
    b'room_id': b'3',
    b'audience': b'[7, 9]',
    b'data': b'{"type": "output", "text": "hi", "category": "say"}',
}


class EntryToRowTests(SimpleTestCase):
    def test_field_mapping_and_ts_derivation(self):
        row = entry_to_row(b'1700000000123-0', WELL_FORMED)
        self.assertEqual(row.stream_id, '1700000000123-0')
        self.assertEqual(row.ts, datetime.fromtimestamp(
            1700000000.123, tz=dt_timezone.utc))
        self.assertEqual(row.kind, 'out')
        self.assertEqual(row.actor_id, 7)
        self.assertEqual(row.actor_name, 'Tess')
        self.assertEqual(row.room_id, 3)
        self.assertEqual(row.audience, [7, 9])
        self.assertEqual(row.data, {'type': 'output', 'text': 'hi',
                                    'category': 'say'})

    def test_empty_ids_map_to_none(self):
        fields = dict(WELL_FORMED)
        fields[b'actor_id'] = b''
        fields[b'room_id'] = b''
        row = entry_to_row(b'1700000000123-1', fields)
        self.assertIsNone(row.actor_id)
        self.assertIsNone(row.room_id)

    def test_malformed_entry_stored_raw_never_raises(self):
        fields = {b'kind': b'out', b'actor_id': b'not-a-number',
                  b'audience': b'[', b'data': b'{broken'}
        with self.assertLogs('shyland.mc', level='WARNING') as logs:
            row = entry_to_row(b'1700000000123-2', fields)
        self.assertEqual(len(logs.output), 1)
        self.assertEqual(row.kind, 'malformed')
        self.assertEqual(row.stream_id, '1700000000123-2')
        self.assertEqual(row.data['raw']['kind'], 'out')


class FakeAckClient:
    def __init__(self):
        self.acked = []

    def xack(self, key, group, *ids):
        self.acked.append((key, group, list(ids)))


class PersistTests(TransactionTestCase):
    def _command(self):
        command = Command()
        command._stopping = False
        return command

    def test_batch_writes_rows_then_acks(self):
        client = FakeAckClient()
        entries = [(b'1700000000123-0', WELL_FORMED),
                   (b'1700000000124-0', WELL_FORMED)]
        count = self._command()._persist(client, entries)
        self.assertEqual(count, 2)
        self.assertEqual(MCEvent.objects.count(), 2)
        self.assertEqual(client.acked, [(MC_STREAM_KEY, GROUP,
                                         ['1700000000123-0',
                                          '1700000000124-0'])])

    def test_duplicate_stream_id_replay_is_a_noop(self):
        client = FakeAckClient()
        entries = [(b'1700000000123-0', WELL_FORMED)]
        command = self._command()
        command._persist(client, entries)
        command._persist(client, entries)
        self.assertEqual(MCEvent.objects.count(), 1)
        # Replay still acks — the entry is done either way.
        self.assertEqual(len(client.acked), 2)

    def test_malformed_entry_is_stored_raw_acked_and_survived(self):
        client = FakeAckClient()
        entries = [(b'1700000000123-0', WELL_FORMED),
                   (b'1700000000125-0', {b'kind': b'out',
                                         b'actor_id': b'xx',
                                         b'data': b'{broken'})]
        count = self._command()._persist(client, entries)
        self.assertEqual(count, 2)
        self.assertEqual(MCEvent.objects.count(), 2)
        malformed = MCEvent.objects.get(stream_id='1700000000125-0')
        self.assertEqual(malformed.kind, 'malformed')
        self.assertEqual(malformed.data['raw']['data'], '{broken')
        self.assertEqual(client.acked[0][2],
                         ['1700000000123-0', '1700000000125-0'])

    def test_db_failure_backs_off_and_retries_without_acking(self):
        client = FakeAckClient()
        entries = [(b'1700000000123-0', WELL_FORMED)]
        command = self._command()
        real_bulk_create = MCEvent.objects.bulk_create
        attempts = []

        def flaky_bulk_create(rows, **kwargs):
            attempts.append(1)
            if len(attempts) == 1:
                raise RuntimeError('db down')
            return real_bulk_create(rows, **kwargs)

        with mock.patch.object(MCEvent.objects, 'bulk_create',
                               side_effect=flaky_bulk_create), \
                mock.patch('apps.shyland.management.commands.'
                           'run_mc_persister.time.sleep'):
            count = command._persist(client, entries)
        self.assertEqual(count, 1)
        self.assertEqual(len(attempts), 2)
        self.assertEqual(MCEvent.objects.count(), 1)
        self.assertEqual(len(client.acked), 1)
