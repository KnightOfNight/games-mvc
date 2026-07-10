# Shyland Architecture

> Authoritative technical reference as of commit f914cd0 (v19 brief 6: player-controlled attack focus).
> Describes what is built. For design intent see the current GDD.
>
> **v19 is implemented across multiple briefs; briefs update this file in place. Brief 1 begins the v19 implementation series. Final version-stamp reconciliation and GDD sync happen at closeout in the design chat.**

---

## 1. Overview

Shyland is a free, browser-based Multi-User Dungeon. The primary interface is text: players connect via WebSocket, type commands, and read descriptive output. A minimal visual chrome (status bar, side panel) supplements the text pane. As of this commit, v16 adds the in-game character creator: a player with no `Character` who visits `/shyland/play/` is redirected to a creation form where they choose an Origin, an Archetype, and a Name, then spawn into The Convergence. Supporting changes: `Character.name` is now a real database field (previously a read-only property over the gamer tag), `Origin` and `Archetype` gained attire flavor-text fields and real seeded descriptions, and the `better-profanity` dependency was added for name filtering. v17 adds the Infinity City world seed — a data-only change (no models, no migrations) that replaces the 5-room placeholder starter zone in `seed_world.py` with the full first-version map of The Convergence: 4 park-path areas (Wisteria Walk, Bamboo Run, Basalt Way, Fern Boards), 54 rooms (obelisk hub, four park paths, a 35-room ring street, and Morra's Smithy), and 9 non-combat NPC definitions placed via `RoomSpawn`. v18 (in progress across multiple briefs) begins The Verdant Reach series. Brief 1 ships the Mk 1 item kit: 23 fantasy `ItemDefinition` seed rows (22 net-new plus the legacy Copper Ring absorbed as Copper Ring of Wisdom) covering a leather armor set, a wooden shield, four weapons, and twelve copper accessories; a `suppress_mk_suffix` display field on `ItemDefinition` (migration `0018`); a central `get_display_name_with_tier()` helper in `item_utils.py`; and a rewritten `equip` command implementing a general exchange rule (one-for-one auto-swap, refusals on multi-item or ambiguous displacement). Brief 1 contains no zone content — Verdant Reach rooms, NPCs, and drop tables come in later v18 briefs. Brief 2 ships the Obelisk Network, Shyland's fast-travel system (GDD 2.11): the superseded `ZoneGate` model is removed and replaced by `TravelNode` (one node per room, obelisk or checkpoint type) and `TravelMessage` (three seeded flavor pools), the `travel` command is implemented in the consumer (list + go forms, revelation derived from `RoomVisit`), the Primordial Sphere NPC is placed at the Heart of the Convergence, and the Heart is registered as the network's first node ("The Convergence", obelisk). Brief 2 also contains no Verdant Reach content. Brief 3 ships four zone-agnostic engine mechanics for battle-zone encounter design (migration `0020`, one `AddField` per model): boss-gated spawns (`RoomSpawn.requires_living_npc` + a tick-engine gate in `process_npc_respawn`), guaranteed-group loot (`LootTableEntry.guaranteed_group` + a rewritten `generate_loot_from_table`), per-NPC death messages (`NpcDefinition.death_message`, broadcast once to the room at death), and outleveled XP reduction (`xp_for_kill` pays −20% per level over the NPC's Mk band, floored at 10% of base and never below 1 XP). Brief 3 contains no zone content either — every mechanic is data-driven; Verdant Reach rooms, NPCs, spawns, and loot tables come in later briefs. Brief 4 ships the commerce loop and one combat quality-of-life change (migration `0021`): item valuation (`ItemDefinition.base_value` plus four helpers in `item_utils.py` — value, sale price, repair cost, repair success chance), the `material` item type with two seeded materials (Animal Hide, Insect Carapace) and a `base_value` back-fill across all definitions, the `list`/`buy`/`sell` commands routed to a living vendor in the room (`VendorEntry.sold_count` tracks finite-stock exhaustion), the `repair` command routed to a living repairer (`NpcDefinition.is_repairer`), and targetless `attack`/`kill` that auto-targets the earliest-engaged living NPC while the player has aggro. Brief 4 also ships no zone content — vendor and repairer NPCs arrive with the Verdant Reach world seed. Brief 5 is the first content payload of the series: the partial world seed for The Verdant Reach (Z01, levels 1–10) — the zone row and 6 areas, 69 rooms (the Tree Arch entrance, Fernwater Vale with the villages Reedmere, the ancient stair, The Sagewind Flats with Windhome, and four caves: Spinner's Hollow, the Silken Cleft, the Whistling Sink, the Drone Pit), the opened Verdant gate on the ring street, six species unarmed-message pools, 29 NPC definitions (surface creatures, villagers, the first vendors Essa/Sona and repairers Maro/Tavik, the Verdant Shard, cave insects, three bosses with death messages, three boss-gated minion definitions), 7 loot tables (three with guaranteed groups for boss drops), 57 room spawns, vendor stock, and the network's first checkpoint nodes (Fordwatch, Stairhead). Brief 5 also fixes a tick-engine respawn bug: dead instances now hold their spawn slot until their timer clears them, so `respawn_minutes` and boss-minion gating actually take effect. Brief 6, the final brief of the series, completes the zone: The Viridian Ridge (51 rooms — the switchback climb from Cragfoot through the villages Stonestep, Highfold, and Lastlight, four warned-about aggro offshoots, and the summit garden of the Verdant Crown), the three mountain delves (The Undercrag 9 rooms, Chitterdeep 10, Hollowcrown 11), vr-f18's north exit wired at last, 20 more NPC definitions (including the three delve bosses — the Undercrag Weaver, the Chittering King, and the Crowned Devourer — with death messages and boss-gated minions, plus the unique Verdant Sphere at the summit), three ridge unarmed pools, 5 loot tables (the Devourer's guaranteeing an Epic accessory), 72 spawns, Ridda's vendor stock and Old Brammel's repair bench at Cragfoot, and two travel nodes — Cragfoot (checkpoint) and The Verdant Crown, the Obelisk Network's second source node. Z01 stands complete at 150 rooms and 10 areas. v19 (in progress across multiple briefs) is a fix-and-feature pass from v18 play-testing; Brief 1 ships the presence-ownership fix, the wallet display (`wallet` command + `inventory` section), and the buy/sell vendor-check reorder. Brief 2 closes the client state synchronization gap found by v18 play-testing: `send_room_description` now fresh-fetches the character before building its status payload (fixing the jump-and-snap-back bar bug on `look`/`move`/`travel`/login), a level-up that ends a kill now pushes the refilled Vitality/Longevity bars to the client, and death respawn synchronizes the consumer's room-group membership, `last_direction`, and dying-command gate with the tick engine's server-side state change instead of leaving the client stranded in the old room. Brief 3 fixes combat narration found by v18 play-testing: NPC unarmed attacks no longer speak in the player's second-person voice (`get_unarmed_message` gained an `attacker_name` substitution and a `fallback_slug` parameter — NPCs fall back to a new `npc-default` pool, never the player-perspective `default` pool; eight Verdant surface animals gained third-person species pools), `cmd_attack` now distinguishes a genuine new engagement (`You move to attack …!`) from a no-op repeat against an already-engaged target (`You're already fighting …`), same-name NPCs in a room are disambiguated with positional ordinals (`npc_display_name`), and the tick engine's `broadcast_to_room` gained an `exclude_pk` parameter so a character's own kill and fall announcements no longer duplicate the personal line they already received. Brief 4 ships the complete death-and-dying presentation: falling now clears the fallen player's output pane (a new engine/consumer-initiated `clear` event, implemented client-side as an ARIA-safe content wipe of the existing live region — never a rebuild) and replaces it with a red fatal-blow line; every active effect on the faller is canceled (`removed_by='dying'`) and their own queued/future attacks are discarded from the moment of falling, so a character who drops mid-round can no longer land a posthumous kill and no combat output of any kind (hit lines, kill lines, "Combat has ended.") reaches a dying player; a lore-only escalation ladder (no numerals, no time units) plays out over the 30-second window from an in-memory per-tick-engine scheduler; `use`-ing a vitality-restoring item while dying revives the character with exactly the healed amount (no bonus, no forced full heal) and resumes combat naturally; and expiry now announces `"The darkness takes you."` before the existing death/respawn flow. Brief 4 Amendment 1 removes a room-title line from between the `clear` event and the fatal-blow line, found redundant with the client's persistent room-name chrome during brief 4 play-testing. Brief 5 re-baselines combat feel: `resolve_hit`'s v18 d100-band formula, under which miss and graze were mathematically unreachable for a well-built attacker, is replaced with a contested d20 to-hit plus an independent critical roll, so Z01's authored NPC stats now mean what they say. Brief 6 makes attack focus player-controlled: `CombatSession.focus_npc` (migration `0022`) is the single field driving both the auto-attack target and the Acuity single-target bonus, replacing the old implicit "always `npcs[0]`" behavior; `cmd_attack` gains a three-way outcome (engage steals focus, repeat against the current focus is a no-op, naming an in-session non-focused target refocuses with a personal-only message); the tick engine auto-shifts focus with an announcement when the focused NPC dies and others remain, and clears it when the session ends; and `npc_display_name`/`ORDINALS` move from `consumers.py` to `combat_utils.py` so the engine's shift announcement can reuse the same ordinal logic as the consumer. See [Section 7](#7-what-is-not-yet-built) for unbuilt systems.

---

## 2. Infrastructure

*(unchanged from v15)*

### 2.1 Docker Compose stack

```
docker-compose.yml defines five containers:

  nginx      nginx:alpine          SSL termination; WebSocket proxy at /ws/
  django     python:3.12-slim      Daphne ASGI server; Django 5 + Channels
  postgres   postgres:16-alpine    Primary database; persistent volume pgdata
  redis      redis:7-alpine        Django Channels layer for WebSocket routing
  ticker     shyland-django image  Tick engine; run_tick_engine management command
```

**Network flow:**

```
Browser
  ↓ HTTPS / WSS  (port HOST_PORT, default 40443)
nginx
  ↓ HTTP proxy_pass http://django:8000
  ↓ Sets X-Forwarded-Proto: https on all requests
  ↓ WebSocket Upgrade headers forwarded for /ws/ paths
Daphne (Django ASGI)
  ├── HTTP requests → Django WSGI stack
  └── WebSocket /ws/* → Django Channels consumers
        ├── reads from / writes to Redis (channel layer)
        └── reads from / writes to PostgreSQL (ORM)
```

Only `nginx` exposes a host port. `django`, `postgres`, `redis`, and `ticker` are internal to the Docker network. `postgres` has a healthcheck; `django` and `ticker` both depend on it being healthy before starting. `ticker` uses the same `shyland-django` image as `django` — no separate build step.

### 2.2 Makefile workflow

| Target | What it does |
|--------|-------------|
| `make setup` | First-time: wizard + build + start |
| `make build` | Rebuild Docker image and recreate containers — **required after any Python/template/settings change** |
| `make start` / `make stop` / `make restart` | Container lifecycle |
| `make logs` | Follow all container logs |
| `make tick-logs` | Follow ticker container logs only |
| `make migrate` | Run `python manage.py migrate` inside the container |
| `make makemigrations [APP=name]` | Generate migrations and auto-sync generated files back to local filesystem |
| `make shell` | Django shell inside the container |
| `make createsuperuser` | Create a Django admin superuser |
| `make new-app NAME=x` | Scaffold a new game app in `apps/` |
| `make reset` | Drop all Docker volumes, rebuild, start, migrate, and run `seed_world` — full data wipe |

> **Critical workflow note:** After editing any file under `django/src/`, run `make build` before testing. `make restart` alone recreates containers from the existing image and picks up no changes.

---

## 3. Django Project Structure

The Django project lives in `django/src/game_mvc/`.

### 3.1 `asgi.py`

Entry point for all traffic. Sets `DJANGO_SETTINGS_MODULE` to `game_mvc.settings.production` by default.

```python
application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
```

`AuthMiddlewareStack` populates `scope['user']` with the authenticated Django `User` before the consumer receives the connection.

### 3.2 `routing.py` — WebSocket URL registry

```python
path('ws/shyship/<uuid:game_id>/', ShyshipConsumer.as_asgi()),
path('ws/shyland/',               SkylandConsumer.as_asgi()),
```

### 3.3 `urls.py` — HTTP endpoints

| Path | Handler |
|------|---------|
| `/` | `HomeView` (game lobby) |
| `/admin/` | Django admin |
| `/accounts/` | `django.contrib.auth.urls` (login, logout, password) |
| `/api/auth/` | DRF browsable API auth |
| `/shydle` | Shydle app |
| `/shyship/` | Shyship app |
| `/shyland/` | Shyland app |

