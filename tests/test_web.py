import unittest
from snooze.web import authorized, safe_link


class WebTests(unittest.TestCase):
    def test_cross_origin_and_missing_token_rejected(self):
        self.assertFalse(authorized({'Origin': 'https://evil.test', 'X-Snooze-Token': 'ok'}, 'localhost:8765', 'ok'))
        self.assertFalse(authorized({}, 'localhost:8765', 'ok'))
        self.assertTrue(authorized({'Origin': 'http://localhost:8765', 'X-Snooze-Token': 'ok'}, 'localhost:8765', 'ok'))

    def test_unsafe_links_rejected(self):
        self.assertIsNone(safe_link('javascript:alert(1)'))
        self.assertIsNone(safe_link('https://user:secret@example.org'))
        self.assertEqual(safe_link('https://app.lightsprint.ai'), 'https://app.lightsprint.ai')
