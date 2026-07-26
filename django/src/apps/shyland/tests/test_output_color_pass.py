"""v23 B5 amendment 1 (#152): the output-color pass — the miss split,
ambient/narration off muted, and copper loot at reward."""

import pathlib
import re

from django.test import SimpleTestCase

from apps.shyland.tests.test_b2_amendment4 import (
    ALLOWED_COLORS, extract_color_literals,
)

APP_DIR = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = (APP_DIR / 'templates' / 'shyland' / 'game.html').read_text()


def python_sources():
    for path in APP_DIR.rglob('*.py'):
        rel = path.relative_to(APP_DIR).parts
        if rel[0] in ('tests', 'migrations') or '__pycache__' in rel:
            continue
        yield path, path.read_text()


def css_rule(selector):
    """The declaration block for one selector, whitespace-tolerant."""
    m = re.search(re.escape(selector) + r'\s*\{([^}]*)\}', TEMPLATE)
    return re.sub(r'\s+', ' ', m.group(1)).strip() if m else None


class ColorPassCssTests(SimpleTestCase):

    def test_the_four_rules(self):
        self.assertEqual(css_rule('.msg-combat-miss-out'),
                         'color: var(--warn-color);')
        self.assertEqual(css_rule('.msg-combat-miss-in'),
                         'color: var(--success-color);')
        self.assertEqual(css_rule('.msg-system'),
                         'color: var(--value-color);')
        self.assertEqual(css_rule('.msg-room'),
                         'color: var(--value-color);')

    def test_legacy_rule_survives(self):
        self.assertEqual(css_rule('.msg-combat-miss'),
                         'color: var(--muted);')

    def test_no_new_hex(self):
        # The pass is variable-only: the template's color-literal set still
        # equals the chart-as-license allowlist, reusing that test's own
        # extractor rather than duplicating its logic.
        self.assertEqual(extract_color_literals(TEMPLATE), ALLOWED_COLORS)


class ColorPassSenderTests(SimpleTestCase):

    def test_zero_legacy_senders(self):
        pattern = re.compile(r"['\"]combat-miss['\"]")
        offenders = [str(p) for p, src in python_sources()
                     if pattern.search(src)]
        self.assertEqual(offenders, [])

    def test_both_new_senders_exist_once_each(self):
        counts = {'combat-miss-out': [], 'combat-miss-in': []}
        for path, src in python_sources():
            for cat in counts:
                counts[cat] += [str(path)] * len(
                    re.findall(r"['\"]" + cat + r"['\"]", src))
        for cat, hits in counts.items():
            self.assertEqual(len(hits), 1, f'{cat}: {hits}')
            self.assertTrue(hits[0].endswith('run_tick_engine.py'), hits[0])

    def test_copper_loot_pays_reward(self):
        src = (APP_DIR / 'consumers.py').read_text()
        m = re.search(
            r'You loot \{copper_str\} from \{corpse\.display_name\}\.\"'
            r',\s*\"(\w+)\"', src)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), 'reward')

    def test_combat_family_styling_coverage(self):
        # Every combat-… category a server source can send has a client
        # rule — a category can never ship unstyled. seed_world.py is
        # excluded: it sends no messages, and its item slugs (e.g. the
        # Combat Knife's 'combat-knife') would false-positive the match.
        sent = set()
        for path, src in python_sources():
            if path.name == 'seed_world.py':
                continue
            sent |= set(re.findall(r"['\"](combat[a-z-]*)['\"]", src))
        self.assertIn('combat-miss-out', sent)   # the walk found the senders
        for category in sorted(sent):
            self.assertIn(f'.msg-{category}', TEMPLATE,
                          f'category {category!r} has no CSS rule')