App-level routes inside the Shyland include are documented in [Section 4.10](#410-http-routes-urlspy).

### 3.4 Settings

| File | Used when | Notable differences |
|------|-----------|---------------------|
| `base.py` | Always imported | PostgreSQL, Redis channel layer, all INSTALLED_APPS |
| `production.py` | Default (container env) | `DEBUG=False`, `SECURE_PROXY_SSL_HEADER` set |
| `local.py` | Set `DJANGO_SETTINGS_MODULE=game_mvc.settings.local` | `DEBUG=True`, `ALLOWED_HOSTS=['*']`, `InMemoryChannelLayer` |

### 3.5 Platform profile system (`apps.profiles`)

`apps.profiles` extends `auth.User` with a `UserProfile` model (`gamer_tag` CharField, max 20, unique, nullable). A `post_save` signal auto-creates a `UserProfile` for each new `User`. As of v16, Shyland no longer derives `Character.name` from the gamer tag at read time — the gamer tag (falling back to `user.username`) is only the *default value* offered in the character creator's Name field. Once a `Character` exists, its `name` field is authoritative and independent of the profile.

---

## 4. The Shyland App (`apps/shyland/`)

### 4.1 Models (`models.py`)

#### Module-level constants

*(unchanged from v15)*

```python
COMBAT_ROUND_TICKS    = 3     # ticks between combat rounds
DYING_DURATION_SECS   = 30    # seconds in dying state before death fires
FLEE_COOLDOWN_TICKS   = 3     # rounds before another flee attempt is allowed
STALE_SESSION_SECS    = 30    # close a CombatSession with no tick activity
XP_PENALTY_MIN_LEVEL  = 10    # level threshold for XP death penalty
DEATH_DURABILITY_LOSS = 10.0  # durability % lost per equipped item on death
CORPSE_DECAY_MINUTES  = 10    # minutes until a corpse is deleted by the tick engine
ACUITY_DRIFT_RATE     = 0.01  # Acuity movement per tick toward baseline
STAT_POINTS_PER_LEVEL = 5     # unspent stat points awarded per level-up
VITALITY_REGEN_SECS   = 120   # seconds to regen full Vitality from zero out of combat
LONGEVITY_REGEN_SECS  = 3600  # seconds to regen full Longevity from zero out of combat
```

#### `UnarmedMessagePool`, `UnarmedMessage`

*(unchanged from v15)*

#### `Origin`

One new field added in v16:

```
name             CharField(100)
slug             SlugField(unique)
description      TextField(blank)
acuity_baseline  FloatField
acuity_band_low  FloatField
acuity_band_high FloatField
attire_material  CharField(200, blank=True, default='')   ← new in v16
```

Ordering: `['name']`. `attire_material` holds the Origin's material/palette phrase for the starting-attire flavor text (see Section 4.11). `description` is now seeded with real content (see Section 4.8).

#### `Archetype`

One new field added in v16:

```
name                 CharField(100)
slug                 SlugField(unique)
description          TextField(blank)
primary_stat_1       CharField(3, choices=STAT_CHOICES)
primary_stat_2       CharField(3, choices=STAT_CHOICES)
attire_silhouette    CharField(200, blank=True, default='')   ← new in v16
unarmed_message_pool ForeignKey(UnarmedMessagePool, SET_NULL, null, blank, related_name='archetypes')
```

Ordering: `['name']`. `STAT_CHOICES` covers all six stats: str, dex, end, int, wis, per. `attire_silhouette` holds the Archetype's garment-silhouette phrase for the starting-attire flavor text (see Section 4.11). `description` is now seeded with real content (see Section 4.8).

#### `Zone`, `Area`, `Room`, `RoomVisit`

*(unchanged from v15)*

#### `Character`

Changed in v16: `name` is now a real, required database field, placed immediately after `user`:

```
user  OneToOneField(User, CASCADE, related_name='shyland_character')
name  CharField(20)                                                    ← new in v16
```

Uniqueness is **case-insensitive and enforced at the database level** via a functional constraint in `Character.Meta`:

```python
constraints = [
    models.UniqueConstraint(
        Lower('name'),
        name='shyland_character_name_ci_unique',
        violation_error_message='That name is already taken.',
    ),
]
```

Django validates this constraint in `full_clean()`, so the admin and any `ModelForm` path get a friendly "That name is already taken." error rather than an `IntegrityError`. `Character.clean()` also strips surrounding whitespace from `name`, so padded names cannot be stored through any `full_clean()`-based write path.

The previous read-only `@property def name` — which returned `user.profile.gamer_tag` falling back to `user.username` — has been **removed entirely**. `Character.name` is set once at creation (defaulting to the gamer tag in the creator form, but freely overridable) and is thereafter independent of the profile. The max length of 20 matches `UserProfile.gamer_tag`'s constraint. The `ObjectDoesNotExist` import that supported the property was also removed.

Migration `0017` adds the field in the standard safe three-step form so it applies cleanly on databases that already contain `Character` rows (this codebase runs as multiple installations): `AddField` nullable → `RunPython` backfill (gamer tag falling back to username, truncated to 20, deduplicated case-insensitively with numeric suffixes) → `AlterField` to non-null + `AddConstraint`. On this deployment the table was empty, so the backfill was a no-op; the populated-table path was exercised by planting rows on the 0016 schema and migrating forward.

#### `ItemDefinition`

One new field added in v18 (brief 1), alongside the existing display-related fields (`mystery_name`, `mystery_description`):

```python
suppress_mk_suffix = models.BooleanField(
    default=False,
    help_text='If True, display names never show the "Mk N" suffix. '
              'Used for tier-material items (copper/silver/gold/platinum) '
              'whose material name already conveys the tier.',
)
```

This is **display-only**: `mk_tier`, scaling, and rarity machinery are untouched — a Copper Ring of Strength still has a real `mk_tier` and scales normally; the player just never sees "Mk N" appended to a tier-material name. Flavor materials (iron, wood, leather) do *not* suppress — an Iron Sword still displays "Iron Sword Mk 1". The suffix suppression is honored by `get_display_name_with_tier()` in `item_utils.py` (see Section 4.6). Migration `0018` adds the field (single `AddField` with a default — safe on populated databases).

Brief 4 adds a second field and a new item type (migration `0021`):

```python
base_value = models.BigIntegerField(
    default=1,
    help_text='Authored worth in copper at Mk 1, Common. Item value = '
              'base_value × mk_tier × rarity multiplier. Sale price is '
              'one third of value.',
)
```

`base_value` is the single authored input to item valuation — everything else is derived by the `item_utils.py` helpers (see Section 4.6). Every seeded definition gets an authored value via the seed's back-fill (see Section 4.8); the default of 1 exists only so the migration is safe, and the seed's verification pass fails if any definition is left at it.

The `ITEM_TYPE_CHOICES` gained **`material`** ("Material") — vendor-sellable materials with no slots, stats, or durability (hides, carapaces, and their future kin). Materials flow through the same `ItemInstance` machinery (they have a real `mk_tier` and rarity, which scale their value) and sell through the same `sell` path as gear.

#### `TravelNode`, `TravelMessage` (new in v18 brief 2) — and `ZoneGate` removed

**`ZoneGate` no longer exists.** The model (introduced v15, authoring-only, never wired to a command; no gate data was ever seeded) was superseded by the Obelisk Network and deleted in brief 2 — model, admin registration, and all references. Migration `0019_travelmessage_travelnode_delete_zonegate` drops the table and creates the two new models below. Do not hunt for `ZoneGate` in current code; it survives only in migration history (`0016` created it, `0019` deletes it).

**`TravelNode`** — the node registry for the Obelisk Network (GDD 2.11). Fields:

| Field | Type | Notes |
|-------|------|-------|
| `room` | `OneToOneField(Room, related_name='travel_node')` | One node per room, enforced by the one-to-one |
| `travel_name` | `CharField(max_length=60, unique=True)` | Unique, typeable destination name shown in travel lists (e.g. "The Convergence") |
| `node_type` | `CharField(max_length=12, choices=...)` | `'obelisk'` (travel source **and** destination) or `'checkpoint'` (destination only) |

There is no per-character revelation table: a character's available destinations are derived entirely from `RoomVisit` — any node whose room appears in their visit records is revealed, permanently. The network is global (no zone scoping) and travel is free (no cost, no cooldown). Node rooms are safe by seeding convention (GDD 2.11); the travel logic performs no combat checks.

**`TravelMessage`** — global flavor-text pools for travel events. Fields: `category` (`'traveler'` — shown to the traveling player; `'departure'` — shown to players in the origin room; `'arrival'` — shown to players in the destination room) and `text`. Witness messages (departure/arrival) may include the literal placeholder `{name}`, replaced with the traveling character's name via `str.replace` (not `.format`, so stray braces in prose are harmless); traveler messages take no placeholders. One message is selected uniformly at random from the appropriate pool per event — travel text is never hardcoded. Pools are global, not per-zone.

#### Battle-zone mechanic fields (new in v18 brief 3)

Three fields, one per model, added by migration `0020` (all nullable/defaulted `AddField`s — safe on populated databases; unset means "exactly the pre-brief behavior"):

- **`RoomSpawn.requires_living_npc`** — nullable FK to `NpcDefinition` (`SET_NULL`, related name `dependent_spawns`). If set, the tick engine only refills this spawn while a live `NpcInstance` of that definition exists in the same room. This is a spawn dependency, not an encounter system: it gates boss minions on their boss — minions respawn on their own `respawn_minutes` timer while the boss lives, reinforcements stop the moment it dies (survivors remain until killed), and gated spawns refill again once the boss respawns, so the encounter resets as a unit. `null` = ungated, spawn behaves as before.
- **`LootTableEntry.guaranteed_group`** — `CharField(max_length=40, blank, default='')`, an optional group label (e.g. `"weapon"`). At roll time each distinct group in a table yields **exactly one** of its entries, every roll, unconditionally; the entry is chosen by weighted selection using `drop_chance` as a *relative weight* (weights need not sum to anything). Grouped entries make no independent drop rolls. Blank = today's independent per-entry roll.
- **`NpcDefinition.death_message`** — `TextField(blank, default='')`. If non-blank, broadcast verbatim to every character in the NPC's room (including the killer) exactly once, at the moment of death, after the kill line and before any corpse/loot output. No substitution placeholders — the text is authored per NPC and stands alone. Blank = no extra message.

#### Commerce fields (new in v18 brief 4)

Two fields added by migration `0021` (alongside `ItemDefinition.base_value` and the `material` type above; all defaulted `AddField`s — safe on populated databases):

- **`NpcDefinition.is_repairer`** — `BooleanField(default=False)`. This NPC offers repair services; the `repair` command routes to a living repairer in the room. Vendors need no analogous flag — an NpcDefinition with one or more `VendorEntry` rows is a vendor, as before.
- **`VendorEntry.sold_count`** — `IntegerField(default=0)`. Units sold so far. An entry with a finite `stock_limit` is **exhausted** when `sold_count >= stock_limit`: it is omitted from `list`, and buying it reports `Sold out.` Entries with `stock_limit=NULL` are unlimited and never exhaust. There is no restock mechanism yet — exhaustion is permanent until an admin resets `sold_count` or raises the limit.

#### Attack focus field (new in v19 brief 6)

One field added by migration `0022` (a nullable/defaulted `AddField` — safe on populated databases; unset means "exactly the pre-brief fallback behavior"):

- **`CombatSession.focus_npc`** — nullable FK to `NpcInstance` (`SET_NULL`, related name `+`). Player-controlled attack focus: the NPC the character's auto-attack targets each round and the NPC the Acuity single-target damage bonus applies to — one field drives both. `null` = no explicit focus; the tick engine falls back to the first live NPC in the session (see Section 4.9), so pre-existing active sessions keep working across the deploy with no data migration. Set by `cmd_attack` on engagement (new session or a newly-added in-session target — engagement always steals focus) and on an explicit refocus against an already-in-session target (see Section 4.3); auto-shifted by the tick engine, with an announcement, when the focused NPC dies and other live NPCs remain in the session; cleared when the session ends.

#### All other models

`EffectDefinition`, `EffectComponent`, `ItemInstance`, `EffectInstance`, `EffectComponentInstance`, `LootTable`, `NpcEffect`, `NpcInstance`, `Corpse`, `CombatAction` — *(unchanged from v15)*. `LootTableEntry` and `RoomSpawn` are unchanged apart from the v18 brief 3 fields above; `NpcDefinition` and `VendorEntry` are unchanged apart from the v18 brief 3 and 4 fields above. `CombatSession` is unchanged apart from the v19 brief 6 field above.

### 4.2 Currency system (`currency.py`)

*(unchanged from v15)*

### 4.3 WebSocket consumer (`consumers.py`)

Changed in v18: brief 1 rewrote the `equip` command and centralized name-plus-tier display formatting; brief 2 added the `travel` command; brief 4 added the `list`/`buy`/`sell`/`repair` commerce commands and targetless `attack`/`kill` under aggro. Changed in v19: brief 1 added the `wallet` command and an `inventory` wallet section, and reordered the vendor-presence checks in `cmd_buy`/`cmd_sell` ahead of the argument checks; brief 2 made `send_room_description` fresh-fetch its character and extended the personal-group message handler with an `event` field (see below); brief 3 reworked `cmd_attack`'s engagement messaging, added the `npc_display_name` ordinal helper, and extended `room_message` to honor engine-side broadcast exclusion (see below); brief 4 added revival to `cmd_use` and a `'clear'` event on `player_message` (see below); brief 6 gave `cmd_attack` a third outcome — refocusing an in-session target — and moved `npc_display_name`/`ORDINALS` out to `combat_utils.py` (see below). All other command handling *(unchanged from v16)*.

#### Revival in `cmd_use`, and the `'clear'` event (v19 brief 4)

`cmd_use` captures `was_dying = self._character_is_dying` before doing anything else — the in-memory dying flag kept current by the `'dying'`/`'respawn'` event handling below, not a DB read, since the character may have fallen between commands. The effect applies exactly as before (instantaneous `restore_vitality` mutates the same `Character` object `cmd_use` already holds, in place, inside the `@database_sync_to_async` call), the item is consumed, and its messages print unchanged. Only then does revival get checked, against a fresh read: `char_fresh = await self.get_character_fresh()`; if `was_dying and char_fresh.vitality_current > 0`, the character revives —

1. `revive_character(char_fresh)` clears `is_dying`/`dying_since` (two-field save, mirrors the tick engine's own dying-state writes).
2. `self._character_is_dying = False` — the `receive_json` command gate opens back up on the very next message, no round-trip through a fresh fetch required.
3. Personal system line: `Breath floods back into your lungs. You are alive — barely.`
4. `send_room_description(room, entering=False)` — the standard full room render (which also pushes the current, now-revived status payload), not a special-cased status dict.
5. `broadcast_to_room_exclude(f"{char_fresh.name} staggers back to their feet!", 'combat')` — the room hears it; the reviving player doesn't get a redundant copy.
6. Early `return`, skipping the generic post-`use` status send below it (the room description already sent one).

No bonus and no forced full heal — the character rises with **exactly** the amount the item restored, capped at `vitality_max` by the same `min()` `_apply_instant_component` always applied. A non-healing `use` (or one that doesn't push vitality above zero) takes the untouched path: item consumed, messages printed, generic status sent, dying window keeps closing — `cmd_use` never special-cases or blocks a non-revival use while dying, matching `receive_json`'s existing allowlist (`use` is the only verb permitted through the gate regardless of what it does).

**The character was never removed from their `CombatSession`** — only actual death does that (`execute_death`, Section 4.9) — so revival needs no session repair. The next combat round picks the character back up exactly as `load_participants` always would: the NPC-attacks-character guard (`if character.is_dying: continue`) no longer trips, and the auto-attack guard (`not character.is_dying`, also Section 4.9) no longer blocks a fresh player action either. Rising at a sliver of Vitality into an unfinished fight is intentional, not an oversight.

**The `'clear'` event** — `player_message` now checks `event.get('event') == 'clear'` first, ahead of the existing `text`/`status` delivery, and sends a bare `{'type': 'clear'}` to the client whenever it fires (independent of whether the same engine message also carries text — the tick engine's fall sequence sends it as its own zero-text message, see Section 4.9). Client-side (`game.html`), a `type: 'clear'` message runs `output.innerHTML = ''` — the exact same primitive the room-entry path already used for `msg.enter`, just exposed as its own message type so the engine can trigger it outside a room render. This clears the **contents** of the `#output` div only; the div itself (`role="log" aria-live="polite"`) is never removed or rebuilt, so a screen reader's live-region subscription survives the clear and the very next appended line — the fatal-blow line (see Amendment 1 below) — is announced normally. `aria-live="assertive"` is never used for any of this; politeness is unchanged.



#### Fresh-read status and the `player_message` event field (v19 brief 2)

`send_room_description(room, entering, force_long)` now opens with `char = await self.get_character_fresh()` instead of reading the cached `self.character`. Real bar changes (combat damage, passive regen, level-ups) happen in the tick-engine process and are written straight to the DB; the consumer's cached `self.character` only reflects what it looked like at connect or at the last command that happened to fresh-fetch. Since every caller of `send_room_description` (`look`, `cmd_move`, `travel`, login) built its status payload from that stale cache, all of them could show a bar value that the next tick "corrected" a moment later. `get_character_fresh()` re-assigns both `self.character` and `self._character_is_dying` as a side effect, so this one change also keeps the dying gate current on any command that reaches this method. The other two status-payload builders (`cmd_use`, `cmd_stats`) already called `get_character_fresh()` before building their payload and are unchanged.

The `player_message` handler (the `player_{character_pk}` group event fired by the tick engine, see Section 4.9) gained an `event` field on top of the existing `text`/`category`/`status` fields, read after those are delivered: `None` (default, no special handling — the vast majority of ticks), `'dying'`, or `'respawn'`.

- **`'dying'`** — sets `self._character_is_dying = True` directly, no DB fetch. The tick engine sends this the instant it sets `character.is_dying = True` server-side (both the combat brink-of-death path and the DoT-kill path), so the command dispatch gate (`receive_json`, blocks all commands but `use` while dying) is correct on the very next message the player sends — previously the flag only updated when a command happened to call a fresh-fetching handler, so a command sent between the fall and that next fresh fetch could slip through.
- **`'respawn'`** — runs the same synchronization sequence a normal move performs: `get_character_fresh()` (clears `_character_is_dying`, since the DB row is already updated by the time the engine sends this event), swap `self.room_group` from the old room to `room_{character.current_room_id}` (`group_discard` the old group, `group_add` the new one), reset `self.last_direction = None` (respawn has no direction for `flee` to reverse — the same rule `travel` follows), then `send_room_description(room, entering=True)` for the new room — identical to normal movement, including `RoomVisit` bookkeeping. Without this, a respawned character's client stayed subscribed to the death room's broadcast group and showed the death room's last-rendered output until their next explicit `look`.

#### Wallet display (v19 brief 1)

`cmd_wallet()`, dispatched on the verb `wallet` (no arguments; any given are ignored). Fetches a fresh character via `get_character_fresh()` — already `select_related('current_room__zone', ...)`, satisfying `format_wallet()`'s need for `character.current_room.zone` — and sends a single line: `Wallet: {format_wallet(character)}`. Subject to the same dying-state command gate as every other command (no special-casing).

`cmd_inventory()` gains a wallet section appended after the existing item listing, separated by a blank line:

```
Wallet:
  {format_wallet(character)}
```

The wallet line also uses a fresh `get_character_fresh()` fetch, independent of the `self.character`-derived equipment/item listing above it, so the copper and zone-display alias shown are always current. `format_wallet()` (previously defined but called by nothing) is no longer orphaned.

#### Buy/sell vendor-check order (v19 brief 1)

`cmd_buy`/`cmd_sell` now check for a living vendor in the room **before** checking whether arguments were given. A bare `buy`/`sell` in a vendor-less room now reads `There is no one here to trade with.` instead of `Buy what?`/`Sell what?`, which previously implied a shop was present. At a vendor, bare `buy`/`sell` is unchanged (`Buy what?`/`Sell what?`). Only the check order moved; no message text changed.

#### The `travel` command (v18 brief 2)

`cmd_travel(args)`, dispatched on the verb `travel`, with two forms. Both forms start with the same source checks against the current room's `TravelNode`:

- **No node in this room** → error: `There is no obelisk here. Travel is a gift of the obelisks — you must stand before one.`
- **Checkpoint node** → error: `The obelisks project their protection here, but only an obelisk itself can send you onward.` Checkpoints are destinations only; only an obelisk-type node can initiate travel.

The character's revealed destinations are computed as all `TravelNode` rows whose room has a `RoomVisit` for this character (helper `get_revealed_destinations`), excluding the node the character is standing at, ordered alphabetically by `travel_name`. No zone filtering — the network is global.

**`travel` (no argument) — list.** Empty set → `The Obelisk is silent. It has nothing to show you yet — the network reveals itself only to those who walk it.` Otherwise a header line `The Obelisk offers passage to:` followed by one plain line per destination — the `travel_name`, with obelisk-type nodes suffixed ` (obelisk)` and checkpoints unsuffixed (screen-reader-friendly, matching existing list output style).

**`travel <destination>` — go.** The argument is matched against the revealed set by case-insensitive prefix match on `travel_name`, additionally ignoring a leading `The ` on the node name (`_travel_name_matches` static helper — `travel verdant` and `travel the verdant crown` both match "The Verdant Crown"). No match → `The Obelisk knows no such place — or you have not yet stood there. Type "travel" to see where it can send you.` Multiple matches → the matching names are listed and the player is asked to be more specific; nothing changes. On a unique match, the travel sequence runs:

1. A random `departure` message (with `{name}` substituted) is broadcast to the origin room, excluding the traveler.
2. The character moves using the same machinery as normal movement: `group_discard` the old room group, the existing `move_character()` helper, `group_add` the new room group (`self.last_direction` is reset to `None` — travel has no direction for flee to reverse).
3. A random `traveler` message is sent to the traveler, followed by the full standard room output (`send_room_description(entering=True)` — identical to normal movement, including `RoomVisit` bookkeeping on arrival; no special-casing).
4. A random `arrival` message (with `{name}` substituted) is broadcast to the destination room, excluding the traveler.

Travel is free: no currency cost, no cooldown, and no combat check (node rooms are safe by design — safety is a seeding concern, not travel logic). The obelisk speaks no words: no NPC dialogue is involved; all travel text comes from the `TravelMessage` pools, selected randomly per event. Supporting DB helpers: `get_travel_node(room)`, `get_revealed_destinations(current_node)`, `get_random_travel_message(category)`.

#### The equip exchange rule (`cmd_equip`)

The old behavior — refuse whenever a target slot is occupied or a two-handed conflict exists — is replaced by a general exchange rule. For each slot in the item's `valid_slots` (in order), `cmd_equip` computes a **displacement set**: every currently equipped item that must come off for the new item to legally occupy that slot.

- The current occupant(s) of the slot, if it is at capacity. Slot capacity comes from the module-level `SLOT_CAPACITY = {'RING': 2}` — RING is the only slot a character has two of; every other slot holds one item. A slot below capacity contributes an empty base set; a slot at capacity contributes one candidate per occupant (displacing that occupant).
- If the new item is two-handed: every equipped item in MAIN_HAND or OFF_HAND, plus every equipped item whose definition is two-handed **regardless of its slot** — a two-handed item claims the character's hands from wherever it sits, including a two-handed bow equipped in RANGED.
- If the new item is one-handed and the candidate slot is MAIN_HAND or OFF_HAND: additionally, any equipped item whose definition is two-handed (its hands-claim conflicts even from RANGED).

Outcome selection, in `valid_slots` order:

1. **Any candidate with an empty displacement set** → equip there. Output: `You equip <item> in your <slot>.`
2. Otherwise, take the minimal displacement sets across candidates:
   - **Minimum size ≥ 2** → refuse, naming every item in the set: `You'd have to unequip your Iron Sword and your Wooden Shield first.` Nothing is unequipped.
   - **Minimum size 1, all minimal sets contain the same item** → **auto-swap**: unequip the displaced item, equip the new one, and send a single exchange message: `You unequip your Broadsword and equip your Wooden Shield in your Off Hand.` (Display names via `get_display_name()`.)
   - **Minimum size 1, but different candidate slots displace different items** (ambiguous — a third ring while both RING slots are full; a MAIN_HAND/OFF_HAND item while both hands hold different items) → refuse, naming the candidates: `Both ring slots are full — unequip your Copper Ring of Strength or your Copper Ring of Wisdom first.` (Non-ring ambiguity uses `You'd have to unequip your X or your Y first.`) Nothing is unequipped.

**Auto-swap defers to the existing unequip constraints.** Before swapping, the displaced item is checked with the same rules `cmd_unequip` applies — cursed items cannot be removed; a bag cannot come off if doing so would violate the carry limit. These checks live in the shared helper `_unequip_blocked_reason()`, used by both `cmd_unequip` and the auto-swap path, so the refusal messages are identical and a partial swap can never occur. The swap itself reuses the existing `unequip_item()`/`equip_item()` helpers, so soulbinding and slot bookkeeping behave exactly as a manual unequip-then-equip would.

A module-level `_join_owned_names(items, conj)` helper formats the `your X and/or your Y` lists in refusal and exchange messages.

#### Commerce commands (v18 brief 4)

`cmd_list`, `cmd_buy(args)`, `cmd_sell(args)`, `cmd_repair(args)`, dispatched on the verbs `list`, `buy`, `sell`, `repair`. No aliases.

**Routing.** A **vendor** is a living `NpcInstance` in the character's current room whose definition has at least one active `VendorEntry`; a **repairer** is a living instance whose definition has `is_repairer=True` (DB helpers `get_vendor_in_room` / `get_repairer_in_room`, first match by instance pk). `list`/`buy`/`sell` route to the vendor; `repair` routes to the repairer. Absent or dead service NPCs are out of business until they respawn: `There is no one here to trade with.` / `There is no one here who can repair.` If multiple qualify, the first found is used; checkpoint seeding never places two.

**`list`** — one line per active, non-exhausted `VendorEntry`: the entry's display name, the price in copper, and `(N left)` when `stock_limit` is finite. Exhausted entries are omitted. Vendor entries reference definitions, not instances, so the name is formatted directly from the definition (`_entry_display_name` static helper: `item_definition.name` plus ` Mk {mk_tier}` unless `suppress_mk_suffix`), **not** via `get_display_name_with_tier()`, which takes an instance.

**`buy <item>`** — case-insensitive prefix match against the vendor's active entries' definition names. Checks, in order: entry exists (`They don't sell that.`); stock (`Sold out.`); price ≤ character copper (a can't-afford message naming the price); carry capacity (the same check and message as `pickup`). On success `do_buy` runs atomically (`select_for_update` on both the entry and the character, re-checking stock and funds inside the transaction): copper deducted via `currency.subtract`, `sold_count` incremented, and an `ItemInstance` generated at the entry's `mk_tier` with **rarity always `common`**, owned by the character, unbound (soulbind happens on first equip, as with any item). Vendor buy prices are authored data (`VendorEntry.price`) — never formula-derived.

**`sell <item>`** — case-insensitive prefix match against the character's carried items; if every match is equipped: `You'll have to unequip it first.` Only unequipped items can be sold, but **soulbound status is irrelevant — soulbound items sell normally**. Selling is compensated disposal: `do_sell` credits `get_sale_price(item)` copper (one third of value, minimum 1) and **deletes the ItemInstance** — vendors never resell player items, and there is no buyback. Materials, gear, and consumables all sell through the same path; unidentified items sell at their stored (apparent) rarity.

**`repair <item>` / `repair` / `repair all`** — repair targets are the character's items (equipped or carried) with `takes_durability_loss=True` and durability below 100%. Repair is **paid per attempt; failure is harmless** — copper is spent, the item is unchanged, and the player may retry immediately. Success always restores `durability_current` to 100% (and clears `is_broken`). Items are never destroyed by repair. Cost and odds come from the Section 4.6 helpers: cost = `value × missing_durability_fraction × 50%` (floored, min 1); success chance = `20% + current_durability_fraction × 75%`. An attempt the character cannot afford is refused *without charging*, naming the cost.

- `repair <item>` — prefix match among the character's items; an undamaged or no-durability match gets `That doesn't need repair.`
- `repair` (bare) — one attempt on the most-damaged eligible item (lowest durability, pk tie-break — stable). Nothing damaged → `You have nothing to repair.` Repeated invocations walk the damage list: a failure re-targets the same item, a success moves on.
- `repair all` — one paid attempt per eligible item, most-damaged first, one report line each; stops (and says so) if copper runs out mid-batch; ends with a one-line summary (items repaired, attempts failed, copper spent).

All money movement goes through `apps.shyland.currency` (`add`/`subtract`) inside `transaction.atomic()` blocks with `select_for_update` on the Character row (`do_buy`, `do_sell`, `do_repair_attempt`). Prices and costs are displayed as plain copper integers (`60 copper`), not through the zone-aliased `display_for_zone` — vendors deal in copper.

#### Targetless `attack`/`kill` (v18 brief 4)

`cmd_attack` invoked **without** a target now auto-targets only while the player has aggro — an active `CombatSession` with at least one living NPC opponent. The target is the **first attacker**: the earliest-engaged living NPC in the session, resolved by `get_first_attacker_npc` as the lowest-pk row of the session's `npcs` M2M through table whose NPC is alive (through-row insertion order = engagement order). From there the command proceeds exactly as if the player had named that NPC. With no aggro, bare `attack` still refuses with `Attack what?`. Explicitly named targets behave exactly as before. Net effect: a player jumped in an aggro room can spam bare `attack`/`kill`, stays on the enemy that hit them first until it dies, then rolls to the next-earliest attacker.

#### Engagement messaging, ordinals, and broadcast exclusion (v19 brief 3)

v18 play-testing found `cmd_attack` printed a fresh `You attack the <npc>!` on every invocation even though combat is session-based with automatic per-round attacks — repeat commands against an already-engaged target are pure no-ops, so the ack lied. After resolving the target NPC (both the targetless-aggro path and the parsed-noun path, `npc = await self.parse_npc_noun(args, npcs_in_room)`), `cmd_attack` now fetches the character's active session (`get_active_combat_session`) and checks membership (`npc_in_session(session, npc)`, `session.npcs.filter(pk=npc.pk).exists()`):

- **Target already in the active session** → personal-only output `You're already fighting {display}.` (category `combat`). No broadcast, no `start_combat` call.
- **Otherwise (no session, or a genuinely new target)** → personal output `You move to attack {display}!`; room broadcast (excluding the actor via `broadcast_to_room_exclude`, the existing WS-side channel exclusion) `{character.name} moves to attack the {npc.definition.name}!` — witness lines always use the plain name, never the ordinal; then `start_combat` runs as before.

**`npc_display_name(npc, npcs_in_room)`** — module-level helper in `combat_utils.py` (moved there from `consumers.py` in v19 brief 6; imported into `consumers.py`, see below), alongside the module-level `ORDINALS = ['first', 'second', … 'tenth']` list. Returns `"the {name}"` when the NPC's `definition.name` is unique among `npcs_in_room`; `"the {ordinal} {name}"` when multiple NPCs share that name, where the ordinal is the NPC's **position** among same-name NPCs in `npcs_in_room`'s order (the same order `parse_npc_noun` indexes against for `N.noun` syntax) — **not** a stable per-instance number. Killing the first of two same-name NPCs makes the survivor "the {name}" again (or "the first …" if a third of that name is still present) on the next lookup, since the position is recomputed from the room's current live-NPC list every call. Beyond ten same-name NPCs in one room, the helper falls back to the bare name — treated as a seeding smell, not a display problem to solve.

**`room_message` broadcast exclusion.** The tick engine cannot exclude a channel-group member by channel name (it doesn't have one), so room broadcasts that need to skip a specific character now carry `exclude_pk` in the `group_send` payload (see Section 4.9). The consumer's `room_message` handler checks it after the existing WS-side `exclude` (channel name) check: `if exclude_pk is not None and exclude_pk == self.character_pk: return`, dropping the message silently for that one connection before anyone else's copy of the same `group_send` is affected. This is a second, independent exclusion mechanism alongside the pre-existing `broadcast_to_room_exclude`/`exclude` (channel name) used by consumer-originated broadcasts (`cmd_attack`, `cmd_flee`) — the engine has no channel name to key off, so it excludes by character pk instead.

#### Attack focus (v19 brief 6)

`cmd_attack` now drives `CombatSession.focus_npc` (Section 4.1) as well as the engagement messaging brief 3 built. After resolving the target NPC (unchanged — targetless-aggro path or `parse_npc_noun`), the same session/membership lookup from brief 3 now branches three ways instead of two, keyed off `session.focus_npc_id` rather than mere membership:

- **No session, or target not in the active session** — a genuine new engagement, unchanged from brief 3's ack and broadcast (`You move to attack {display}!` / `{character.name} moves to attack the {npc.definition.name}!`), then `start_combat([npc], first_attacker='character', focus_npc=npc)`. `start_combat` sets `session.focus_npc = npc` unconditionally when a `focus_npc` argument is passed, whether it created a brand-new session or added the NPC to one already in progress — **engagement always steals focus**, by ruling, covering both the fresh-engage case and the mid-fight "add a new target" case with one code path.
- **Target in session and `session.focus_npc_id == npc.pk`** — brief 3's already-fighting no-op, unchanged: personal-only `You're already fighting {display}.` (category `combat`), no broadcast, no `start_combat` call.
- **Target in session but not the current focus** — new case. `session.focus_npc` is set to the target and saved; personal-only message, category `combat`: `You change your attacks to focus on {display}.` No room broadcast — witnesses see the ensuing attacks land on the new target; the refocus decision itself is internal to the player.

The `flee` command's aggro-engagement call to `start_combat` (fleeing into a room with aggressive NPCs) passes no `focus_npc` argument, so it is unaffected by this brief — the resulting session's `focus_npc` stays `null` and the tick engine's first-live-NPC fallback (Section 4.9) applies, same as it always implicitly did for a freshly-created session.

#### Display formatting

`consumers.py` no longer formats Mk suffixes inline. Every name-plus-tier display (inventory equipment block, inventory item lines, examine header) goes through `get_display_name_with_tier()` from `item_utils.py` (see Section 4.6). Rarity labels are unchanged and still appear exactly where they did before, prepended by the call sites.

Carried over from v16 unchanged: character-less connections get a structured redirect; `disconnect()` guards against `self.character is None`; profile joins removed.

### 4.4 `effect_utils.py`

*(unchanged from v15)*

### 4.5 Combat utilities (`combat_utils.py`)

**`resolve_hit` is a contested d20 to-hit with an independent critical roll (rewritten v19 brief 5).** The v18 formula (`d100 + attacker_dex` against absolute bands anchored at the defender's DEX) was replaced because the d100's range dwarfed every stat in the game — in v18 play-testing a DEX-18 player vs. a DEX-5 bear produced criticals on ~84% of player swings and ~58% of bear swings, with miss and graze mathematically unreachable for the player. The new formula: `total = d20 + attacker_dex`; static `defense = TO_HIT_DEFENSE_BASE + target_dodge`. `total >= defense` is a success (hit or critical); on the gap `defense - total`, `1..GRAZE_WINDOW` short of defense is a graze, further short is a miss. Critical is then a **separate, independent roll** on any success: `crit_chance = clamp(CRIT_BASE + CRIT_PER_DEX_ADVANTAGE × (attacker_dex − target_dodge), CRIT_BASE, CRIT_CAP)`. Five module-level named constants (never inline literals, so post-play tuning is a one-line change) — `TO_HIT_DEFENSE_BASE = 10`, `GRAZE_WINDOW = 3`, `CRIT_BASE = 0.05`, `CRIT_PER_DEX_ADVANTAGE = 0.01`, `CRIT_CAP = 0.25` — are **tunable starting values by design ruling**, not final balance. Signature and return contract are unchanged (`resolve_hit(attacker_dex, target_dodge) → 'miss'|'graze'|'hit'|'critical'`); neither call site (`run_tick_engine.py`'s player-attack and NPC-attack rounds) changed. `calculate_damage` and its multipliers (graze 0.5×, hit 1.0×, critical 1.5×) are untouched. At equal DEX: ~55% hit-or-crit, 15% graze, 30% miss, crit ≈5% of successes. Large attacker advantage: always hits (deliberate — outleveled content is trivially hittable under infinite level scaling), crit bounded at 25% forever. Attacker at a disadvantage: crit stays at the 5% floor, never below.

**`get_unarmed_message` gained `attacker_name` and `fallback_slug` parameters (v19 brief 3).** New signature: `get_unarmed_message(attacker_pool, target_name, attacker_name=None, fallback_slug='default')`. Substitution is now literal `str.replace` — `'{target}'` → `target_name`, `'{attacker}'` → `attacker_name` when provided — **not** `.format(target=…)` (see the superseded design-principles line in Section 6); stray braces left in a template are harmless, matching the `TravelMessage` precedent. `fallback_slug` names the pool used when `attacker_pool` is `None` or has no messages: the player attack call site (unarmed player swings) leaves it at the default `'default'`; the NPC attack call site in the tick engine passes `attacker_name=npc.definition.name, fallback_slug='npc-default'` so an NPC's unarmed attack can never fall back to the player-perspective `default` pool (whose templates are second-person, `"You swing at {target}"` — narrating an NPC's hit in the player's own voice was the bug this brief fixes). If even the fallback pool is missing, the ultimate hardcoded fallback also branches on `attacker_name`: `f"The {attacker_name} strikes {target_name}."` for NPC callers, `f"You strike {target_name}."` for the player.

One change in v18 (brief 3): **`xp_for_kill(npc_instance, character)` now reduces XP for outleveled kills.** Base XP is unchanged (`int(mk_tier × 10 × scaling_factor)`) and is paid in full while the character is within the NPC's Mk level band — band top = `mk_tier × 10`. Beyond the band top the multiplier drops 20% per level over, floored at 10% of base, and the awarded amount is additionally floored at 1 XP (`max(1, …)` — matters for low-base NPCs where 10% truncates to 0). Outleveled content always pays something. Worked values for a Mk 1 NPC at `scaling_factor=1.0` (base 10): levels 1–10 → 10 XP; 11 → 8; 12 → 6; 13 → 4; 14 → 2; 15+ → 1. The product is rounded at the 9th decimal before truncation to correct binary-float error (0.20 × 3 → 0.6000…01) so results match the decimal formula. The signature already took both arguments, so no call sites changed. Everything else *(unchanged from v15)*.

`recalculate_bars(character)` gained a second call site in v16: the character creator calls it on the unsaved `Character` to compute starting bars from the level-1 stats before the first save (see Section 4.11).

**`npc_display_name` and `ORDINALS` relocated here from `consumers.py` (v19 brief 6).** Content and behavior unchanged (see Section 4.3 for the full description); the move makes the ordinal display helper importable from the tick engine (`management/commands/run_tick_engine.py`) without pulling in the whole `consumers.py` module (Channels/redis imports, WebSocket-only helpers), since the engine's focus-death shift announcement (Section 4.9) now needs the identical ordinal logic the consumer already used for engagement/refocus messages. `consumers.py` imports it back: `from .combat_utils import npc_display_name`.

### 4.6 Item generation and utilities (`item_utils.py`)

One new helper added in v18 (brief 1), directly below `get_display_name()`:

```python
def get_display_name_with_tier(item):
    """
    Display name plus Mk tier suffix, honoring suppress_mk_suffix.
    Unidentified items never show a tier.
    """
    name = get_display_name(item)
    if not item.is_identified:
        return name
    if item.definition.suppress_mk_suffix:
        return name
    return f"{name} Mk {item.mk_tier}"
```

This is the **single source of truth for name-plus-tier formatting**. No inline `Mk {item.mk_tier}` formatting of player-facing item names remains in `consumers.py`. (Model `__str__` methods and tick-engine log lines are admin/debug representations, not display names, and intentionally do not use it.)

**`generate_loot_from_table(loot_table, mk_tier)` was rewritten in v18 (brief 3)** for guaranteed-group loot. The roll now partitions the table's entries by `guaranteed_group`:

- **Ungrouped entries** (blank group): exactly the previous behavior — an independent `drop_chance` roll per entry.
- **Each distinct group**: exactly one entry is selected per roll via `random.choices` with each entry's `drop_chance` as its relative weight — one instance per group, every roll, unconditionally.

Every selected entry (grouped or not) then flows through the same tier clamp (`mk_tier` clamped to `[mk_tier_min, mk_tier_max]`), rarity roll from `rarity_weights`, and `generate_item_instance()` as before; the `create_corpse` caller is unchanged. **Rarity floors are seed data, not code**: "boss always drops Rare or better" is expressed by giving the entry a `rarity_weights` dict containing only the permitted rarities — there is no rarity-floor machinery.

**Valuation helpers (new in v18 brief 4)** — the single source of truth for item worth; no command computes value, price, cost, or chance inline:

```python
RARITY_VALUE_MULTIPLIERS = {
    'common': 1, 'uncommon': 2, 'rare': 4,
    'epic': 8, 'legendary': 16, 'artifact': 32,
}
```

- **`get_item_value(item)`** — full worth in copper: `base_value × mk_tier × rarity multiplier` (unknown rarity falls back to ×1).
- **`get_sale_price(item)`** — what a vendor pays: one third of value, integer floor, minimum 1 copper.
- **`get_repair_cost(item)`** — cost per repair attempt: `value × missing_durability_fraction × 50%`, integer floor, minimum 1 (`durability_current` is the 0–100 scale on `ItemInstance`).
- **`get_repair_success_chance(item)`** — `0.20 + current_durability_fraction × 0.75`: 20% at zero durability, ~95% near full.

Everything else in `item_utils.py` *(unchanged from v15)*.

### 4.7 Admin

| Model | Admin class | Notable changes in v16 |
|-------|-------------|------------------------|
| `Character` | `CharacterAdmin` | `name` added to the first fieldset (`user, name, origin, archetype, current_room, recall_room`) — required now that it is a real, non-nullable field |
| `Origin` | `OriginAdmin` | `attire_material` added to `list_display` |
| `Archetype` | `ArchetypeAdmin` | `attire_silhouette` added to `list_display` |

Neither `OriginAdmin` nor `ArchetypeAdmin` declares `fieldsets`, so the new attire fields appear in their add/change forms automatically. All other admin registrations unchanged from v15, except: one v18 (brief 1) change — `ItemDefinitionAdmin` *does* declare `fieldsets`, so `suppress_mk_suffix` was added to its Identification fieldset (alongside `mystery_name` / `mystery_description`); v18 (brief 2) changes — `ZoneGateAdmin` was removed with its model, and `TravelNodeAdmin` (list display: `travel_name`, `room`, `node_type` — nodes are builder-authorable data) and `TravelMessageAdmin` (list display: `category`, `text`) were registered; and v18 (brief 3) changes — `RoomSpawnAdmin` gained `requires_living_npc` (list display, raw-id, select-related), a standalone `LootTableEntryAdmin` was registered with `guaranteed_group` in its list display and filters (entries were previously editable only via the `LootTableAdmin` inline, which also gained the field), and `death_message` appears in the `NpcDefinitionAdmin` form automatically (no `fieldsets` declared). v18 (brief 4) changes: `ItemDefinitionAdmin` gained an Economy fieldset holding `base_value` (also in list display); `NpcDefinitionAdmin` gained `is_repairer` in list display and filters (the form picks it up automatically); `VendorEntryAdmin` gained `sold_count` in list display.

### 4.8 Seed data (`management/commands/seed_world.py`)

Changed in v19 (brief 3): **nine new unarmed message pools for NPC-perspective attack flavor**, seeded additively in `_seed_unarmed_pools` alongside the existing species pools (`get_or_create` by pool slug and message template — unlike the `default` pool's delete-and-recreate).

- **`npc-default`** — the NPC-perspective fallback pool (four third-person templates: `"The {attacker} strikes {target}"`, `"…lashes out at {target}"`, `"…slams into {target}"`, `"…tears at {target}"`). Used by any NPC whose `unarmed_message_pool` is unset or empty (e.g. unpooled Viridian Ridge creatures) — NPC attacks never fall back to the player-perspective `default` pool (see Section 4.5).
- **Eight species pools** (`sp-river-otter`, `sp-black-bear`, `sp-mountain-lion`, `sp-wild-boar`, `sp-plains-deer`, `sp-plains-rabbit`, `sp-prairie-dog`, `sp-buffalo`), four third-person templates each, for the eight Verdant Reach surface animals seeded in brief 5.
- **Wired to their `NpcDefinition.unarmed_message_pool` FKs** by changing the `pool_slug` tuple element (7th field) for those eight rows in `_seed_verdant_npcs`'s `npcs` list from `None` to the matching `sp-*` slug. The FK lookup lives in `content` (not `balance`) in `_upsert_npc_definitions`, so — per the existing content/balance `update_or_create` convention — the wiring is refreshed on every seed run, same as `name`/`description`/`is_aggressive`, never admin-tuning-protected the way `balance` fields are.
- Idempotent — verified by double-run (pool and message counts unchanged on the second run).

Changed in v18 (brief 6): **The Verdant Reach is complete** — the second and final content payload seeds The Viridian Ridge, the three mountain delves, and the Verdant Crown, bringing Z01 to **150 rooms across 10 areas**. Same conventions and idempotency guarantees as brief 5 (verified by double-run: second run creates nothing).

- **Four new areas** appended to `_seed_verdant_areas`: The Viridian Ridge, The Undercrag, Chitterdeep, Hollowcrown.
- **81 new rooms** seeded section by section (`_seed_ridge_rooms_leg1` 16, `_seed_ridge_rooms_leg2` 15, `_seed_ridge_rooms_leg3` 20, `_seed_undercrag_rooms` 9, `_seed_chitterdeep_rooms` 10, `_seed_hollowcrown_rooms` 11) through the existing `_vr_room` helper. Seed keys: `vr-c01` (Cragfoot), `vr-m01`–`m43` (ridge spine, offshoots, vistas, aggro grounds), `vr-st1/2` (Stonestep), `vr-hf1/2` (Highfold), `vr-ll1/2` (Lastlight), `vr-vc1` (The Verdant Crown), `vr-c5a`–`i` (Undercrag), `vr-c6a`–`j` (Chitterdeep), `vr-c7a`–`k` (Hollowcrown). **Coordinate ranges:** the Ridge climbs y 31→58 and z 4→12 on the spine (offshoots at x ±1–2); the Undercrag descends z 6→3 under the first shoulder (x 2, y 39–43); Chitterdeep falls z 8→5 then rises back to 7 for the throne (x 2–3, y 47–51); Hollowcrown climbs *up* inside the summit, z 11→14 (x 2–3, y 55–60). **`vr-f18` north is wired to `vr-c01`** and its pending `no_exit_north_msg` is cleared. Only Cragfoot and the Verdant Crown are `flag_safe` (Z01 now has four safe rooms); all 30 new delve rooms are `flag_indoors` (49 cave rooms zone-wide); `flag_dark` remains unused. All new edges live in the same `VR_EDGES_ONE_WAY` list.
- **Three ridge unarmed pools** (`ridge-spider`, `ridge-centipede`, `ridge-beetle`) — the vale templates with the species noun upsized to its elder variant (9 species pools total).
- **20 NPC definitions** (`_seed_ridge_npcs`; the brief-5 upsert loop is extracted to a shared `_upsert_npc_definitions` helper that now honors an `is_unique` extra): 4 passive surface creatures (mountain goat, mountain squirrel, brown bear [elite], mountain lion [elite]); **two aggressive variants** (prowling mountain lion, territorial brown bear — both elite, placed only in the four aggro offshoot rooms); 2 passive villagers (mountain villager, mountain hunter; copper 8–20, loot `ridge-gear`/`ridge-hunter-gear`); 2 checkpoint service NPCs at Cragfoot (**Old Brammel the Mender**, `is_repairer=True`; **Ridda the Trader**, copper 10–24); **the Verdant Sphere** (`the-verdant-sphere`, `is_unique=True`, stats 1 across the board — the green sphere in the Crown's obelisk, second of the Primordial Sphere's kind); 3 aggressive elder cave insects (elder cave spider/centipede/beetle, all elite, sf 7–9); 3 aggressive bosses (`combat_tier='boss'`, respawn 10, death messages): **the Undercrag Weaver** (VIT 500, sf 21, copper 150–400), **the Chittering King** (VIT 650, sf 27, copper 150–400), **the Crowned Devourer** (VIT 850, sf 30, copper 400–1000); and 3 aggressive minion definitions (the Weaver's brood, the King's skitterlings, the Devourer's drones — elite, stats as their elder-insect bases with reduced VIT, respawn 3). The Cragfoot spawn reuses brief 5's `verdant-shard` definition unchanged.
- **5 loot tables** (`_seed_ridge_loot_tables`): `ridge-gear` (Iron Mace, Iron Sword, Leather Shoulders, Wooden Shield at 0.10; common 85 / uncommon 15) and `ridge-hunter-gear` (those four + Battle Axe); and the three guaranteed-group boss tables — `weaver-loot` (group `weapon`: the six weapons, **rare 100**), `king-loot` (group `armor`: seven leather pieces + Wooden Shield, **rare 100**), `devourer-loot` (group `accessory`: all twelve copper accessories, **epic 100** — the game's first guaranteed Epic drop), each plus an ungrouped Insect Carapace at 0.5.
- **72 room spawns** (33 surface + 39 delve), all Mk 1. The three minion spawns gate on their boss via `requires_living_npc`.
- **5 vendor entries** for Ridda: Healing Draught 15, Iron Mace 80, Wooden Shield 70, Iron Sword 75, Leather Cap 40 (all Mk 1, unlimited stock).
- **Two travel nodes** appended to `_seed_travel_nodes`: **Cragfoot** (`vr-c01`, checkpoint) and **The Verdant Crown** (`vr-vc1`, **obelisk** — the Obelisk Network's second travel *source*, completing the Convergence↔Crown round trip). 5 nodes total.
- **Verification pass updated**: 150 rooms / 10 areas / 5 travel nodes; f18↔c01 wired with the pending message gone; exactly four safe Z01 rooms; 49 indoor cave rooms; no `flag_dark`; the 49-definition Verdant roster with its passive/aggressive split (23 aggressive); 6 bosses with death messages; 3 repairers; the Verdant Sphere unique with one spawn at the Crown; 129 Z01 spawns; 6 gated minion spawns; 12 loot tables with guaranteed-group counts and the Devourer's all-epic weights; 9 species pools; Ridda's 5 vendor rows.

Runtime verification performed at ship time (not part of the seed command): full topology walk both ways (spine, every offshoot/village/vista, all delve U/D pairs); aggro fires on entering the four offshoot grounds and all delve rooms but not for the passive spine lions; all three bosses killed end-to-end through the live tick engine (death message broadcast to the room, exactly one guaranteed drop at the correct rarity and category, copper in range, minions cleared-and-not-respawned while their boss is dead and back once he returns); Convergence↔Crown travel round trip including Cragfoot's destination-only refusal; `list`/`buy`/`repair` at Cragfoot; XP spot checks (level 10 vs sf 9 → 90, level 12 → 54, Devourer at-band → 300).

Changed in v18 (brief 5): part 1 of the world seed for **The Verdant Reach** (Z01), the first zone beyond The Convergence. All new steps follow the established conventions (coordinate-keyed `update_or_create` rooms via a registry of seed keys, two-pass exit wiring, content/balance `update_or_create` split for NPCs, `get_or_create` for spawn/loot/vendor/node rows) and the whole command remains idempotent — verified by double-run.

- **Zone & areas.** The Z01 zone row (`the-verdant-reach`, danger `beginner`) is created via `get_or_create` on its slug — contrary to the brief's assumption it did **not** already exist in the Infinity City seed, which referenced the zone only in prose. Six areas (`_seed_verdant_areas`, `get_or_create` by slugified name within the zone): Fernwater Vale, The Sagewind Flats, Spinner's Hollow, The Silken Cleft, The Whistling Sink, The Drone Pit.
- **69 rooms** seeded section by section (`_seed_verdant_rooms_vale` 30, `_seed_verdant_rooms_flats` 20, `_seed_verdant_rooms_caves` 19) through a new `_vr_room` helper (like `_room` but with a z coordinate and safe/indoors flags defaulting to unsafe/outdoors). Seed keys use the `vr-` prefix (`vr-v01`…`vr-v22`, `vr-rm1`–`3`, `vr-s1`–`5`, `vr-f01`–`f18`, `vr-w1`/`w2`, `vr-c1a`, `vr-c2a`–`d`, `vr-c3a`–`f`, `vr-c4a`–`h`). **Coordinate scheme:** zone-local, `vr-v01` (the Tree Arch) at (0,0,0), north +Y / east +X / up +Z; the ancient stair climbs z 1→4 and the Flats sit at z=4; the Whistling Sink and Drone Pit descend to z=3 (the Drone Pit's larder shaft to z=2); the vale caves stay at z=0. Only the two checkpoint rooms (`vr-v07` Fordwatch, `vr-f01` Stairhead) are `flag_safe`; all 19 cave rooms are `flag_indoors`; `flag_dark` is unused. Exits are declared once in the module-level `VR_EDGES_ONE_WAY` list and expanded to both directions by `vr_edges()`, folded into the existing `_wire_exits` pass. `vr-f18` (The Boulder Field) shipped with its north exit held back behind a pending message; brief 6 wired it to Cragfoot.
- **The Verdant gate opened.** Ring room R02 (The Green Gate) lost its sealed `no_exit_north_msg`; its description's beyond-the-arch sentences were replaced with the brief's open-gate sentence; R02 ↔ `vr-v01` is wired both ways through the same edge list.
- **Character relocation narrowed.** `_set_character_rooms` now excludes both seeded zones from its "move strays to the Heart" sweep — previously a re-seed would have teleported anyone standing in the Verdant Reach back to The Convergence.
- **Six unarmed message pools** (`vale-spider`, `vale-centipede`, `vale-beetle`, `flats-spider`, `flats-centipede`, `flats-beetle`), four messages each, `get_or_create` by pool slug and message template; the flats variants are the vale templates with the species noun upsized to its giant form. Unlike the Default pool (delete-and-recreate), these are purely additive.
- **29 NPC definitions** (`_seed_verdant_npcs`, content/balance split, all `genre_tag='fantasy'`, all Mk 1): 8 passive surface creatures (river otter, black bear, young mountain lion, wild boar [elite], plains deer, plains rabbit, prairie dog, buffalo [elite]; respawn 1, loot `animal-drops`, no copper); 4 passive villagers (Reedmere villager/fisher, Windhome villager/hunter; respawn 5, copper 2–8 / 4–12, loot `reedmere-gear`/`windhome-gear`); 4 checkpoint service NPCs (**Maro the Mender** and **Tavik the Mender** with `is_repairer=True`, **Essa the Trader** and **Sona the Trader** as the game's first vendors); **a Verdant Shard** (`verdant-shard`, stats 1 across the board, one instance at each checkpoint — the green counterpart of the Primordial Sphere); 6 aggressive cave insects (cave/giant-cave spider, centipede, beetle; respawn 1, loot `insect-drops`, species pools); 3 aggressive bosses (`combat_tier='boss'`, `is_unique=False`, respawn 10, copper 50–150, death messages): **the Silk Matron** (VIT 120, `matron-loot`), **the Whistler Below** (VIT 260, `whistler-loot`), **the Dronemother** (VIT 320, `dronemother-loot`); and 3 aggressive minion definitions (the Matron's brood, the Whistler's young, the Dronemother's swarm; respawn 3).
- **7 loot tables** (`_seed_verdant_loot_tables`, all entries Mk 1–1): `animal-drops` and `insect-drops` (one material each at 0.35, common); `reedmere-gear` and `windhome-gear` (four gear pieces each at 0.10–0.12, common 85 / uncommon 15); and the three boss tables using brief 3's guaranteed groups — `matron-loot` (group `weapon`: the six one-slot weapons, uncommon 100), `whistler-loot` (group `armor`: the seven leather pieces + Wooden Shield), `dronemother-loot` (group `accessory`: all twelve copper accessories), each plus an ungrouped Insect Carapace at 0.5.
- **57 room spawns** (`get_or_create` on the `(room, definition, mk_tier)` natural key), 30 surface + 27 cave. The three minion spawns set `requires_living_npc` to their boss — the first live use of brief 3's gate.
- **8 vendor entries**: Essa (Healing Draught 15, Combat Knife 40, Leather Boots 35, Leather Gloves 35), Sona (Healing Draught 15, Hunting Bow 90, Leather Vest 60, Leather Leggings 55); all Mk 1, unlimited stock.
- **Two checkpoint travel nodes** added to `_seed_travel_nodes`: `Fordwatch` (`vr-v07`) and `Stairhead` (`vr-f01`), both `node_type='checkpoint'` — the Obelisk Network's first destinations beyond the Heart.
- **Verification pass extended** with 18 Verdant checks: zone/area/room counts, every VR edge bidirectional in the DB (including the gate), the F18 pending exit + message, safe-room and indoor counts, the definition roster, the passive/aggressive split, boss tier + death messages, repairer flags, spawn counts, the gated minion spawns, loot-table entry and guaranteed-group counts, pool message counts, and vendor entry counts. (Brief 6 re-baselined all of these numbers; the current expectations are listed in the brief 6 section above.)

Changed in v18 (brief 4): two additions to `_seed_items`, plus two new verification checks.

- **Two material definitions** appended to the gear/consumable list (`get_or_create`, like the rest of it): **Animal Hide** (`animal-hide`, `base_value=6`) and **Insect Carapace** (`insect-carapace`, `base_value=8`) — `item_type='material'`, fantasy genre, no slots, no stats, no durability. Item count: 33 → 35.
- **`base_value` back-fill.** After the item loops, an authored value table is applied with `.filter(slug=...).update(base_value=...)` — forced on every run, since `get_or_create` never updates existing rows. Values: broadsword/battle-axe 100, pulse-pistol 90, hunting-bow 80, iron-mace 65, iron-sword 60, apprentice-staff/ballistic-jacket/wooden-shield 55, leather-vest 50, leather-leggings 45, leather-shoulders/leather-boots 40, combat-knife and the remaining leather pieces 35, all 12 copper accessories 30; then every `consumable` → 12 and every `bag` → 50 by item-type update; then any definition not covered → 25. Note the back-fill deliberately clobbers admin tuning (unlike the balance-data convention below) — `base_value` is authored in the seed, matching the copper-accessory precedent.
- The verification pass gained two checks: the two materials exist with `item_type='material'`, and **no `ItemDefinition` remains at the migration default `base_value=1`**.

Changed in v18 (brief 2): three new idempotent seed steps, run from `handle()` after `_seed_convergence_npcs`:

- **`_seed_primordial_sphere`** — the tenth Convergence NPC: **the Primordial Sphere** (`the-primordial-sphere`), the white sphere suspended in the Obelisk at the Heart of the Convergence, now examinable. The first of its kind — origin of the pattern every zone-end obelisk sphere will follow. Non-aggressive, unique, never wanders, `combat_tier='normal'`, no loot table, no currency drop. Unlike the other Convergence NPCs (whose placeholder stats use `base_vitality=999`), the brief pins its stats at 1 across the board (`base_vitality` and all six base stats = 1, `scaling_factor=1.0`). Follows the standard NPC convention: `update_or_create` by slug with content in `defaults` and balance in `create_defaults`, placed via a `RoomSpawn` (count 1) in the Heart. The Heart is a safe room, so the Sphere can never be attacked in practice.
- **`_seed_travel_nodes`** — registers the network's first node: `TravelNode(room=<Heart of the Convergence>, travel_name='The Convergence', node_type='obelisk')` via `get_or_create` on the room. The room is looked up by the seed's own room key (coordinate identity `(0,0,0)`), never by display-name matching.
- **`_seed_travel_messages`** — seeds the three global message pools with exactly 22 entries: **10 traveler, 6 departure-witness, 6 arrival-witness**. Idempotent via `get_or_create` on `(category, text)`.

The built-in verification pass was extended accordingly: 10 NPC definitions / 10 RoomSpawns (was 9/9), exactly one Sphere spawn at the Heart, exactly one `TravelNode` (The Convergence obelisk at the Heart), and the 10/6/6 message counts.

Changed in v18 (brief 1): `_seed_items` was expanded with the Mk 1 item kit for The Verdant Reach. Three mechanisms:

- **Legacy absorption.** Before any item is processed, the legacy generic `copper-ring` definition is renamed in place (`.filter(slug='copper-ring').update(...)`) to `copper-ring-of-wisdom` / "Copper Ring of Wisdom". The old dictionary was removed from the seed list, so the generic ring can never be recreated and the rename is safe to re-run on both fresh and existing databases.
- **Gear** (weapons, armor, shield) stays on `get_or_create(slug=...)` — created once, never overwritten, so admin-tuned balance survives re-seeding.
- **The 12 copper accessories** use `update_or_create(slug=...)` uniformly, so the absorbed legacy ring is normalized to its authored shape on existing databases and re-seeding stays idempotent.

**Full post-brief ItemDefinition inventory (33 rows):**

| Group | Definitions |
|-------|-------------|
| Leather armor set (6 new + adopted vest) | Leather Cap (HEAD), Leather Shoulders (SHOULDERS), Leather Gloves (HANDS), Leather Belt (WAIST), Leather Leggings (LEGS), Leather Boots (FEET); the pre-existing Leather Vest (CHEST) is adopted into the set unchanged |
| Shield (new) | Wooden Shield (armor-typed, OFF_HAND, one-handed) |
| Weapons (4 new) | Iron Mace (MAIN_HAND, 1H), Broadsword (MAIN_HAND, 2H), Battle Axe (MAIN_HAND, 2H), Hunting Bow (RANGED, **2H** — all bows are two-handed for now) |
| Copper accessories (11 new + 1 absorbed) | Copper Ring of Strength / Dexterity / Endurance / Intelligence / Wisdom / Perception (RING) and Copper Amulet of the same six stats (NECK). Copper Ring of Wisdom is the absorbed legacy `copper-ring`. All twelve: `suppress_mk_suffix=True`, scaling 2.0/0.8, no durability, primary = suffix stat at base 2.0 / factor 0.8, secondary pool = the two adjacent stats at 0.5/0.2 (str→dex+end, dex→str+per, end→str+wis, int→wis+dex, wis→int+end, per→dex+int) |
| Pre-existing, unchanged | Iron Sword, Combat Knife, Pulse Pistol, Apprentice Staff, Leather Vest, Ballistic Jacket, Satchel, Healing Draught, Focus Tonic, Repair Kit |

Net effect on an existing v17 database: 22 new rows plus the in-place rename (11 → 33). On a fresh database the full seed creates all 33 directly. No proper nouns in any new item name; no new technology weapons (the Pulse Pistol is untouched and receives no new associations). This brief seeds **no zone content** — no rooms, NPCs, or drop tables.

Changed in v17: the world-seed portion of the command was rewritten for the Infinity City map. `handle()` first deletes the placeholder content (the five Fracture Point plaza rooms by name, the `goblin-scout`/`training-dummy`/`fracture-wraith` NPC definitions, and the `the-fracture-point-plaza` area — the old `_seed_npcs` method that created them is gone), then builds The Convergence: the zone, 4 areas, 54 rooms keyed on `(zone, coord_x, coord_y, coord_z)` via `update_or_create`, exits wired in a second pass (every room's six exit FKs are assigned explicitly, absent ones to `NULL`, so re-runs fully normalize), 9 unique non-combat NPC definitions placed via `RoomSpawn`, and character relocation (characters with no `current_room`, or one outside The Convergence, move to Heart of the Convergence at (0,0,0); null `recall_room` is set the same way). The command ends with a built-in verification pass (room/area/NPC/spawn counts, ring-loop and path-connectivity walks, flags) that raises `CommandError` on any failure. The command is idempotent. One deliberate deviation from the v17 content brief: the brief assigned ring room R16 the same coordinates as the Basalt Way's last room; R16 sits at (1,−5,0) instead. NPC stats and drop/respawn numbers follow the balance-data convention below (create-only); NPC name, description, genre tag, and behavior flags are refreshed on every run.

Changed in v16: `_seed_origins` and `_seed_archetypes` now use **`update_or_create`** instead of `get_or_create`, keyed on `slug`. Re-running the seed command therefore applies content changes to already-existing rows instead of silently skipping them (their stdout lines now report `"created"`/`"updated"` accordingly). This mattered for v16 because all seven Origins and seven Archetypes already existed from prior seeding.

**Balance data is create-only.** The `defaults` dict (applied on every run) carries only content fields — `name`, `description`, and the attire phrase — while balance values (`Origin.acuity_baseline`/`acuity_band_low`/`acuity_band_high`, `Archetype.primary_stat_1`/`primary_stat_2`) go in `create_defaults` (Django 5's create-only bucket). Re-running `seed_world` on a live database refreshes descriptions but never reverts admin-tuned balance numbers. (The v18 copper accessories deliberately deviate: they are full `update_or_create` rows per the brief, so re-seeding normalizes them — including the absorbed legacy ring.)

Both methods seed real content:

- **Origins** — each of the seven (`highborn`, `feral`, `streetborn`, `irradiated`, `undying`, `machinekind`, `voidtouched`) has a non-empty `description` (flavor text tying the Origin's genre to its Acuity profile) and a non-empty `attire_material` phrase (e.g. Voidtouched: `'shifting, void-dark cloth that seems to drink the light'`). The `acuity_baseline` / `acuity_band_low` / `acuity_band_high` values are unchanged from v15.
- **Archetypes** — each of the seven (`blade`, `bulwark`, `shade`, `conduit`, `warden`, `gunner`, `machinist`) has a non-empty `description` (role summary referencing its two primary stats) and a non-empty `attire_silhouette` phrase (e.g. Machinist: `'a utility vest lined with tool loops'`). The `primary_stat_1` / `primary_stat_2` values are unchanged from v15.

All other seed methods (`_seed_unarmed_pools`, `_seed_effects`, zone/room/area creation) *(unchanged from v17)*.

### 4.9 Tick Engine (`management/commands/run_tick_engine.py`)

Two changes in v18 (brief 3), one in brief 5, three in v19 brief 2, two in v19 brief 3, the fall/dying/expiry rework in v19 brief 4, and the focus-driven targeting rework in v19 brief 6 below; everything else *(unchanged from v15)*.

**The fall sequence, run at both places a character's Vitality can hit zero (v19 brief 4).** `process_combat`'s NPC-attacks-character branch and `process_effects`'s `dot_vitality` component handler each run the identical sequence the instant `vitality_current <= 0`, before either function's usual per-hit messaging:

1. `vitality_current = 0`, `is_dying = True`, `dying_since = now`, saved.
2. Every active `EffectInstance` on the character, and its `component_instances`, deactivated with `removed_by='dying'` — the same bulk-update shape `execute_death` already used with `removed_by='death'`. This includes the very effect instance whose `dot_vitality` tick just caused the fall, if that's the site; a same-tick guard (`newly_dying`, a local set built while iterating `ticking`) skips any other not-yet-processed component belonging to a character who fell earlier in the same phase-1 loop, so a multi-component DoT can't tick a second component (and print a second message) on a character already falling this tick.
3. `CombatAction.objects.filter(character=character, is_processed=False).delete()` — the character's own queued/future attacks are gone. Combined with a new guard on auto-attack creation (`if not player_actions and npcs and not character.is_dying:` in `process_combat` — was unconditional), a dying character never gets a fresh attack queued in a later round either. **This is one-directional.** The pre-existing guard on the NPC-attacks-character branch (`if character.is_dying: continue`) already stopped incoming hits from mattering; this adds the other direction, so a character who falls mid-round cannot land a posthumous kill on the NPC that killed them (or one it's fighting alongside) even if their own attack action was already queued for later in the same round's `ordered_actions`. If the character's attack had already resolved *earlier* in the same round, that kill stands — the discard only reaches forward from the moment of falling.
4. Two `send_to_player` calls, in order: an `event='clear'` message with no text (see Section 4.3 for the client-side effect), then the personal fatal-blow line, `category='error'`, riding `event='dying'` (no separate send for the flag sync — Section 4.3's consumer handling is unchanged from brief 2). No hit line, kill line, or "Combat has ended." for this character is generated after this point while `is_dying` is true — the NPC-attacks-character branch's existing early guard and the new character-attacks-NPC guard together make "no combat output of any kind reaches the dying player" absolute, not just "no damage." *(Amendment 1 removed a room-title line, `category='room'`, that originally sat between the two — the room name is already shown in the client's persistent header chrome; the extra line was found redundant during brief 4 play-testing.)*
5. The third-person room announcement, `"{character.name} has fallen and is dying!"`, `category='combat'`, `exclude_pk=character.pk` — unchanged from brief 2/3, still using the same exclusion machinery brief 3 built.

The combat-branch version of this appends to the same `messages`/`room_messages` lists `execute_actions` already threads out to the per-round flush loop (the clear/title/fatal-blow lines are just three more tuples with a `None` category-and-`'clear'`-event, `'room'`-category, and `'error'`-category-plus-`'dying'`-event entry respectively); the effects-branch version calls `send_to_player`/`broadcast_to_room` directly, since `process_effects` is already an async method rather than a synchronous `@database_sync_to_async` closure.

**The dying lore ladder — `process_dying_ladder`, called once per tick after `process_effects`.** A module-level `DYING_LADDER` list of nine `(elapsed_seconds, line)` pairs (5, 10, 15, 20, 25, 26, 27, 28, 29 — dense in the final five seconds) — no numerals or time units appear in any line; the escalation itself carries the urgency. Bookkeeping is a single in-memory `Command.__init__`-initialized dict, `self._dying_ladder_sent: dict[character_pk, set[int]]`, living only in the running tick-engine process:

- Each tick, query `Character.objects.filter(is_dying=True)`. For each: `elapsed = int((now - dying_since).total_seconds())`. **First sight of a pk this process** (no dict entry yet) seeds its sent-set with every threshold `<= elapsed` already — this covers both an engine restart mid-window (the dict is empty again, but the DB's `dying_since` still says how far in the character actually is) and a character who just fell this same tick (`elapsed` is ~0, so the seed is the empty set and nothing is skipped). Every tick after that, any threshold `<= elapsed` not yet in the sent-set fires once and is added — a tick that runs late (engine hiccup, not a normal case) emits the line it missed rather than silently skipping it, and no line is ever sent twice.
- After the per-character loop, any pk in the bookkeeping dict that the current `is_dying=True` query no longer returned is dropped. This is the entire "stop the ladder" mechanism for both revival and death — neither path touches `self._dying_ladder_sent` directly; clearing `is_dying` (revival, `cmd_use`; death, `execute_death`) is sufficient, because the next tick's query simply won't include that pk anymore and the sweep removes its entry.

**Death declaration before the existing respawn flow (v19 brief 4).** The dying-expiry loop in `process_combat` (`get_expired_dying` → `execute_death` → respawn message) now opens each iteration with `await self.send_to_player(character.pk, "The darkness takes you.", 'error', None)`, sent before the unchanged `"You have died and awakened at …"` message/status/`event='respawn'` flow from brief 2. `execute_death` itself is untouched — penalties, recall-room respawn, and full-bar restoration are all unchanged; this brief only adds the lore line in front of them.

**`broadcast_to_room` gained an `exclude_pk` parameter (v19 brief 3).** `broadcast_to_room(self, room_id, text, category='room', exclude_pk=None)` — the `group_send` payload to `room_{room_id}` now always carries `'exclude_pk': exclude_pk`. The engine has no per-connection channel name to exclude by (unlike the consumer's own `broadcast_to_room_exclude`, which excludes `self.channel_name`), so this excludes by character pk instead; the consumer's `room_message` handler drops the message for the one connection whose `character_pk` matches (see Section 4.3). `room_messages` tuples threaded through `execute_actions` gained a fourth element, `exclude_pk`, dispatched as `await self.broadcast_to_room(room_id, text, category, exclude_pk=exclude_pk)`. Two broadcasts pass their subject's pk, since that character already received an equivalent personal line and would otherwise see it twice: the kill announcement (`"{character.name} has slain the {npc.definition.name}!"`, `exclude_pk=character.pk` — the killer already got `"You have slain …"`) and the fall announcement (`"{character.name} has fallen and is dying!"`, `exclude_pk=character.pk` — the faller already got the personal brink-of-death line). The NPC `death_message` broadcast is **not** excluded from anyone, including the killer — it is world flavor addressed to the whole room, unchanged from the v18 brief 3 design (below). The one other `broadcast_to_room` caller (corpse decay) passes no `exclude_pk` and is unaffected.

**NPC attacks use their own flavor pool, never the player's (v19 brief 3).** The NPC-attacks-character branch of `execute_actions` calls `get_unarmed_message(npc_pool, character.name, attacker_name=npc.definition.name, fallback_slug='npc-default')` (was: `get_unarmed_message(npc_pool, character.name)`, which silently fell back to the player-perspective `default` pool and printed second-person lines like `"You swing at Shy-Guy"` for a bear's own attack). See Section 4.5 for the full substitution-rule change and Section 4.8 for the new pools.

**Level-up status push (v19 brief 2).** The character-attack branch's level-up `while` loop (in `process_combat`, refills Vitality/Longevity via `recalculate_bars` on each level gained) previously appended only a text message per level. Immediately after the loop completes — not per iteration, so a multi-level kill still pushes one status — `statuses.append((character.pk, self._build_status(character)))` runs, placed inside the `if npc.vitality_current <= 0:` kill block so a levelling kill always pushes the refilled bars to the client even when the same round ends the fight. Before this, a level-up that also ended the fight left the header showing the pre-level bars until some later command or tick happened to push a fresh status.

**`send_to_player` gained an `event` parameter (v19 brief 2).** `send_to_player(character_pk, text, category, status, event=None)` — the group-send payload to `player_{character_pk}` now carries `'event': event` alongside the existing fields. All pre-existing call sites are unaffected by the default. Two values are sent:

- **`event='dying'`** — sent at both places in the file that set `character.is_dying = True`: the combat brink-of-death path in `process_combat`'s NPC-attack branch, and the DoT-kill path in `process_effects`'s `dot_vitality` component handling (the latter call was previously missing its required `status` argument entirely — a pre-existing bug that would raise on any DoT kill; fixed as part of adding the event, since the two changes touch the same call). The `messages` list threaded through `execute_actions` gained a fourth tuple element (`event`, default `None`) so the brink-of-death text carries `'dying'` through to its `send_to_player` call without a special-cased second send.
- **`event='respawn'`** — sent from the dying-expiry path once `execute_death` has moved the character to their recall room, alongside the existing death text and status payload (the payload dict is now named `status_payload` rather than being built inline, but is otherwise unchanged, including the deliberate `'area_name': None` — the recall room's area is not `select_related` here and fetching it in async context would crash).

Consumer-side handling of both events is in Section 4.3.

**Respawn-timer fix in `process_npc_respawn` (brief 5).** The creation gap is now computed against **live + dead** instance counts (`to_create = min(count − (live+dead), count×2 − (live+dead))`), matching the `RoomSpawn` docstring. A dead instance therefore holds its spawn slot until `clear_expired_dead` deletes it at `respawn_at`, and the replacement is created on the following tick. Before the fix the gap was computed against live instances only, so every kill was refilled one tick later (up to the 2× cap) — `respawn_minutes` never mattered in practice, a killed boss reappeared immediately, and the minion gate below never actually engaged. Found by brief 5's verification step "brood stops respawning while the Matron is dead", which was unpassable against the old arithmetic.

**Spawn gate in `process_npc_respawn` (brief 3).** For each active spawn, after `clear_expired_dead` runs and before any instances are created: if `spawn.requires_living_npc` is set and no live `NpcInstance` of that definition exists in the spawn's room (`gate_npc_is_alive`, one `exists()` query per gated spawn; ungated spawns query nothing), instance creation is skipped for that spawn this tick. Dead-row clearing still runs — it is bookkeeping. Net behavior: gated minions respawn on their own timer while their boss lives, stop refilling the moment it dies, and refill again on the tick after the boss respawns — the encounter resets as a unit. (A brief 3 note here previously described the count/cap arithmetic giving a `count=1` spawn a buffered instant replacement; that behavior was the bug fixed in brief 5 above.)

**Death broadcast in the combat block.** Where an NPC's death is processed (`vitality_current <= 0` → `is_alive = False`), immediately after the existing kill output and before any corpse/loot output: if `npc.definition.death_message` is non-blank it is appended once to the round's `room_messages` and broadcast to the NPC's room — every character present, including the killer (personal kill lines are flushed before room broadcasts, so the killer always sees the kill line first). Blank message = byte-identical pre-brief output.

**Focus-driven attack targeting (v19 brief 6).** A pure-Python helper, `resolve_focus_npc(session, npc_list)` (no DB access — reads the already-loaded `session.focus_npc_id` and an in-memory NPC list), replaces the old hardcoded `npcs[0]`: it returns `session.focus_npc` if that id is set and still present in `npc_list`, otherwise the first entry of `npc_list`. Two call sites now go through it:

- **Auto-attack creation** — where `process_combat` queues the character's action for the round (`create_auto_attack`, guarded by `not player_actions and npcs and not character.is_dying`, unchanged), the target passed is `resolve_focus_npc(session, npcs)` instead of `npcs[0]`.
- **`execute_actions`'s Acuity `is_focus` computation** — `focus_npc_pk` (previously `npcs[0].pk if npcs else None`, computed once at the top of the closure) is now `resolve_focus_npc(session, live_npcs).pk` at that same point. Because the player's auto-attack target and the round's `is_focus` reference now come from the identical resolution, `is_focus` is no longer a separate concept shadowing the real target — Acuity's single-target bonus always applies to whatever the character is actually attacking, by construction. `focus_npc_pk` is then a plain local variable, live-updated in place by the kill-block shift below (not re-resolved from `session` mid-round, since `session.focus_npc` itself is only written when a shift occurs).

**Focus-death shift and session-end clearing (v19 brief 6).** In the kill block (`npc.vitality_current <= 0`), immediately after the killed NPC is dropped from `live_npcs` and removed from `session.npcs`:

- **No live NPCs remain** — unchanged combat-end path, now also clears focus: `session.is_active = False; session.focus_npc = None`, saved together, then the existing `"Combat has ended."` message.
- **Other live NPCs remain, and the killed NPC was the round's focus** (`npc.pk == focus_npc_pk`) — `session.focus_npc` is set to `live_npcs[0]` (first in the existing live-NPC ordering) and saved; `focus_npc_pk` is updated in place so any later action in the same round sees the new focus immediately; and a personal message is appended, category `combat`: `You turn your attacks on {name}.`, where `{name}` is `npc_display_name(new_focus, live_npcs)` — the same ordinal helper the consumer uses (Section 4.3/4.5), so a shift onto the last same-name survivor correctly drops the ordinal (`"the black bear"`, not `"the first black bear"`). If the killed NPC was *not* the focus (an off-focus kill isn't possible today — there's no multi-target damage, so the character only ever damages its own focus — but the check exists for whenever that changes), no shift or message fires.

The dying path is untouched by this brief: a dying character's own attacks are discarded before action generation (Section 4.9's fall sequence, above), so a dying character never reaches either of these focus-resolution call sites.

### 4.10 HTTP routes (`urls.py`)

The app-level URL configuration (`apps/shyland/urls.py`, namespace `shyland`) as of v16:

| Path | View | URL name |
|------|------|----------|
| `/shyland/play/` | `GameView` | `shyland:game` |
| `/shyland/create/` | `CharacterCreateView` | `shyland:create_character` |
| `/shyland/create/check-name/` | `CheckNameView` | `shyland:check_name` |
| `/shyland/` | `RedirectView` → `/shyland/play/` (non-permanent) | — |

All views are gated by `ShylandAccessMixin` (login required + `players.shyland` group or superuser).

### 4.11 Character Creation Flow (`views.py`, `forms.py`, `templates/shyland/character_create.html`)

New in v16. One character per account was already enforced at the schema level (`Character.user` is a `OneToOneField`); the creation flow now also enforces it at the view layer.

**Gating (`GameView.get`)** — if the authenticated user has no `Character`, `/shyland/play/` redirects to `shyland:create_character` instead of rendering the game terminal. A player without a character can do nothing in Shyland except use the creator or follow its "Back to front page" link to the site root (`{% url 'home' %}`).

**`CharacterCreateView`** (`GET`/`POST` at `/shyland/create/`) — both handlers first check for an existing `Character` and redirect to `shyland:game` if one exists (visiting the creator with a character never shows the form). The form has exactly three fields: Origin, Archetype, Name. No portrait selection exists, by design.

**Default name** — `_default_character_name(user)` returns `user.profile.gamer_tag or user.username`, matching the fallback order of the removed `Character.name` property, **truncated to 20 characters** so a long username can never pre-fill a value that fails validation.

**`CharacterCreationForm`** (`forms.py`) — `origin`/`archetype` are `ModelChoiceField`s with no empty label; `name` is a max-20 CharField. `clean_name` is the single source of truth for name validation, used by both the AJAX check and the final POST:

1. strip; reject blank
2. reject > 20 characters
3. reject if `Character.objects.filter(name__iexact=name).exists()` (advisory pre-check for the friendly error; the DB constraint is the authoritative gate)
4. **only if the submitted name differs from the user's set gamer tag** (`vetted_name`, passed in by the views): reject if `better_profanity.profanity.contains_profanity(name)`. The exemption covers only the gamer tag — the `username` fallback default has no upstream vetting and is always profanity-checked.

**`CheckNameView`** (`GET /shyland/create/check-name/?name=...`) — real-time availability endpoint. Instantiates `CharacterCreationForm` with only the name populated, runs validation, and returns `{"available": bool, "error": str|null}` from the name field's errors alone. The client-side check is advisory; the POST re-validates authoritatively.

**Creation (`CharacterCreateView.post`)** — on a valid form:

- **Spawn point** — `Room.objects.filter(zone__slug='the-convergence', coord_x=0, coord_y=0, coord_z=0).first()`. The lookup is by zone slug + coordinates, **never by room name** — the coordinate convention is stable across content rebuilds (as of v17 the room seeded there is "Heart of the Convergence"; before the Infinity City seed it was the placeholder "The Fracture Point"). If no room matches, the view fails loudly with a non-field form error ("Spawn point is not configured. Contact an admin.") rather than picking a different room. Both `current_room` and `recall_room` are set to the spawn room.
- **Starting stats** — flat baseline of 8 on all six stats, with the Archetype's `primary_stat_1` and `primary_stat_2` raised to 18. No Origin-based stat modifiers.
- **Acuity** — `acuity_current`, `acuity_baseline`, `acuity_band_low`, `acuity_band_high` are copied from the chosen Origin (overriding the model defaults of 1.0/1.0/0.8/1.2).
- **Bars** — `recalculate_bars(character)` is called on the unsaved instance so `vitality_max/current` and `longevity_max/current` are computed from the level-1 stats above, not left at the model's raw 100/100 defaults.
- **Race safety** — `character.save()` runs inside `transaction.atomic()` with `IntegrityError` handling: concurrent same-name submits (both passing the form's advisory `exists()` check) re-render the form with "That name is already taken.", and a double-submit that trips the `user` OneToOne constraint redirects to the game. No creation path can 500 on a constraint violation.
- On save, the player is redirected to `shyland:game` and drops into the terminal at the spawn room.

**Starting attire** — generated flavor text only: the Archetype's `attire_silhouette` phrase combined with the Origin's `attire_material` phrase (e.g. Warden + Undying → "simple, unadorned vestments" of "black lace and grave-worn cloth"). No `ItemDefinition`/`ItemInstance` is created and no equipment slot is occupied. The phrases live on the two model fields; no code path renders the combined text yet (see Section 7).

**Template** (`character_create.html`) — extends the shared `base.html`, continuing the dark monospace terminal aesthetic of `game.html`. Native `<select>`/`<label>` elements (accessible without custom ARIA work), the chosen Origin's and Archetype's `description` shown beneath each select via a small vanilla-JS show-on-select, and a debounced (~400 ms) `fetch` to `shyland:check_name` that writes availability feedback into an inline `aria-live` status area under the Name field. Responses are sequence-guarded: stale in-flight checks are invalidated both by newer input and by clearing the field. `{% csrf_token %}` is the first element inside the form. All fields remain editable until submit.

**No-character WebSocket handling** — the consumer's character-less connect path sends `{"type": "redirect", "url": "/shyland/create/"}` before closing, and `game.html` navigates on that message type, so the HTTP gate and the WS gate route to the same place (see Section 4.3).

**Dependency** — `better-profanity>=0.7` added to `django/requirements.txt` (image rebuild required).

---

## 5. Data Flow Diagrams

*(unchanged from v15)*

---

## 6. Key Design Decisions

These are settled. Do not revisit without deliberate consideration.

**`EffectDefinition` is a pure container.** All behavior lives in `EffectComponent` children. Allows multi-component effects.

**Mk tier scaling: `magnitude = magnitude_base + (magnitude_scaling × mk_tier)`; `duration = duration_base + (duration_scaling × mk_tier)`.** Deterministic — no random ranges.

**Instantaneous components: `duration_base=0`, `duration_scaling=0`.** No `EffectComponentInstance` row created. Parent `EffectInstance` closed immediately after application.

**Reapplication: same or higher Mk tier resets; lower Mk tier ignored silently.** Prevents downgrading active effects.

**Expiry messages: one per parent if all components expire together; one per component if staggered.** Balances feedback against message spam.

**`make reset` target** (renamed from `db-reset`). Drops all volumes, rebuilds, starts with `--wait`, migrates, reseeds. Used for breaking model changes.

**Single `copper` BigIntegerField for all currency.** All math through `currency.py`.

**`Character.name` is a real field, not derived from `user.profile.gamer_tag` at read time.** ⚠️ This **explicitly reverses** the decision recorded in v14/v15 ("Character name from `user.profile.gamer_tag`. Always `select_related('user__profile')`."). As of v16, the gamer tag is only the default offered in the character creator; once created, `Character.name` is authoritative (max 20 chars) and independent of the profile. The `user__profile` joins that served the old property have been removed, and CLAUDE.md's profile-name rule was amended with the Shyland exception in the same change.

**Name uniqueness is case-insensitive and lives in the database.** `UniqueConstraint(Lower('name'))` on `Character` is the authoritative gate for every write path (creator, admin, shell); the form's `name__iexact` `exists()` check is only an advisory pre-check for friendlier real-time feedback, and the creation view catches `IntegrityError` from the race the pre-check cannot close. Never rely on a form-level uniqueness check alone.

**One character per account.** Enforced at the schema level by `Character.user` being a `OneToOneField` (true since v14); as of v16 the creation flow also enforces it at the view layer — both the creator's GET and POST redirect to the game if a character already exists, rather than relying on the DB constraint to fail loudly.

**Spawn-point lookups use zone slug + coordinates, never room name.** The creator finds the spawn room via `zone__slug='the-convergence', coord_x=0, coord_y=0, coord_z=0`. Room names are content, subject to rebuild; coordinates are convention. Future briefs should reuse this pattern instead of name-based room lookups. If the lookup fails, fail loudly — never silently substitute a different room.

**Tier materials suppress the Mk display suffix (v18).** Items named with a tier material (copper — later silver/gold/platinum) never display "Mk N"; the material name conveys the tier. Display-only via `ItemDefinition.suppress_mk_suffix` and `get_display_name_with_tier()` — `mk_tier`, scaling, and rarity machinery are unchanged. Flavor materials (iron, wood, leather) do not suppress.

**The equip exchange rule (v18).** Equipping counts the equipped items that must come off: zero → equip into a free valid slot; exactly one, unambiguously → auto-swap in a single command with an exchange message (never silent); two or more, or one but ambiguous → refuse, naming the items. A two-handed item claims both hands regardless of which slot it sits in (a two-handed bow in RANGED conflicts with MAIN_HAND/OFF_HAND and with other two-handed items); all bows are two-handed for now. Auto-swap defers to the existing unequip constraints (curses, bag carry limit) — no partial swaps.

**Items soulbound on equip.** Permanently soulbound the moment an item is equipped.

**Item identification is per-character knowledge.** Dropping resets `is_identified=False`.

**Room Groups as the broadcast primitive.** Every player in room X is in channel group `room_{X.id}`.

**Personal player groups for direct notification.** Each connected player joins `player_{character_pk}` on connect.

**Server is the authority; client is a dumb terminal.**

**Status payloads are always built from fresh DB reads, and every engine-side mutation of player-visible state pushes an update to the client (v19 brief 2).** The complement of the rule above: authority means nothing if the client is never told what changed. State mutations happen in two processes — the consumer (synchronous with a player's own command) and the tick engine (asynchronous, driven by combat rounds and passive ticks) — and nothing else keeps them in sync. Adopted after v18 play-testing surfaced three bugs that all traced back to a display built from a stale in-process cache instead of the current row, or an engine-side mutation that mutated the DB but never told the client: stale status payloads on `look`/`move`/`travel`/login, a level-up that healed the character without refreshing the header, and a death respawn that moved the character server-side while the client stayed on the old room and the old broadcast group.

**Redis presence for `who` and room description filtering (rewritten v19 brief 1).** One key per character, key name and cadence unchanged: `shyland:online:{character_pk}`, 90s TTL, 60s heartbeat interval. The key's **value** is now a JSON object carrying a per-connection ownership token — `{"name": <character.name>, "token": <uuid4 hex, generated fresh per WebSocket connection>}` — instead of a bare name string, so a stale session can never delete a newer session's key (the v18 race: a browser reconnect fires the old socket's `disconnect` *after* the new socket's `connect`, and a plain `DEL` on the shared key made the character permanently invisible to `who` and room descriptions for the rest of the session).

- **Connect** — plain `SET ... EX 90`, unconditional. The newest connection always takes ownership.
- **Heartbeat** — a guarded Lua script run via `EVAL`: if the key is missing, `SET` this session's value with `EX 90` (self-heals after a Redis restart or a lost key, no reconnect required); if the key holds this session's exact value, `EXPIRE 90`; if it holds a different value (another session now owns the character), do nothing.
- **Disconnect** — a guarded Lua script run via `EVAL`: delete the key only if it still holds this session's exact value; otherwise do nothing. This is what closes the race — the old session's disconnect can no longer clobber a newer session's key.
- Both scripts compare the **exact value string** the connect handler wrote (`ARGV[1]`), not a parsed/partial match.
- **Readers tolerate legacy values.** `cmd_who` and `send_room_description`'s `online_names` filter both go through the module-level `parse_presence_name(raw)` helper, which JSON-decodes the value and returns `["name"]`, falling back to treating the raw string as a bare name if JSON parsing fails — tolerating keys written by pre-brief code that can survive up to 90 seconds across a deploy.

**`@database_sync_to_async` pattern throughout.** Never call ORM methods in async context.

**Acuity as a float damage modifier (0.1–1.9).** 1.0 = neutral.

**Tick-driven combat with queued actions.** `CombatSession` owns session metadata; `CombatAction` owns per-round actions.

**The player's attack target is player-controlled focus; focus changes are always announced, never silent (v19 brief 6).** `CombatSession.focus_npc` is the single field behind both the auto-attack target and the Acuity single-target bonus. Every way focus can change tells the player why: engaging or refocusing prints a `cmd_attack` message, an automatic shift after a focused kill prints `"You turn your attacks on {name}."` No focus change is ever silent. Multi-target damage (cleave, AoE) remains deliberately unbuilt — see Section 7.

**Dying state as a 30-second grace window.** All commands except `use` blocked.

**Dying interrupts combat in both directions — no posthumous death blows, no combat output to the dying (v19 brief 4).** The pre-existing incoming-attack guard (hits stop landing on a dying character) is only half the rule. A character's own queued or future attacks are discarded from the instant they fall, so a kill that would have resolved a moment later never does — and from that same instant, nothing generated by combat processing (hit lines, kill lines, "Combat has ended.") is sent to the dying player. The clear/title/fatal-blow sequence and the lore ladder are the *only* things a dying player sees; everyone else in the room keeps seeing normal combat and room broadcasts.

**Revival restores exactly what the potion heals (v19 brief 4).** No bonus, no forced full heal — a character revived by `use`-ing a vitality-restoring item rises with whatever Vitality that application produced, capped at `vitality_max` like any other heal. A strong enough item can legitimately bring a character back at full; a weak one brings them back at a sliver, and combat resumes against them immediately if the fight isn't over.

**Flee with cooldown and directional preference.** DEX + d20 vs average NPC PER.

**Criticals are an independent roll on successful hits — never a band of the to-hit roll (v19 brief 5).** Outleveled always-hit is deliberate; the crit cap bounds the multiplier at any stat spread.

**XP threshold formula: `level² × 100`.** `xp_for_next_level(level)` in `combat_utils.py`.

**Stat points on level-up.** `STAT_POINTS_PER_LEVEL = 5`. Never expire.

**Bar recalculation on stat change.** `vitality_max = (END×10)+(STR×3)+(level×5)`. `longevity_max = (END×8)+(WIS×5)+(level×5)`.

**`make build` required after every code change.** Source is baked into the Docker image at build time.

**`make makemigrations` auto-syncs migration files.** The Makefile copies generated files back from the container.

**Boolean commands always require an explicit value.** `brief on` / `brief off`, not bare `brief`. This rule applies to all future boolean-setting commands.

**`brief_description` is required on all rooms.** Non-null, non-blank. No fallback path.

**`look` always shows the long description.** Bypasses `brief_mode` entirely.

**`Origin` and `Archetype` are full models.** Both were promoted from CharField choices in v13b. `Origin` owns the Acuity baseline and band bounds (copied onto the `Character` at creation). `Archetype` owns primary stats and the unarmed message pool FK.

**Unarmed combat is explicit, not a fallback.** No weapon equipped means no weapon damage component — the formula is unchanged. Flavor messaging comes from the attacker's `UnarmedMessagePool`, falling back to the default pool.

**`UnarmedMessage.template` uses literal `str.replace`, not Python `.format` (revised v19 brief 3).** `'{target}'` and `'{attacker}'` (when an attacker name is given) are substituted via `.replace`, not `.format(target=name)` — the originally established pattern. `.replace` tolerates stray `{`/`}` characters in authored prose without raising, matching the `TravelMessage` precedent; this is now the pattern for all configurable message templates going forward.

**Passive regen is silent and gate-only.** No combat session + not dying = regen fires. No delay, no Origin exceptions, no player notification. Formula: `ceil((max - current) / ticks_to_full)`. Minimum effective heal of 1 per tick prevents stall. Both bars covered; Longevity recovers 30× slower than Vitality.

**`RoomSpawn` is the source of truth for NPC population.** The tick engine populates rooms from `RoomSpawn` config, not from dead `NpcInstance` state. Dead instances persist until `respawn_at` passes; `clear_expired_dead` deletes them at that point, allowing the fill logic to create replacements. Total instances (live + dead) per spawn slot are capped at `count × 2` to prevent unbounded accumulation.

**`VendorEntry` price is always explicit copper.** No auto-calculation formula. Every row requires a price value. Since brief 4 this asymmetry is deliberate and load-bearing: the **buy side is authored data** (`VendorEntry.price`, Common rarity, entry's Mk tier), while the **sell side is formula-derived** (`get_sale_price` — one third of `get_item_value`, which is the only place `base_value` enters play). Selling deletes the instance; vendors never resell player items, so the two sides never meet.

**The Obelisk Network replaces `ZoneGate` (v18 brief 2).** Fast travel is node-based, not edge-based: `TravelNode` rows mark rooms as obelisks (source + destination) or checkpoints (destination only), and any revealed node is reachable from any obelisk — the network is global, with no zone scoping and no per-gate rows. Revelation is per-character, permanent, and derived entirely from `RoomVisit` (no new per-character table; no sharing between characters). Travel is free — no currency, no resource, no cooldown. The obelisk speaks no words: all travel text comes from the randomly-selected `TravelMessage` pools. Safe rooms are a seeding concern, not travel logic — the command performs no combat checks.

**Per-direction blocked exit messages are optional on `Room`.** Fields `no_exit_{direction}_msg` default to `''`. When non-empty, the custom message overrides the hardcoded default in `_NO_EXIT_DEFAULTS` in `consumers.py`. Direction aliases are resolved to canonical before the field lookup.

**Profanity filtering skips only a kept gamer tag, via `better-profanity`.** A name exactly equal to the user's set gamer tag skips the profanity check (the tag is treated as vetted upstream); everything else — overrides *and* the `username` fallback default, which has no upstream vetting — is checked with the `better-profanity` library, never a hand-rolled wordlist. Uniqueness is always checked, default or not, both in real time (AJAX) and authoritatively at the DB constraint on submit.

---

## 7. What Is Not Yet Built

Future sessions should check this list before assuming a system exists.

- Vendor and repairer NPCs in The Convergence (briefs 5–6 shipped the first reachable services — Essa/Sona/Ridda vend and Maro/Tavik/Old Brammel repair at the Verdant Reach checkpoints — but no Convergence NPC has `VendorEntry` rows or `is_repairer` set)
- Vendor restock (`VendorEntry.sold_count` exhaustion is permanent until an admin intervenes; moot for now — all three live vendors have unlimited stock)
- Obelisk Network nodes beyond Z01 (the network now has two sources — The Convergence and The Verdant Crown — plus three checkpoints; every future zone adds its own)
- Per-combat-tier behavior differences (`combat_tier` field exists; no differentiated AI yet)
- Custom blocked exit messages for the `flee` path (flee uses a different room-exit lookup; `no_exit_*_msg` fields only apply to `cmd_move`)
- Per-archetype unarmed message pools (all archetypes currently fall back to the default pool)
- Per-NPC unarmed message pools for Convergence NPCs (the Verdant Reach cave insects, bosses, and minions carry the nine species pools; all other NPCs fall back to the default pool)
- Rendering of starting-attire flavor text (`Origin.attire_material` / `Archetype.attire_silhouette` are seeded; no command or view composes/displays the combined phrase yet)
- Item identification trigger — NPC sage, Warden ability, identification scrolls
- Durability degradation on combat use (model field and death-penalty logic exist; per-hit degradation deferred)
- `durability_restore` consumable effect (placeholder response implemented; the vendor `repair` command shipped in brief 4, but the self-service consumable path remains unbuilt)
- Skill point system — distinct from stat points; abilities/talents unlocked by spending skill points (not yet designed)
- NPC AI — wandering, dialogue, patrol (is_aggressive aggro on room entry is implemented)
- Party system (M2M relationship on `CombatSession` is in place; multi-character combat not yet wired)
- Multi-target damage — cleave, AoE, or any attack that hits more than the character's current `focus_npc` in one round (deliberately deferred by v19 brief 6's design ruling; the player currently damages exactly one NPC per round, whichever is focused)
- Guild system
- Quest system
- Dungeon instancing
- PvP flagging, entry confirmation, and bounty system
- The Wastelands (`is_scaled=True`) level-scaling logic
- XP death penalty floor logic — level < `XP_PENALTY_MIN_LEVEL` (10) currently has no XP penalty
- Revival mechanic — another player using a revival item on a dying character
- `examine` dialogue integration — NPC examine shows description only; no dialogue tree
- Super user in-game item gifting flow
- Minimap and fog-of-war rendering in client (`RoomVisit` records exist but are not rendered)
- Admin in-game teleport commands
- All chat channels except `say` and `who`: `yell`, `tell`, `party`, `guild`, `zone`, `general`, `emote`
- All zones beyond Z01 (The Verdant Reach is complete as of brief 6)
- Monitoring container — tracks health of all containers

---

## 8. Known Issues / Flags for Future Sessions

**Side panel is a stub.** `game.html` shows "Session 1 — world coming soon." in the side panel.

**`create_corpse()` is synchronous.** Always call it from within a `@database_sync_to_async` wrapper.

**No room description sent after entering combat.** When a player moves into a room with aggressive NPCs, the room description is not sent.

**Epic accessories roll 2 secondary stats — resolved at v18 closeout as correct-as-built.** The brief 6 verification expected the Devourer's guaranteed Epic accessory to roll 3 secondaries, but the brief 1 copper accessories were authored with **2-entry** `secondary_stat_pool`s (primary stat + two themed secondaries), and `generate_item_instance` draws without replacement capped at pool size. GDD v18.0 (RC17 ruling) blessed **pool-capped semantics**: secondary slot count is `min(rarity's slots, pool size)` — Legendary's "all in pool" was already this principle at the ceiling. No data change; an Epic copper accessory correctly rolls its full pool of 2 (3 stat lines total with the primary). Kept here as history since the code behavior is easy to misread as a bug.

**`tests.py` and `tests/` coexist in `apps/shyland/`.** The stale default `tests.py` stub shadows nothing at runtime, but `manage.py test apps.shyland` crashes during unittest discovery because of the module/package name collision. Run the test modules explicitly (`manage.py test apps.shyland.tests.test_currency apps.shyland.tests.test_area`) until the stub is removed. Pre-existing; not introduced by v18.
