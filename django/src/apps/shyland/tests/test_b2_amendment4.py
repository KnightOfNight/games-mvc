"""v22 brief 2 amendment 4: the exhaustive palette conformance test.

Chart-as-license (ruled 2026-07-20): the color chart is not a
description of the colors in use — it is the license to use them. A
color literal not on the chart, or on the explicitly documented chrome
list, is a defect by definition. This test asserts SET EQUALITY between
the template's color literals and ALLOWED_COLORS: a new color appearing
fails, and an allowed color disappearing fails — every palette change is
a deliberate two-place edit (CSS + allowlist) traceable in one diff.

Supersedes-and-absorbs the piecemeal dead-hex scans of amendments 1–3
(those tests remain in their own modules; their assertions are implied
here — any dead hex reappearing breaks set equality)."""

import re
from pathlib import Path

from django.test import SimpleTestCase

from apps.shyland import consumers


# The license. Two groups; every entry annotated. Normalized form:
# uppercase, #RRGGBB (or #RRGGBBAA).
ALLOWED_COLORS = {
    # ------------------------------------------------------------------
    # Chart colors (the B2 DD §2 palette + rarity scale, as amended)
    # ------------------------------------------------------------------
    '#7FB3D5',    # key-color
    '#E8E4D8',    # value-color (also --loc-room, independently declared per #1)
    '#6B6B80',    # muted-color (also --conn-gray)
    '#E24B4A',    # error-color / agro-color / crit-out / Artifact rarity / --combat-accent
    '#F0C060',    # say-color / Epic rarity
    '#E8D44D',    # warn-color
    '#4CAF7D',    # loot-color / success-color (also --conn-green)
    '#C4453F',    # hit-out-color (and generic combat)
    '#E0724A',    # hit-in-color / Legendary rarity
    '#F08A50',    # crit-in-color
    '#9C9A90',    # Common rarity / flag-chrome
    '#5FA8D3',    # Uncommon rarity
    '#B387E8',    # Rare rarity
    '#3A1212',    # combat-bg (the v20 #2 combat-red family tint)
    # ------------------------------------------------------------------
    # Chrome — structural colors not yet on the chart. Each is
    # chrome — pending chart ruling; the closeout lists this group as the
    # design chat's ruling queue. Do not change these here.
    # ------------------------------------------------------------------
    '#0D0D0F',    # chrome — pending chart ruling (--bg)
    '#16161A',    # chrome — pending chart ruling (--surface)
    '#2A2A35',    # chrome — pending chart ruling (--border)
    '#C8C8D4',    # chrome — pending chart ruling (--text: body default, input)
    '#7B68EE',    # chrome — pending chart ruling (--accent: prompt, caret, send button)
    '#A8D8A8',    # chrome — pending chart ruling (--room: dead declaration, zero readers)
    '#8888AA',    # chrome — pending chart ruling (--system: dead declaration, zero readers)
    '#E0A840',    # chrome — pending chart ruling (--conn-amber: connection dot)
    '#6E6C64',    # chrome — pending chart ruling (.msg-ts timestamp prefix)
    '#CCCCCC',    # chrome — pending chart ruling (zone/area color JS fallbacks)
    '#CCCCCCBF',  # chrome — pending chart ruling (--zone-border fallback, ~0.75 alpha)
    '#FFFFFF',    # chrome — pending chart ruling (#send-btn text, authored as #fff)
}


def extract_color_literals(source):
    """Every color literal in a value position: hex forms preceded (bar
    whitespace) by ':', a quote, or '=' — which excludes issue references
    in comments ('(#124)') — plus every rgb()/rgba() form anywhere.
    #RGB expands to #RRGGBB; comparison is case-insensitive."""
    found = set()
    for m in re.finditer(
        r"""[:'"=]\s*#([0-9A-Fa-f]{8}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})\b""",
        source,
    ):
        body = m.group(1)
        if len(body) == 3:
            body = ''.join(ch * 2 for ch in body)
        found.add('#' + body.upper())
    for m in re.finditer(r'rgba?\([^)]*\)', source):
        found.add(re.sub(r'\s+', ' ', m.group(0)).upper())
    return found


class PaletteConformanceTests(SimpleTestCase):

    def test_template_colors_equal_the_license_exactly(self):
        path = (Path(consumers.__file__).parent
                / 'templates' / 'shyland' / 'game.html')
        found = extract_color_literals(path.read_text())
        unlicensed = found - ALLOWED_COLORS
        vanished = ALLOWED_COLORS - found
        self.assertEqual(
            unlicensed, set(),
            f'Color literals with no license (add to the chart or the '
            f'chrome list deliberately): {sorted(unlicensed)}',
        )
        self.assertEqual(
            vanished, set(),
            f'Licensed colors no longer present (remove from '
            f'ALLOWED_COLORS deliberately): {sorted(vanished)}',
        )

    def test_report_color_is_value_color(self):
        path = (Path(consumers.__file__).parent
                / 'templates' / 'shyland' / 'game.html')
        html = path.read_text()
        self.assertNotIn('#B8B4A6', html)
        self.assertNotIn('#b8b4a6', html)
        m = re.search(r'\.msg-report\s*\{([^}]*)\}', html)
        self.assertIsNotNone(m)
        self.assertIn('var(--value-color)', m.group(1))
