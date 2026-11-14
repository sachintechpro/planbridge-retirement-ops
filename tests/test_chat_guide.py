"""Regression checks for the read-only, page-aware chat guide."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class ChatGuideContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / 'static/index.html').read_text(encoding='utf-8')
        cls.app = (ROOT / 'static/app.js').read_text(encoding='utf-8')
        cls.chat = (ROOT / 'static/chat.js').read_text(encoding='utf-8')
        cls.css = (ROOT / 'static/chat.css').read_text(encoding='utf-8')
        cls.help = (ROOT / 'static/help.js').read_text(encoding='utf-8')
        cls.server = (ROOT / 'server.py').read_text(encoding='utf-8')

    def test_chat_assets_delivered_by_the_python_server(self):
        for asset in ('/chat.js', '/chat.css'):
            with self.subTest(asset=asset):
                self.assertIn("'" + asset + "'", self.server)
                self.assertIn(asset + '?v=1', self.html)

    def test_all_nine_page_contexts_and_technical_terms(self):
        for page in ('overview', 'employers', 'participants', 'payroll',
                     'exceptions', 'ledger', 'requests', 'architecture', 'quality'):
            with self.subTest(page=page):
                self.assertIn(page + ': {', self.chat)
        for term in ('remittance mismatch', 'deferral', 'idempotency', 'rbac',
                     'csrf', 'guidewire', 'variance', 'needs_review',
                     'allocation', 'test bench', 'tenant isolation'):
            with self.subTest(term=term):
                self.assertIn("'" + term + "'", self.chat)

    def test_chat_tracks_active_page_persona_and_selected_record(self):
        self.assertIn("window.PlanBridgeChat?.setContext({page,actor:S.actor", self.app)
        self.assertIn('batch:S.batches.find', self.app)
        self.assertIn('person:S.people.find', self.app)
        self.assertIn('pageHelp,tableHelp', self.help)
        self.assertIn('selectedValue()', self.chat)

    def test_guide_is_read_only_and_responsive(self):
        self.assertNotIn("fetch(", self.chat)
        self.assertNotIn("XMLHttpRequest", self.chat)
        self.assertNotIn("fetch(", self.chat)
        self.assertIn('pb-guide-panel[hidden]', self.css)
        self.assertIn('@media(max-width:650px)', self.css)
        self.assertIn("e.key==='Escape'", self.chat)
        self.assertIn("textContent=text", self.chat)  # no unsafe HTML for visitor messages
        self.assertIn("No outside AI service", self.chat)

if __name__ == '__main__':
    unittest.main()
