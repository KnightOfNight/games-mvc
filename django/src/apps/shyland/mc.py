"""v25.1 (#37): the MC sink's emit helper — the single creation-level
choke point for Monitoring and Command event records (GDD §10.11).

Standalone by design: game code imports mc, never the reverse. Every
call is fire-and-forget by construction — a sink failure (Redis down,
serialization error, anything) drops the record and never raises into
game code. No game path may ever block or break on MC.
"""

import asyncio
import json
import logging
import time

import redis as sync_redis
import redis.asyncio as aioredis
from channels.db import database_sync_to_async
from django.conf import settings

logger = logging.getLogger(__name__)

MC_STREAM_KEY = 'mc:events'

# Lazy module-level async client, built on first use from the one
# endpoint constant (#271). db 0 is shared with the channel layer and
# the presence keys — the mc:* key namespace doesn't collide with
# either. Rebound if the running event loop changes: redis.asyncio
# pools bind to the loop that created them — Daphne and the ticker
# each live on one loop for the process lifetime, but test runs
# create many.
_client = None
_client_loop = None

# Sink-failure warnings are throttled to at most one per interval so a
# dead Redis never floods the logs.
_WARN_INTERVAL = 60.0
_last_warn = None


def _get_client():
    global _client, _client_loop
    loop = asyncio.get_running_loop()
    if _client is None or _client_loop is not loop:
        _client = aioredis.Redis(host=settings.REDIS_HOST, port=6379, db=0)
        _client_loop = loop
    return _client


def _warn(msg, *args):
    global _last_warn
    now = time.monotonic()
    if _last_warn is None or now - _last_warn >= _WARN_INTERVAL:
        _last_warn = now
        logger.warning(msg, *args)


async def mc_emit(kind, *, actor_id=None, actor_name='', room_id=None,
                  audience=(), data=None):
    """Emit one MC record to the hot tier (Redis Stream ``mc:events``).

    One event, one record, emitted where the event is born — never at
    the delivery choke point. ``audience`` is the list of character pks
    the event was addressed to, resolved at fan-out time. No caller
    ever uses a return value.
    """
    try:
        record = {
            'kind': kind,
            'actor_id': '' if actor_id is None else str(actor_id),
            'actor_name': actor_name or '',
            'room_id': '' if room_id is None else str(room_id),
            'audience': json.dumps(list(audience)),
            'data': json.dumps(data or {}),
        }
        await _get_client().xadd(
            MC_STREAM_KEY, record,
            maxlen=settings.MC_STREAM_MAXLEN, approximate=True,
        )
    except Exception:
        _warn('shyland mc: emit failed — record dropped (kind=%s)', kind)


def mc_emit_sync(kind, *, actor_id=None, actor_name='', room_id=None,
                 audience=(), data=None):
    """Sync twin of mc_emit for sync creation sites (v25.4: the kill
    switch flip — shell, Django admin, and the command's ORM path).
    Identical record shape and fire-and-forget law; builds a
    short-lived sync client per call (flips are rare by definition)."""
    try:
        record = {
            'kind': kind,
            'actor_id': '' if actor_id is None else str(actor_id),
            'actor_name': actor_name or '',
            'room_id': '' if room_id is None else str(room_id),
            'audience': json.dumps(list(audience)),
            'data': json.dumps(data or {}),
        }
        client = sync_redis.Redis(host=settings.REDIS_HOST, port=6379, db=0)
        try:
            client.xadd(MC_STREAM_KEY, record,
                        maxlen=settings.MC_STREAM_MAXLEN, approximate=True)
        finally:
            client.close()
    except Exception:
        _warn('shyland mc: emit failed — record dropped (kind=%s)', kind)


@database_sync_to_async
def _pks_in_room(room_id):
    from .models import Character
    return list(Character.objects.filter(current_room_id=room_id)
                .values_list('pk', flat=True))


async def resolve_room_audience(room_id, exclude_pks=()):
    """Pks of connected characters in room ``room_id``, minus excludes.

    Connected = a live presence key (``shyland:online:{pk}``) — the
    same mechanics as the consumer's presence filtering and the
    ticker's ``_online_character_pks``. Returns a sorted list; any
    failure yields ``[]``, never an exception (fire-and-forget posture
    when called from inside the emit path).
    """
    try:
        pks = await _pks_in_room(room_id)
        exclude = set(exclude_pks or ())
        pks = [pk for pk in pks if pk not in exclude]
        if not pks:
            return []
        keys = [f'shyland:online:{pk}' for pk in pks]
        values = await _get_client().mget(*keys)
        return sorted(pk for pk, value in zip(pks, values) if value)
    except Exception:
        _warn('shyland mc: audience resolution failed — empty audience '
              '(room_id=%s)', room_id)
        return []
