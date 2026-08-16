# Shyland Standalone Ops Brief — Build-Exhaust Sweep Corrections (#257)

**Lane:** standalone ops brief, main — Makefile deployment surface (#187/#249-Part-1 precedent) plus errata-lane doc corrections. **Authority:** operator direction 2026-08-15 ("fix deployment cleanups here and now"). **Founding facts:** #257 (V24.31 sweep follow-up).

**Verified facts this brief stands on (v36 technical coherence — every claim checked live this session, none from recall):**
- The prune flag is parsed **client-side** by Emma's CLI (29.6.2-rd, confirmed `docker version`); `DOCKER_HOST` redirects the API call only. Proof: the V24.31 tail ran `--keep-storage` against prod's Engine 25.0.16 and the *local* CLI accepted it as a deprecated alias and printed the deprecation warning (#257 body, live output). The CLI's help advertises only `--reserved-space` (confirmed).
- Prod's build cache: **3.199GB, 134 entries, 0 active, 100% reclaimable** (`docker system df`, confirmed live); `make build` is `--no-cache` by design, so no build ever reads it. Prod root volume 20G / 38% used.
- Prod's daemon is dedicated to this stack; Emma's dev daemon is shared (rancher-desktop) and `builder prune` eviction is daemon-wide.

## 1. Makefile

1. **Prod's builder prune goes uncapped:** the line becomes `docker builder prune -f` (no size flag). Rationale: the 5GB reserve on prod preserves only never-readable exhaust (0 active entries, `--no-cache` builds) on a dedicated daemon — and dropping the flag entirely removes the deprecated-alias exposure on that line (there is no flag left to be removed from under us). Delete `PROD_BUILDER_PRUNE_FLAGS`.
2. **Dev keeps its cap, current spelling:** `DEV_BUILDER_PRUNE_FLAGS := --reserved-space 5GB` stays — the dev daemon is shared, eviction is daemon-wide, and the reserve bounds collateral eviction of other projects' caches. The spelling is already the CLI's canonical one.
3. **The sweep goes loud-on-failure while staying non-fatal:** the `-` error-ignore prefixes on all four prune lines (image + builder, both deploy targets) are replaced with `<cmd> || echo "WARNING: ... failed — sweep skipped (non-fatal)"`. A future flag removal or daemon error prints an unmissable warning instead of make's `Error 1 (ignored)`; the deploy still never fails and posture handling is untouched (the prod sweep already runs after the posture restore).
4. **The header comment block is rewritten** to state the client-side-parsing fact and the real rationale for the asymmetry (dedicated vs shared daemon), replacing the false by-daemon-version story.

## 2. Doc corrections (errata-lane: shipped narrative is factually wrong, #257)

Both sites assert "the flag name diverges **by daemon**" and "the production line ships **unexercised**" — the mechanism claim is false (client-side parsing; one CLI parses both lines) and the tail already exercised the prod line. Corrections are minimal and in place; stamps and the architecture hash do **not** move (the #242 technical-writer lane):

1. **Architecture doc** (`Shyland_Architecture_v24.md`): the §2.2 "flag name diverges by daemon" bullet and the corresponding fragment in the version-header paragraph are corrected to the client-side fact and the new sweep shape (prod uncapped on a dedicated daemon; dev reserved-space on the shared one; loud-but-nonfatal), each marked "(corrected/updated by ops, 2026-08-15, #257)".
2. **GDD changelog row v24.31** (`gdd/_01_version_history.md`): the same false fragment corrected in place with the same provenance note; `make gdd` rebuild follows.
3. The V24.31 brief itself is a historical artifact — not edited; #257 records the defect.

## 3. One-off production reclaim (operator-directed, this session)

The corrected prod line only runs at the *next* deploy; the operator wants prod clean now. Run once, command-scoped, no posture involvement: `docker builder prune -f` against the prod daemon — expected reclaim ≈ 3.2GB (every entry inactive) — then confirm with `docker system df` (expected: build cache ≈ 0B) and record actual-vs-expected.

## 4. Verification

1. Dev-side sweep lines run standalone against the dev daemon: image prune + builder prune with the kept flag — both succeed; the `|| echo` form returns exit 0 either way.
2. `make -n deploy-prod` inspection is unavailable (guard denies embedded target names — by design); the prod lines are verified by review and by the one-off reclaim using the identical command.
3. Post-reclaim `docker system df` on prod shows build cache ~0B; root volume usage drops accordingly.
4. `make gdd` rebuild clean; grep confirms no remaining "diverges by daemon" text in arch doc or GDD source.

## 5. Out of scope

- The sanctioned daemon-inspection path (#257's third ruling scope, the #248-shaped gap on the daemon face) — filed as its own follow-up issue, not fixed here.
- The V24.31 brief document (historical); the `stock-playtest-items` skill; anything player-facing (nothing here is).

**Close:** commit applied changes to main, record applied state + reclaim numbers on #257, file the follow-up, close #257, run the issues report.
