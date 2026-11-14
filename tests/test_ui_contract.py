"""Regression checks for mobile typography and asset delivery.

Browser viewport coverage is exercised in development with Playwright; these
standard-library checks also run in Render's dependency-free CI build.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class ResponsiveUIContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / 'static/index.html').read_text(encoding='utf-8')
        cls.theme = (ROOT / 'static/theme.css').read_text(encoding='utf-8')
        cls.server = (ROOT / 'server.py').read_text(encoding='utf-8')

    def test_mobile_viewport_and_versioned_assets(self):
        self.assertIn('width=device-width,initial-scale=1', self.html)
        for url in ['/styles.css?v=2.1', '/theme.css?v=2.1', '/help.js?v=2.1', '/app.js?v=2.1']:
            with self.subTest(url=url):
                self.assertIn(url, self.html)

    def test_all_navigation_and_context_helpers_load(self):
        self.assertIn('id="menu-toggle"', self.html)
        self.assertIn('id="nav-scrim"', self.html)
        self.assertIn('/help.js?v=2.1', self.html)
        self.assertTrue((ROOT / 'static/help.js').exists())
        self.assertIn('PlanBridgeHelp', (ROOT / 'static/app.js').read_text(encoding='utf-8'))
        self.assertIn("'/theme.css'", self.server)
        self.assertIn("'/help.js'", self.server)

    def test_font_scale_technical_notes_and_mobile_overflow(self):
        for expected in ['--type-body: 16px', 'text-size-adjust: 100%',
                         '.note {', 'font-size: 15px', '.table-wrap {',
                         '@media (max-width:600px)', 'overflow-wrap: anywhere']:
            with self.subTest(rule=expected):
                self.assertIn(expected, self.theme)

if __name__ == '__main__':
    unittest.main()
