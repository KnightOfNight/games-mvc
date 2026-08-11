"""v22 brief 2 amendment 1 (#120): the single source of truth for the
player-visible Shyland version. The version-closeout ritual bumps this to
the release stamp (e.g. "22.0") alongside the GDD and architecture
stamps; point releases bump it the same way on their own branch ("22.1",
...) — main never carries a DEV-suffixed stamp (Deployment Law). The
constant tells the truth about the code it ships with."""

SHYLAND_VERSION = "24.20-DEV"
