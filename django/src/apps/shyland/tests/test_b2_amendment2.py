"""v22 brief 2 amendment 2: agro unification and the stats-pane repaint.

Pure CSS by design — coverage is the source-conformance scan, in the
pattern of Amendment 1's vocabulary scan."""

from pathlib import Path

from django.test import SimpleTestCase

from apps.shyland import consumers


class StatsRepaintConformanceTests(SimpleTestCase):

    def _template(self):
        path = (Path(consumers.__file__).parent
                / 'templates' / 'shyland' / 'game.html')
        return path.read_text()

    def test_dead_hexes_do_not_survive(self):
        html = self._template()
        for dead in ('#8FCF9F', '#D8B45A', '#40B58C', 'rgba(64, 181, 140'):
            self.assertNotIn(dead, html)

    def test_agro_color_unified_with_error(self):
        html = self._template()
        self.assertIn('--agro-color: #E24B4A', html)
