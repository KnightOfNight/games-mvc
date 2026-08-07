# Shyland V24.13 Brief 1 — NPC HP Mk Scaling (#104)

- **Release:** Version 24.13 (milestone `Version 24.13`)
- **Founding ticket:** #104 — NPC HP must scale with level/Mk tier before any Mk 2 spawn is authored
- **Branch:** `version_24_13`
- **Design authority:** ruling recorded on #104 (2026-08-07, V24.13 design session, operator-confirmed); GDD §5 updated on this branch with `(v24.13, pending implementation)` markers
- **Phase:** opens Phase 3 (Mk 2 balance) of the V24 series plan (#139)

---

## 1. Context

NPC contest stats already band-lift: `combat_utils.npc_level()` returns `scaling_factor + 10 × (mk_tier − 1)`, and `get_npc_stats()` scales DEX/STR/PER/INT from it. HP does not: the single `NpcInstance` creation site — the tick engine's respawn/refill sweep, `run_tick_engine.py` (~line 833, `NpcInstance.objects.create(...)`) — sets `vitality_current = vitality_max = base_vitality`, flat, ignoring `mk_tier`. The first Mk 2 spawn authored would carry level-12+ contest stats with Mk 1 HP — an instant trivialization.

## 2. The ruled design (do not deviate)

1. **Doctrine:** at-level time-to-kill is band-invariant. `base_vitality` remains the authored *within-band* (Mk 1) value — species identity and the #101 boss-ladder tuning are untouched.
2. **Formula:** at spawn, `vitality_max = base_vitality × (1 + 0.75 × (mk_tier − 1))`, **rounded half-up**.
3. **Rounding law:** half-up means `int(x + 0.5)`. Do **not** use Python's built-in `round()` — banker's rounding sends `.5` cases to even (`round(262.5) == 262`), the exact parity trap recorded on #105. Silk Matron (150) at Mk 2 must be **263**, not 262.
4. **Uniform across all combat tiers** — normals, elites, bosses alike. The lift is per-band and linear; it is deliberately *not* exponential.
5. **Mk 1 multiplies by exactly 1** — zero change to any shipped spawn. This brief must not alter any live Mk 1 number.
6. The lift is computed **once, at instance creation** and persisted to `vitality_max`/`vitality_current` — no read-time scaling anywhere.

## 3. Implementation

### 3.0 Opening act — version constant (standing requirement, first brief of the release)

Bump `SHYLAND_VERSION` to `"24.13-DEV"` in its own commit, moving the pin-test assertion in the same commit. Then run the version-start `make deploy-dev` from the worktree.

### 3.1 The helper — `django/src/apps/shyland/combat_utils.py`

Add, adjacent to `npc_level()` (constant with the other module-level tuning constants):

```python
NPC_HP_BAND_LIFT = 0.75   # per Mk band above 1; linear, tracks player at-level damage growth (#104)


def npc_max_vitality(npc_definition, mk_tier):
    """Spawn-time HP for an NpcInstance: the authored within-band value
    lifted linearly per Mk band (#104). Rounded half-up — banker's
    rounding would drop .5 cases to even (262.5 -> 262; cf. #105)."""
    lifted = npc_definition.base_vitality * (1 + NPC_HP_BAND_LIFT * (mk_tier - 1))
    return int(lifted + 0.5)
```

Exact names are binding: `NPC_HP_BAND_LIFT`, `npc_max_vitality(npc_definition, mk_tier)`.

### 3.2 The spawn site — `django/src/apps/shyland/management/commands/run_tick_engine.py`

In the respawn/refill sweep's `NpcInstance.objects.create(...)` call (~line 833), replace both flat assignments:

```python
hp = npc_max_vitality(spawn.npc_definition, spawn.mk_tier)
NpcInstance.objects.create(
    ...
    vitality_current=hp,
    vitality_max=hp,
    ...
)
```

Import `npc_max_vitality` alongside the tick engine's existing `combat_utils` imports. This is the **only** creation site in the codebase (verified 2026-08-07); if implementation finds another, stop and record it as a deviation.

### 3.3 Explicitly out of scope / unchanged

- **No model changes → no migration.** `NpcInstance.vitality_max`/`vitality_current` already exist.
- **No seed data changes, no reseed.** `base_vitality` values stay authored as-is. Expected deletions: **0** (no seed run at all). No PENDING DEPLOY-TIME ACTIONS block.
- `release_session_npcs()` (reset to `vitality_max`), healing clamps, and the health-description bands all read instance fields and need no change.
- `SHYLAND_VERSION` is bumped by §3.0 only; the closeout stamps the release.

## 4. Tests — `django/src/apps/shyland/tests/`

New test module (e.g. `test_npc_hp_scaling.py`) following the existing tests-package conventions:

1. **Helper unit cases** (table-driven; expected values are binding):

   | base_vitality | mk_tier | expected |
   |---|---|---|
   | 25  | 1 | 25  |
   | 40  | 1 | 40  |
   | 150 | 1 | 150 |
   | 999 | 1 | 999 |
   | 25  | 2 | 44  |
   | 40  | 2 | 70  |
   | 150 | 2 | 263 |
   | 240 | 2 | 420 |
   | 260 | 2 | 455 |
   | 75  | 3 | 188 |

   The `150 → 263` case is the banker's-rounding sentinel: it fails under built-in `round()` and must be present.
2. **Mk 1 identity invariant:** for every seeded-range value tested, `npc_max_vitality(defn, 1) == defn.base_vitality`.
3. **Spawn-path test:** create a test `NpcDefinition` (e.g. `base_vitality=40`) with a `RoomSpawn` at `mk_tier=2`, run the tick engine's respawn sweep the way existing tick-engine tests drive it, and assert the created instance has `vitality_current == vitality_max == 70`. A companion `mk_tier=1` spawn asserts `40` (live-content invariance at the integration layer).

## 5. Verification (gates issue close)

1. Full in-container suite passes — the only working invocation form:
   `docker exec <django container> python manage.py test apps/shyland/tests`
   (directory-path form; the label form crashes on the `apps` namespace package.)
2. The new module's cases all pass, including the `150 → 263` sentinel.
3. `grep -rn 'NpcInstance.objects.create' django/src/apps/shyland --include='*.py'` (non-test) still shows exactly one site, and it routes through `npc_max_vitality`.
4. `make deploy-dev` from the worktree once 1–3 pass.
5. Live dev spot-check after deploy (objectively verifiable, via `make shell`): confirm a freshly respawned Mk 1 instance still carries its definition's flat `base_vitality` (e.g. any cave beetle at 40).

Close #104 only after all verification steps pass.

## 6. Operator playtest checklist (dev stack)

The change has no Mk 2 surface until Mk 2 content is authored (V25-era); the playtestable claim is Mk 1 invariance:

- [ ] Fight and kill one Z01 normal (e.g. a cave beetle) — fight length and feel unchanged.
- [ ] Fight one boss or elite far enough to read its health-description transitions — unchanged.

(If you judge this surface too thin to bother, the "No playtests for this brief" disposition is reasonable — your call, recorded per #170.)

## 7. Architecture doc (last, gated)

This step is gated on all implementation and verification steps above being complete and passing. Update `docs/shyland/Shyland_Architecture_v24.md` **in place**:

- Header stamp `24.12 → 24.13`; the architectural-changes **hash moves** to this release's implementation commit (this is an architectural change).
- **§4.5 Combat utilities (`combat_utils.py`):** document `NPC_HP_BAND_LIFT` and `npc_max_vitality()` (formula, half-up rounding rationale, #104).
- **§4.9 Tick Engine (`run_tick_engine.py`):** update the respawn-sweep description — instance HP now comes from `npc_max_vitality`, not flat `base_vitality`.

## 8. Closeout

Commit the closeout report (completing the Step 0 stub in place) as a `.txt` in `docs/shyland/`, including the final commit hash and the operator playtest disposition (#170). Commit and push at every step boundary — branch only, never merge. Then: run the issues report.
