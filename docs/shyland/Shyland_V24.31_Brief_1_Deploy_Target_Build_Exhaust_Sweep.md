# Shyland V24.31 — Brief 1: Deploy-Target Build-Exhaust Sweep

- **Release:** Version 24.31 (point release) — milestone `Version 24.31`
- **Branch:** `version_24_31`
- **Founding ticket:** #205 — *Production deploy target gains a prune — stop the ~500MB/release root-volume growth* (operator-ruled 2026-08-15; the ruling comment on the issue supersedes the issue body's implementation shape)
- **Dependency:** #255 — arch doc §2.2's Makefile table is stale (documents a nonexistent `make reset`, omits the whole deployment/guard surface). Ruled to ride this brief rather than a separate ops session, because §8 rewrites that exact table and a split would guarantee a closeout merge conflict.
- **Written by:** the V24.31 design session, 2026-08-15.

---

## 1. Problem and ruling

Every `make build` leaves exhaust behind on the daemon it ran against: orphaned (`<none>`) image pairs plus BuildKit cache entries. Nothing sweeps it. Field data from #205:

- **Prod:** root volume 20% → 58% across ~10 releases (2026-07-29 → 2026-08-11); ~500MB per release.
- **Dev (Emma's Lima VM):** 41GB / 898 cache entries on 2026-08-06 (VM disk 43%), and 22.8GB again by 2026-08-11 — roughly 2GB per build.

Both daemons have needed manual operator catch-ups. This brief makes the sweep automatic, inside the two deploy targets.

**The reconciliation that determines the fix.** The issue's body ruled a **dangling-image prune only**, based on the 2026-08-06 census (13 dangling image pairs, 4.35GB "reclaimable"). The 2026-08-11 follow-up found `docker image prune` reclaimed **~0B on both daemons**, and `docker builder prune -a` is what actually freed the space (7.3GB prod, 22.8GB dev). Both observations are true and not in conflict: the dangling images' layers were *also* held by build-cache references, so pruning the image records released **records, not bytes**; the builder prune released the last references and the layers actually died.

**Ruling (operator, 2026-08-15, on #205):**

1. The sweep is **both prunes**, image first then builder, and **the builder prune is the load-bearing one**. Shipped as the body ruled — dangling images only — the fix would have appeared not to work.
2. Eviction is **size-capped LRU, not `-a`**: the most recent build's layers are by definition kept, so the next deploy's expensive layer (pip) is still a cache hit and **no deploy gets slower**. This is the property `-a` cannot offer, and the 2026-07-29 slowdown is why it matters.
3. **Both targets get the sweep** — `deploy-dev` as well as `deploy-prod`. The issue body left dev as an optional rider needing its own nod; the operator gave it this session. Dev grows faster than prod and has already cost two manual catch-ups.
4. The sweep is **non-fatal**, and on `deploy-prod` it runs **after** the resting-posture restore. Rationale in §4.

**Scope:** entirely within `Makefile` — **shared deployment surface, operator-confirmed this session** (CLAUDE.md Rule 2) — apart from the standing version-constant bump (§3), which touches `version.py` and its pin test as every release does. **No game code, no model change, no migration, no seed data, no GDD change** (nothing player-facing changes, so this release produces no `(pending implementation)` markers).

## 2. Technical claims — verified per the v36 technical-coherence rule

Every claim below was **confirmed against the code at writing time** — branch `version_24_31` at commit `5757b19` (the branch was cut from `origin/main` at that commit and carries no commits of its own yet). File: `Makefile`. Line numbers are indicative at that commit, not load-bearing.

1. **Daemon versions, both read live at writing time.** Dev (Emma, Rancher Desktop): `docker --version` → **29.6.2-rd**; `docker builder prune --help` routes to `docker buildx prune` and offers **`--reserved-space bytes`** with **no `--keep-storage`**. Prod (operator-supplied, in conversation): **Docker Engine 25.0.16, API 1.44, linux/arm64** — the pre-rename era, where **`--keep-storage`** is the valid spelling. `--keep-storage` was renamed `--reserved-space` in Docker 28. **The flag genuinely diverges by daemon; one spelling cannot serve both.**
2. **`PROD_DOCKER_HOST` (line 14):** `PROD_DOCKER_HOST := ssh://ec2-user@games.magrathea.com`, declared with `:=` under a comment noting it is owned by the production deploy target and pinned per command, never exported ambiently. **The Makefile's variable convention is `:=` throughout**, not `?=`.
3. **`deploy-dev` (lines 147–154)** — prerequisite `require-local`, so `DOCKER_HOST` is **guaranteed unset** when its recipe runs and a bare `docker` command necessarily targets the local dev daemon:
   ```make
   deploy-dev: require-local
   	@test -s .env.dev || (echo "ERROR: .env.dev missing or empty." && exit 1)
   	cp .env.dev .env
   	python3 scripts/check_docker_host.py
   	$(MAKE) build
   	$(MAKE) migrate
   	@echo "deploy-dev complete — local dev stack refreshed."
   ```
4. **`deploy-prod` (lines 163–172)** — no prerequisite; it guards inline and pins `DOCKER_HOST` per command:
   ```make
   deploy-prod:
   	@test -z "$(DOCKER_HOST)" || (echo "ERROR: DOCKER_HOST is already set ..." && exit 1)
   	@test -s .env.prod || (echo "ERROR: .env.prod missing or empty." && exit 1)
   	@test -s .env.dev || (echo "ERROR: .env.dev missing or empty — deploy-prod needs it to restore the resting posture." && exit 1)
   	cp .env.prod .env
   	DOCKER_HOST=$(PROD_DOCKER_HOST) python3 scripts/check_docker_host.py
   	DOCKER_HOST=$(PROD_DOCKER_HOST) $(MAKE) build
   	DOCKER_HOST=$(PROD_DOCKER_HOST) $(MAKE) migrate
   	cp .env.dev .env
   	@echo "deploy-prod complete — production deployed, resting posture restored (.env == .env.dev)."
   ```
   Its comment block (lines 156–162) states the deliberate failure contract: a partway failure **leaves `.env` in prod posture** for a human, and the guards block dev work until it is restored by hand.
5. **`.env` is `-include`d at line 6**, so its keys become Make variables — this is why the guards catch a `DOCKER_HOST` set in `.env` as well as one from the environment. **Only `docker compose` substitutes from `.env`; a bare `docker image prune` / `docker builder prune` does not read it.** This is what makes claim-4's ordering change in §4.3 safe.
6. **The `.PHONY` list (lines 33–36)** already contains `deploy-dev` and `deploy-prod`. **This brief adds no new targets, so `.PHONY` is not edited.**
7. **`make help` (lines 344–350)** prints a Deployment block describing all four deployment targets; `deploy-dev` reads *"Deploy current source to the local dev stack (build + migrate)"* and `deploy-prod` *"Operator-authorized production deploy (flips posture, / pre-flights, builds, migrates, restores dev posture)"*.
8. **There is no `reset` target in the Makefile** (#255). Verified against the complete target list at this commit. The nearest real target is **`nuke` (line 126)**, which is materially different: `require-local`-gated, removes containers/volumes/images, and does **not** rebuild, start, migrate, or seed.
9. **Arch doc §2.2's table (`docs/shyland/Shyland_Architecture_v24.md`, lines 122–134)** lists eleven rows ending in the nonexistent `make reset`, and omits `deploy-dev`, `deploy-prod`, `seed-prod`, `verify-prod`, `require-local`, `crosscheck-env`, `hooks`, `push-certs`, `nuke`, `createuser`, `gen-certs`, `seed`, `verify`, `check-secrets`, `gdd` and `help`. (`verify` / `verify-prod` *are* described accurately elsewhere in the doc, near line 1518 — only this table is behind.)
10. **Version constant:** `django/src/apps/shyland/version.py` line 8 (`SHYLAND_VERSION = "24.30"`); pin test `django/src/apps/shyland/tests/test_b2_amendment1.py` line 118 (`self.assertEqual(SHYLAND_VERSION, '24.30')`).

Self-consistency: this brief was given one end-to-end read before commit; §2's claims, §4's edits, §6's verification and §8's arch-doc scope agree.

## 3. Step 1 — version start (opening act, standing requirement)

1. In its **own commit**: `SHYLAND_VERSION = "24.31-DEV"` in `django/src/apps/shyland/version.py`, and the pin test in `tests/test_b2_amendment1.py` moved to `'24.31-DEV'` in the same commit.
2. `make deploy-dev` from the worktree (the version-start deploy). **Note:** at this point `deploy-dev` still has no sweep — that is expected; §6.1 uses this run as the *before* measurement.

## 4. Step 2 — implementation

All edits in `Makefile`. Nothing under `django/src/` changes in this step.

### 4.1 Add the cap variables

Immediately **after** the `PROD_DOCKER_HOST` declaration (§2 claim 2, line 14) and its comment, add:

```make
# Build-exhaust sweep caps (#205). Every build orphans image layers and leaves
# BuildKit cache entries behind; unswept, prod's root volume grows ~500MB per
# release and Emma's dev VM ~2GB per build. Eviction is LRU to a cap rather
# than a full prune, so the most recent build's layers survive and no deploy
# gets slower. The flag name diverges by daemon version: --keep-storage was
# renamed --reserved-space in Docker 28. Prod runs Docker Engine 25.0.16
# (linux/arm64); Emma's dev daemon runs 29.6.2-rd.
PROD_BUILDER_PRUNE_FLAGS := --keep-storage 5GB
DEV_BUILDER_PRUNE_FLAGS  := --reserved-space 5GB
```

Use `:=`, matching the file's convention (§2 claim 2) — **not `?=`**. These caps must not be overridable from an ambient environment.

### 4.2 `deploy-dev` — sweep after migrate

Insert two lines after `$(MAKE) migrate` and amend the completion echo:

```make
	$(MAKE) migrate
	-docker image prune -f
	-docker builder prune -f $(DEV_BUILDER_PRUNE_FLAGS)
	@echo "deploy-dev complete — local dev stack refreshed, build exhaust swept."
```

Bare `docker` is correct here: `require-local` guarantees `DOCKER_HOST` is unset (§2 claim 3).

### 4.3 `deploy-prod` — sweep after the posture restore

Insert two lines **after** `cp .env.dev .env` and amend the completion echo:

```make
	cp .env.dev .env
	-DOCKER_HOST=$(PROD_DOCKER_HOST) docker image prune -f
	-DOCKER_HOST=$(PROD_DOCKER_HOST) docker builder prune -f $(PROD_BUILDER_PRUNE_FLAGS)
	@echo "deploy-prod complete — production deployed, build exhaust swept, resting posture restored (.env == .env.dev)."
```

Also extend the target's comment block (lines 156–162) with a sentence recording why the sweep sits last:

```make
# The build-exhaust sweep (#205) runs LAST, after the posture restore, and is
# non-fatal. Both prunes pin their own DOCKER_HOST and neither reads .env, so
# posture is irrelevant to them — running them after the restore means not even
# an operator Ctrl-C during a long prune can strand production posture.
```

### 4.4 Three rules that must not be deviated from

1. **Never `-a` on `docker image prune`.** Bare (dangling-only) is the whole intent. `docker image prune -a` removes tagged base images — that is precisely what caused the 2026-07-29 cold-rebuild slowdown the issue warns about.
2. **Never `-a` on `docker builder prune` either.** The cap flags replace it, by ruling 2. `-a` was the emergency manual instrument, not the shipped one.
3. **Both prune lines keep make's `-` error-ignore prefix.** Housekeeping must never fail a deploy. On `deploy-prod` specifically, a hard failure would abort the recipe and — combined with the target's deliberate leave-prod-posture-on-failure contract (§2 claim 4) — block all dev work behind the guards over a disk-cleanup step. Do **not** substitute `|| true`; the `-` prefix keeps the failure visible in make's output (`Error 1 (ignored)`), which is the signal §6.4 and §7 depend on.

### 4.5 `make help`

Amend the two Deployment lines (§2 claim 7) so the printed help stays truthful about the sweep — the `deploy-dev` line gains *"+ exhaust sweep"* and the `deploy-prod` line's parenthetical gains *"sweeps exhaust"*. Keep the existing column alignment and line-wrapping style.

**Migration step: none.** No model changes. (Stated explicitly per the brief rules.)

## 5. Step 3 — tests

**No new tests, and no test file is created.** The Makefile is not under test in this repo; there is no harness that could exercise a make recipe, and inventing one is out of scope for this release. Verification is by execution (§6).

The full Django suite is still the regression bar and must pass with **no edits beyond the §3 version pin**: suite **687** at the V24.30 stamp, unchanged by this release. If any existing test fails, that is a deviation to stop and report — not a test to edit.

## 6. Verification

1. **Before measurement.** After §3's version-start `make deploy-dev` (which still has no sweep), record `docker system df` — specifically the Build Cache row's SIZE and RECLAIMABLE. This is the *before* number.
2. **Flag acceptance on dev.** After §4, run `make deploy-dev`. Both prune lines must execute and exit **0** — in particular `--reserved-space 5GB` must be accepted, not rejected as an unknown flag. A `make: [Makefile:NN: deploy-dev] Error 1 (ignored)` line for either prune means the flag was rejected: **stop and report**, do not work around it.
3. **The cap holds.** `docker system df` after the sweep shows Build Cache SIZE at or below **5GB**. Record before/after and the reclaimed delta in the closeout. **A reclaimed delta of ~0 is a valid pass**, not a failure, if the cache was already under the cap when the sweep ran (the last manual dev catch-up on 2026-08-11 left it at 5.9GB, so the first sweep may reclaim little); the assertion is the *ceiling*, not the delta.
4. **No deploy got slower — the property the whole ruling rests on.** Run `make deploy-dev` a **second** time immediately, with no source change. The build output must show the pip/requirements layer as **CACHED**. If it rebuilds, the cap is evicting the layers it was chosen to preserve — stop and report.
5. **Posture intact.** After each `make deploy-dev`, `cmp -s .env .env.dev` succeeds (exit 0) — the resting posture is undisturbed.
6. **Full suite, in-container, the only working form:** `python manage.py test apps/shyland/tests` (via `docker exec` in the django container). All pass; suite count **687**, unchanged.
7. **`make help` renders** without breaking its alignment.

**The production line cannot be dev-tested and ships unexercised.** `--keep-storage` is rejected by dev's Docker 29 by construction, so §6.2 exercises only the dev spelling. This is a known, accepted residual: the `-` prefix (§4.4.3) bounds the blast radius to "the sweep silently does nothing", never a failed or posture-stranded deploy. It is exercised for the first time in this release's own closeout tail — see §7.

## 7. The prod-side first exercise — no separate action required

The issue body called for a one-time manual catch-up on prod to reclaim the accumulated backlog. **It is now free and needs no separate executor:** once this ships, V24.31's own closeout-tail `make deploy-prod` performs the first sweep as part of an ordinary deploy, reclaiming everything accumulated to date.

**There is therefore no `PENDING DEPLOY-TIME ACTIONS` block** — no data action, no seed, no `verify_*` command, nothing prod-side that a session must run separately. The executor checkpoint (#248) is satisfied by construction: the only prod-side step is inside `make deploy-prod`, whose executor is `make deploy-prod`.

What the **closeout tail** must do is *read its own output* and record, in the closing report:

- whether both prune lines ran clean or either printed `Error 1 (ignored)` — the latter meaning prod's `--keep-storage` was rejected after all;
- the bytes reclaimed by each prune.

If `--keep-storage` is rejected, file a follow-up issue (the flag spelling would need to move to `--reserved-space`, meaning prod's daemon was upgraded past Docker 28). The deploy itself is unaffected either way.

## 8. Operator playtest checklist (dev stack)

Ready after this brief's `make deploy-dev`.

**This release has no playtestable game surface.** Nothing player-facing changes — no command, no output, no model, no content. The correct disposition for this brief is expected to be **"No playtests for this brief"** (#170, terminal).

The operator may optionally confirm the infrastructure change directly, none of it in-game:

1. Run `make deploy-dev` and watch the tail of the output: both prune lines run, the completion echo reads `deploy-dev complete — local dev stack refreshed, build exhaust swept.`
2. `docker system df` → Build Cache at or below 5GB.
3. Log in to the dev stack and confirm the game is up and behaves exactly as it did before (`look`, `who`, `inv`) — the sweep must be invisible from inside the game.
4. `make help` → the Deployment block reads correctly.

## 9. Architecture doc — last, gated

This step is gated on all implementation and verification steps above being complete and passing.

`docs/shyland/Shyland_Architecture_v24.md`, updated **in place** (point-release document rule):

1. **Stamp → 24.31.** The header's "as of commit" hash **moves** to this brief's final implementation commit. **Design-session ruling on this point:** the hash moves even though no *game* code changes, because §2 documents the build and deployment machinery and this release changes the deployment procedure itself — infrastructure is architecture here. (Contrast v24.24, whose hash did not move: that was presentation-only template work.) Append a one-line summary in the header's established style.
2. **Add the V24.31 release paragraph** at the top of the release box-out stack, in the established style. Prior release paragraphs are history and are **not** edited.
3. **§2.2 "Makefile workflow" — rewrite the table** (§2 claim 9). This carries **#255**, the erratum, by the ruling recorded on that issue:
   - **Delete the `make reset` row** — the target does not exist. Do **not** rename it to `nuke`; add `nuke` as its own row with its real behavior (`require-local`-gated; removes containers, volumes and images; does not rebuild, start, migrate or seed).
   - **Add the deployment targets:** `deploy-dev`, `deploy-prod`, `seed-prod` (#187), `verify-prod` (#249) — the four posture-setting targets, noting they are the only ones permitted to write `.env`, and that the last three are operator-authorized and bare-only.
   - **Add the guards:** `require-local` and `crosscheck-env`, noting they are check-only (they stop on mismatch and never copy or repair) and run automatically before daemon-touching targets.
   - **Add the remaining shipped targets** the table omits: `hooks`, `push-certs`, `createuser`, `gen-certs`, `seed`, `verify`, `check-secrets`, `gdd`, `help`.
   - Verify the finished table against the Makefile target-for-target before committing — the whole point of #255 is that this table drifted unnoticed.
4. **Document the sweep** in §2.2, below the table, as a short passage: what it removes, why both prunes are needed (the layer-reference reconciliation from §1), why the cap rather than `-a`, why the flag differs by daemon, why it is non-fatal, and why it runs after the posture restore on `deploy-prod`. Cite #205.
5. The existing **"Critical workflow note"** under §2.2 is correct and stays.

**No GDD change** (§1). Do not run `make gdd`.

## 10. Closeout report

`docs/shyland/Shyland_V24.31_Brief_1_Closeout.txt` (stub created and pushed at Step 0 per the standing ritual, completed in place): final commit hash, suite count (687), the §6 verification results — **including the before/after `docker system df` numbers and the §6.4 cache-hit observation** — any deviations, an explicit note that the production prune line ships unexercised (§6), and the **operator playtest disposition** line (#170).

**No PENDING DEPLOY-TIME ACTIONS** (§7).
