"""v25.1 (#37): the MC persister — drains the hot tier (Redis Stream
``mc:events``) into the durable record (``MCEvent``), GDD §10.11.

A sync loop with a sync Redis client: a management command doing ORM
writes needs no async. Consumer-group semantics make the drain
crash-safe — an entry is acked only after its row write commits, and
pending entries from a dead run are reclaimed by XAUTOCLAIM. The unique
``stream_id`` makes replay idempotent (``ignore_conflicts``)."""

import json
import logging
import signal
import time
from datetime import datetime, timezone as dt_timezone

import redis
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.shyland.mc import MC_STREAM_KEY
from apps.shyland.models import MCEvent

logger = logging.getLogger('shyland.mc')

GROUP = 'persister'
CONSUMER = 'worker-1'
BATCH_COUNT = 500
BLOCK_MS = 5000
# Pending entries idle longer than this are reclaimed (crash recovery).
AUTOCLAIM_IDLE_MS = 60000
DB_RETRY_SECONDS = 5


def _decode(value):
    return value.decode() if isinstance(value, bytes) else value


def entry_to_row(stream_id, fields):
    """Map one stream entry to an unsaved MCEvent row. ``ts`` derives
    from the stream id's millisecond prefix (timezone-aware UTC). A
    malformed entry never raises out of the loop — the caller wraps
    this; whatever parses is stored (raw fields into ``data``)."""
    stream_id = _decode(stream_id)
    fields = {_decode(k): _decode(v) for k, v in fields.items()}
    ms = int(stream_id.split('-', 1)[0])
    ts = datetime.fromtimestamp(ms / 1000.0, tz=dt_timezone.utc)
    try:
        actor_id = fields.get('actor_id') or None
        room_id = fields.get('room_id') or None
        return MCEvent(
            stream_id=stream_id,
            ts=ts,
            kind=fields.get('kind', ''),
            actor_id=int(actor_id) if actor_id is not None else None,
            actor_name=fields.get('actor_name', ''),
            room_id=int(room_id) if room_id is not None else None,
            audience=json.loads(fields.get('audience') or '[]'),
            data=json.loads(fields.get('data') or '{}'),
        )
    except (ValueError, TypeError) as exc:
        logger.warning('mc persister: malformed entry %s stored raw (%s)',
                       stream_id, exc)
        return MCEvent(stream_id=stream_id, ts=ts, kind='malformed',
                       audience=[], data={'raw': fields})


class Command(BaseCommand):
    help = 'Drain the MC event stream into the durable MCEvent table (#37).'

    def handle(self, *args, **options):
        self.stdout.write('MC persister starting.')
        self._stopping = False
        signal.signal(signal.SIGTERM, self._handle_sigterm)

        client = redis.Redis(host=settings.REDIS_HOST, port=6379, db=0)
        try:
            client.xgroup_create(MC_STREAM_KEY, GROUP, id='0', mkstream=True)
        except redis.ResponseError as exc:
            if 'BUSYGROUP' not in str(exc):
                raise

        drained = 0
        last_reported = 0
        autoclaim_cursor = '0-0'
        while not self._stopping:
            # Crash recovery first: reclaim entries a dead run read but
            # never acked, then serve fresh entries.
            try:
                autoclaim_cursor, claimed, _deleted = client.xautoclaim(
                    MC_STREAM_KEY, GROUP, CONSUMER,
                    min_idle_time=AUTOCLAIM_IDLE_MS,
                    start_id=autoclaim_cursor, count=BATCH_COUNT)
                if claimed:
                    drained += self._persist(client, claimed)
                response = client.xreadgroup(
                    GROUP, CONSUMER, {MC_STREAM_KEY: '>'},
                    count=BATCH_COUNT, block=BLOCK_MS)
            except redis.RedisError as exc:
                logger.warning('mc persister: redis unavailable (%s); '
                               'retrying', exc)
                time.sleep(DB_RETRY_SECONDS)
                continue
            for _stream, entries in response or []:
                drained += self._persist(client, entries)
            if drained - last_reported >= BATCH_COUNT or (
                    drained != last_reported and not response):
                self.stdout.write(f'MC persister: {drained} entries drained.')
                last_reported = drained

        self.stdout.write(f'MC persister stopping ({drained} entries '
                          'drained this run).')

    def _handle_sigterm(self, signum, frame):
        # Graceful: the loop finishes its in-flight batch and exits 0.
        self._stopping = True

    def _persist(self, client, entries):
        """Write one batch, ack only after a successful write. On DB
        failure, back off and retry the same batch without acking."""
        rows = [entry_to_row(stream_id, fields)
                for stream_id, fields in entries]
        while True:
            try:
                MCEvent.objects.bulk_create(rows, ignore_conflicts=True)
                break
            except Exception as exc:
                logger.warning('mc persister: DB write failed (%s); '
                               'retrying in %ss without acking',
                               exc, DB_RETRY_SECONDS)
                if self._stopping:
                    # Shutdown requested while the DB is down: leave the
                    # batch pending for the next run's XAUTOCLAIM.
                    return 0
                time.sleep(DB_RETRY_SECONDS)
        client.xack(MC_STREAM_KEY, GROUP,
                    *[_decode(stream_id) for stream_id, _fields in entries])
        return len(entries)
