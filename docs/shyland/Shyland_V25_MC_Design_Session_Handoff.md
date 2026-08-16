# Shyland V25 (MC) — Design Session Handoff

**Written 2026-08-16 by the ops session that scoped the major, at operator direction.**

This document hands the V25 opening design session everything the scoping discussion produced beyond the issues themselves. Provenance rules: **operator rulings live on the tracker** (issue comments dated 2026-08-16) — this document summarizes them and the tracker wins on any divergence. Technical claims below were **verified against the repo during the ops session** (source noted inline); everything labeled *recommendation* is exactly that — Claude's suggestion, unruled, for the design session to confirm, modify, or discard.

**Founding ticket: #269.** The session's plan of record for the constellation: the `monitoring-and-command` label (`gh issue list --label monitoring-and-command --state all`).

---

## 1. The major, named

**V25 = MC — Monitoring and Command.** Operator ruling, 2026-08-16: "the firehose" is renamed MC, and the major ships ahead of new zones so that AI actors (`sudo` bots, Sirius, player pets, NPC chat responders) are unblocked. *"MC Shyland in the house."*

Consequences the design session owns:

- **New zones move to a later major.** Standing docs assert "Version 25 = new zones" — instructions v37 (§Release Model line ~118, §Zones Reference line ~337), GDD `section_02_world_model.md` ("the V25 zones are expected to require the Verdant Reach", "when a V25 gate first asks for it"), and the v24.15 changelog row ("champion and world_boss design-ahead for V25"). All are unshipped-design references → design content → **rethemed on the version branch, never on main**. The changelog rows are historical record — re-point the *forward-looking* references only; whether shipped changelog rows are ever touched is a question to answer **no** by default.
- **Terminology sweep** (#264): seven forward-looking "firehose" references across GDD source, arch doc, and instructions, enumerated in the issue. Same motion as the retheme.
- **House style**: operator gave both "Monitoring and Command" and "MC." One-line ruling needed before seven files get edited in seven voices (#264 records the question).

## 2. State of the world (verified 2026-08-16)

| Fact | Value | Verified via |
|---|---|---|
| Last release | **V24.31, closed** — merged PR #256, ops corrections #257 applied after | `git log` on main |
| `SHYLAND_VERSION` on main | `"24.31"` | `django/src/apps/shyland/version.py:8` |
| V24 queue | **Drained** — 36 issues carry `V24`, all closed; no open issue carries the label | `gh issue list --label V24 --state all` |
| Open milestones | **None** | `gh api repos/…/milestones` |
| Nothing in flight | No version branch active; next release starts with this design session | branch survey + tracker |
| Active instructions | **v37** (daemon-inspection pass) | `docs/shyland/Shyland_Project_Instructions_v37.md` |

V24 (new-zone-prep) ends by implication when V25.0 ships, per the release model. The shipping release's changelog row notes the drain — that's the whole event.

## 3. Rulings already made (tracker is authoritative; dated 2026-08-16)

1. **Total capture** (recorded on #260): *nothing in the game is private.* Every category through the MC sink, speech included, future DMs included — no exclusions at the tap, no conditionals, no blockers. DMs are private *between players*, never private *from the game* (design-ahead, binding on any future DM design). Agents get the full stream. Capture serves balance, analysis, and AI — not just moderation. **§10.5 is reversed; the GDD text harmonization is the remaining work and lands with 25.0.** Retention is now a purely operational (volume/disk) question. The exclude-speech-by-default recommendation was explicitly rejected.
2. **Redis role opening** (recorded on #37): expanding Redis beyond the channel layer for MC is welcome — "especially things like firehose retention." The formal role-change ruling + doc updates (CLAUDE.md / arch-doc Redis lines) ride the release that ships it.
3. **RAM posture** (recorded on #267): the hot-window budget is soft — instance RAM pre-approved in principle, ElastiCache the named escalation, but "we're a few users away from that": build for the current single-box reality; keep the Redis endpoint configurable as the one cheap future-proofing.
4. **Kill switch is HIGH PRIORITY** (recorded on #266): operator-ruled. Recommended crisp reading, for the session to confirm: *ships no later than the first live AI actor.*
5. **V25.0 ships nothing real** (recorded on #269): version bump + major-opening mechanics + the design/doc pass only. 25.1 sees the first functional change. This shaped the founding-ticket choice (#37 would outlive the milestone; v35 litmus).
6. **Label**: all MC issues carry `monitoring-and-command` (renamed in place from `firehose-logging`; standing direction for new MC filings).

## 4. The issue map (14 tickets)

| # | Role | One line |
|---|---|---|
| **#269** | **Founding, 25.0** | The major design pass + version opening; closes with 25.0 |
| #37 | Monitoring core | Universal event logging at the taps; sink, store, retention-as-volume, query. **No open blockers** (#32 shipped v20; chat ruled) |
| #33 | Monitoring | Combat internals instrumentation (tick engine — rolls that never become messages); explicitly unblocked |
| #191 | Consumer | Command-pattern watcher — mines behavior for the next heal/loot-shaped verbs |
| #260 | Policy — **ruled** | Total capture; open only for the GDD text landing (25.0) |
| #261 | Command half — scoping | How a non-human actor acts; identity, ingress, authz, rate, failure. Likely v35 action-item shaped |
| #262 | Actor | `sudo` AI watcher; collides with the shipped "sudo never responds" ruling — reversal or silence is a design choice |
| #263 | Actor | Player pets/companions; may be AI; Machinist's missing core loop; **gated by #220**; `train` verb noted (operator) |
| #264 | Docs | firehose→MC terminology sweep + house-style ruling; pairs with the zones retheme (§1) |
| #265 | Actor | NPC chat responders; **speech-only actuation = thinnest real slice of the Command half**; silence is in-character failure |
| #266 | **HIGH PRIORITY** | The kill switch — one lever, game-side cut points, kills actors not capture |
| #267 | Infrastructure | MC egress — Streams inside the trust boundary, WebSocket across it; auth, backpressure, resume cursors |
| #268 | Infrastructure | Agent runtime & ops — hosting, supervision, credentials, cost caps; likely v35 action-item shaped |
| #259 | Actor (design) | Sirius — felis sapiens companion; whim is the character; unfinished design |

Adjacent non-MC: **#220** (shared-NPC combat unmodeled — gates any actor that fights), **#223** (uptime monitoring — sibling of #268), **#236** (`wall`), **#219** (`readme` — candidate disclosure surface, non-blocking per #260), **#214** (AWS — where an ElastiCache move would live).

## 5. Technical findings (verified in-session; provenance inline)

**Feasibility: yes, comfortably.** Every player's browser is already a remote real-time client (nginx → Daphne → Channels/Redis, `/ws/` proxied with a 24h read timeout). An MC consumer is the same shipped machinery with a wider subscription. Volume arithmetic: a busy night ≈ 100–200 events/s × ~300 B ≈ 30–60 KB/s — a fraction of one WebSocket's capacity. Latency: transport is tens of ms; **model inference (0.5–3 s) is the only real clock** — fine for chat, tight for 3-second combat rounds, and never the pipe's fault.

**The tap subtlety (recorded on #37; verified against `Shyland_Architecture_v24.md:1375` and GDD §10):** the designated tap, `SkylandConsumer.send_json`, is **per-connection**, and `seq` is per-connection monotonic. A room broadcast to five players passes five choke points → a delivery-level sink records **one row per recipient, not per event**. Right for "what did this player see" (#191); wrong for the canonical event record. Creation-level vs delivery-level capture must be placed deliberately — and a creation-level tap must exist **in the ticker's process too** (tick-engine broadcasts multiply identically; command ingress `receive_json` is naturally singular).

**Stack facts (verified against `docker-compose.yml`):** `redis:7-alpine` — Streams available, **no Redis Stack modules** (no RedisJSON/RediSearch — don't design against them); **no published ports** (only nginx faces the network — remote agents can never and must never speak Redis directly); **no volume** (ephemeral across recreation — correct for a channel layer; a deliberate decision point once the hot window has value). Also: `local.py` uses `InMemoryChannelLayer` — a Streams-based MC requires real Redis, so the containerized dev stack is the dev target and bare-local is out for MC work.

**The architecture sketch that fell out (recorded on #37/#267 — a sketch, not a ruling):**

- Sink = `XADD` to a stream at the creation-level taps (django consumer + ticker), fire-and-forget in try/except — a Redis hiccup drops a log line, never a game action. Additive-never-load-bearing holds **by construction**.
- Stream ids (`<ms>-<n>`) are the **global resume cursor** per-connection `seq` can never be; replay is native; ordering is total.
- **Consumer groups** give every reader (Postgres persister, #191, #262, #265) its own cursor, pace, ack/pending, and crash recovery — a slow agent never backpressures the game or its siblings.
- **Retention is `XADD … MAXLEN ~ N`** — the hot window is bounded by construction. **Two-tier retention:** Redis = hot window in RAM (live agents, reconnect-replay); a persister consumer group batch-drains to **Postgres as the durable record** (EBS disk, SQL analysis, policy-pruned). RAM math: ~1–20 events/s sustained × ~400 B ⇒ a 1M-entry cap is a few hundred MB worst case; the cap is sized deliberately in the brief and the ceiling is soft (§3.3).
- **Trust boundary:** Streams solve buffering/replay/cursors *inside*; WebSocket-through-nginx solves transport *across*; Django auth secures agents exactly as it secures players. Same front door, wider subscription.
- Bonus, cheap: sorted-set counters at the sink (`ZINCRBY` on unknown-command attempts, error frequencies) give a live "what are players fumbling for" leaderboard before any agent exists.

**The actor insight:** four actor shapes are filed (#262 watcher, #263 pets, #265 NPC chat, #259 Sirius). **Speech-only actuation (#265) is the thinnest real slice of the Command half** — a voice, not hands; the output surface (attributed say-color speech) already shipped; chat tolerates model latency; and the failure posture is silence, which is in-character and identical to today's game. The kill switch's reliable form is **game-side** (cut egress forwarding, refuse at the actuation ingress) — works even when every agent process is hung.

## 6. Design questions the session must take up

In rough dependency order; the session rules the real agenda.

1. **House style** for MC naming (one line; unblocks #264's edits).
2. **GDD text for the total-capture ruling** — harmonize §7.1/§10.5 (#260); GDD-first law applies.
3. **Terminology sweep + zones retheme** (#264 + §1) on the branch.
4. **Queue order** — which tickets found 25.1, 25.2, … (see §7 for a recommendation). Includes sequencing #220 and the kill-switch gate (#266).
5. **Creation-level vs delivery-level capture** (#37 comment) — shapes the sink and the wire format.
6. **Streams vs alternatives** — confirm the hot-tier architecture and the Redis role-change ruling it implies.
7. **The Command half** (#261) — far enough to know whether V25 ships any actuation, or monitoring-only with Command as V26+. Either is legitimate; it should be ruled, not defaulted.
8. **The `sudo` silence question** (#262) — reversing a shipped ruling is a design act.
9. **AI speech vs the pooled-speech doctrine** (#265) — generated speech as an explicit third category.
10. **v35 action-item classification** — #261 and #268 (probably also #266's arc) never join milestones; slices ride briefs with ruling comments.
11. **Milestone + label mechanics** — create `V25` label, apply across the constellation (the session's call which), re-triage per the major's first-session duty; create `Version 25.0` milestone holding #269 (+ #260/#264 if the session rules they close with 25.0).

## 7. Recommended release ladder (*recommendation — unruled*)

| Release | Founding ticket | Ships |
|---|---|---|
| **25.0** | #269 | The design pass, GDD harmonization + sweeps, version bump, major-opening mechanics. No functional change (operator expectation, recorded). |
| **25.1** | #37 | The sink: creation-level taps (consumer + ticker), Redis Stream hot tier, Postgres persister, retention caps. First real change; "the firehose works." |
| **25.2** | #33 | Combat internals instrumentation onto the same stream. |
| **25.3** | #267 | Egress: agent authn, the MC WebSocket endpoint, resume/replay contract. |
| **25.4** | #266 | The kill switch — in place **before** any actor goes live (the #266 gate). |
| **25.5+** | #262 or #265 | First live actor (watcher = zero player surface; NPC chat = thinnest Command slice). Then #191, and the rest as ruled. |

#263 (pets) waits on #220; #259 (Sirius) waits on the actor substrate; #261/#268 ride as action-item slices throughout.

## 8. Session mechanics (standing law, for convenience)

First design session of the release: create `version_25_0` from main, worktree, version-start rituals; **first agenda item = verify the prior release's end state from committed reports** (V24.31 closeout artifacts are on main). Create the `V25` label and milestone; re-triage the labeled queue against the theme. GDD-first authoring; rulings recorded on issues immediately; briefs born committed; end ritual = issues report on the version branch. Process docs newer than the branch merge forward from main before dependent sessions run.

---

*Everything here that is not a dated operator ruling is input, not law. The design session rules.*
