"""v20 brief 2 (#32): outbound WebSocket message envelope.

Every message sent to the Shyland client carries two envelope fields:

- ``ts``  — epoch milliseconds, UTC, stamped server-side at message
  *creation* time via :func:`envelope_ts`. Never client-supplied.
- ``seq`` — per-connection monotonic integer, stamped at the delivery
  choke point (``SkylandConsumer.send_json``), starting at 1 per
  connection. ``seq`` order is authoritative for rendering; ``ts`` may
  occasionally run non-monotonic relative to ``seq`` (a broadcast created
  earlier can be delivered after a direct message created later) and
  that is correct behavior.

The choke point is the designated tap for the Firehose Logging
milestone (#37/#33). No persistence happens here.
"""
import time


def envelope_ts():
    """Epoch milliseconds, UTC — the creation-time ``ts`` stamp."""
    return int(time.time() * 1000)
