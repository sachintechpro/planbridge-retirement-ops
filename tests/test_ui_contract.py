"""Static UI contract tests for accessibility, responsive behavior, and contextual help.
The business logic remains covered by test_engine.py.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "static" / "styles.css").read_text(encoding="utf-8")
JS = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")


class UIContractTests(unittest.TestCase):
    def test_distinct_accessible_theme(self):
        self.assertIn("PLANBRIDGE-V2-EDITORIAL-THEME", CSS)
        self.assertIn("#302437", CSS)
        self.assertIn("Georgia", CSS)
        self.assertIn("font-size:16px", CSS)

    def test_mobile_viewports_and_overflow_guards(self):
        self.assertIn("@media(max-width:900px)", CSS)
        self.assertIn("@media(max-width:600px)", CSS)
        self.assertIn("@media(max-width:360px)", CSS)
        self.assertIn("grid-template-columns:minmax(0,1fr)", CSS)
        self.assertIn("overflow-x:auto", CSS)

    def test_navigation_accessibility(self):
        self.assertIn("aria-label=\"Open navigation\"", HTML)
        self.assertIn("togglePlanBridgeDrawer", JS)
        self.assertIn("closePlanBridgeDrawer", JS)
        self.assertIn("aria-expanded", JS)
        self.assertIn("Escape", JS)

    def test_help_is_available_on_every_page(self):
        self.assertIn("renderAssistance(page)", JS)
        for page in ["overview","employers","participants","payroll",
                     "exceptions","ledger","requests","architecture","quality"]:
            self.assertIn(page + ":[", JS)

    def test_help_is_touch_and_keyboard_accessible(self):
        self.assertIn('<details class="context-topic">', JS)
        self.assertIn('<summary>', JS)
        self.assertIn("help-inline", JS)
        self.assertIn("summary:focus-visible", CSS)

    def test_guidewire_analogy_is_not_misrepresented(self):
        self.assertIn("not an InsuranceSuite integration", JS)
        self.assertIn("PolicyCenter", JS)
        self.assertIn("BillingCenter", JS)
        self.assertIn("ClaimCenter", JS)


if __name__ == "__main__":
    unittest.main()
