# Shyland V20 Brief 2 — Output Message Envelope (Timestamps + Guaranteed Ordering)

Implements GitHub issue **#32**. Self-contained; do not consult chat history. Apply after V20 Brief 1 (Map System). **Never remove or prune any transient document from the repo** — the operator does all pruning.

Design intent, binding: this envelope is deliberately the future tap point for the Firehose Logging milestone (#37/#33). Build the choke point cleanly enough that a log sink can later attach to it without restructuring. **No persistence, no sink, no retention policy in this brief** — those belong to the firehose.

---

## 1. The envelope

Every outbound WebSocket message to the Shyland client — all types: `output`, `map`, state sync, presence, everything — gains two fields:

- `ts` — **epoch milliseconds, UTC, server-generated**, stamped **where the message is created** (at construction time: in the consumer for direct sends, in the tick engine / broadcasting code for `group_send` payloads). Never trusted from, or supplied by, the client.
- `seq` — **per-connection monotonic integer**, stamped at the **single delivery choke point** (see §2), starting at 1 on each new connection and strictly increasing for the life of that connection. Resets on reconnect.

Ordering semantics, binding: **`seq` order is authoritative for rendering.** `ts` may occasionally be non-monotonic relative to `seq` (a broadcast created earlier can be delivered after a direct message created later) — this is correct behavior, not a defect. The client renders in arrival order and never reorders by timestamp.

## 2. The delivery choke point

Route **every** outbound send through one wrapper on the consumer (e.g. a single helper method that all `send_json` / channel-layer message handlers call). That wrapper:

1. Assigns `seq` (increment a per-connection counter; consumer event-loop context makes this safe — verify no send path bypasses the wrapper, including channel-layer group handlers and any tick-engine-originated deliveries).
2. Ensures `ts` is present (stamping it at delivery only if a creation site failed to — and log a server-side warning naming the offending message type when that fallback fires, so unstamped creation sites get found and fixed).
3. Sends.

Audit the consumer for every send site and collapse them onto the wrapper. After this brief, a message that reaches the client without passing the choke point is a bug by definition — this single-point property is exactly what the firehose will tap.

## 3. Client rendering

- `output`-category messages display a **dim timestamp prefix** in the player's local time: `[HH:MM:SS.ss]` — hours/minutes/seconds plus **two decimal places** on the seconds, derived from `ts`. Styled visually subordinate to the message text (dim/low-contrast within palette rules).
- The timestamp span is **`aria-hidden="true"`** — the ARIA live region must read message text clean, without timestamp noise on every line. Verify with the output pane's existing live-region behavior.
- Non-`output` message types carry the envelope but display nothing new.
- Messages render strictly in arrival (`seq`) order. On reconnect, the client resets its sequence expectation and renders the fresh full state per the v19 client-state sync pattern.

## 4. Out of scope

- Any persistence or log sink (Firehose milestone).
- A player-facing `timestamps on|off` preference — ruled into this version's **commands brief**, not here (boolean commands always take explicit values).
- Any change to message content, categories, or game behavior. This brief is additive metadata plus display.

## 5. Verification (all must pass before the architecture doc step)

1. Every outbound message type observed over a play session carries `ts` (epoch ms, sane value) and `seq`.
2. `seq` is strictly increasing per connection under mixed concurrent sources: active combat ticks + another character chatting/moving in the same room + rapid movement commands. No gaps-by-design assertion needed — only monotonicity.
3. The creation-site fallback warning (§2.2) does not fire during a full play session (all creation sites stamp `ts` themselves).
4. Reconnect: new connection restarts `seq` at 1; client renders cleanly with no stale-order artifacts.
5. Display: output lines show `[HH:MM:SS.ss]` in local time, dim; two decimal places present; non-output messages unchanged visually.
6. Screen reader pass: live region reads message text without timestamps.
7. No gameplay or message-content regressions: room look, combat, commerce, movement, map messages all behave identically apart from the envelope.

## 6. Architecture doc update (LAST — gated on all implementation and verification above being complete and passing)

Update `docs/shyland/Shyland_Architecture_v20.md` **in place, no version bump** (per the multi-brief convention; the file was created by V20 Brief 1). Update: the WebSocket message reference (envelope fields on every message, semantics of `ts` vs `seq`, per-connection reset), the consumer section (the delivery choke point and the rule that all sends route through it; its role as the future firehose tap), and the client section (timestamp rendering and the aria-hidden stance). Do not remove any file.

## Closeout report

Report: commit hash, each verification result (including the mixed-source ordering evidence), and confirmation that #32 is closed with a closing comment referencing this brief.
