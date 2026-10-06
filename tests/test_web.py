import unittest
import json
import tempfile
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from snooze.web import authorized, safe_link, _make_server


class WebTests(unittest.TestCase):
    def test_same_origin_cookie_controls_do_not_require_pasting_secret(self):
        self.assertTrue(authorized({'Origin': 'http://localhost:8765', 'Cookie': 'snooze_control=ok'}, 'localhost:8765', 'ok'))
        self.assertFalse(authorized({'Origin': 'https://evil.test', 'Cookie': 'snooze_control=ok'}, 'localhost:8765', 'ok'))

    def test_cross_origin_and_missing_token_rejected(self):
        self.assertFalse(authorized({'Origin': 'https://evil.test', 'X-Snooze-Token': 'ok'}, 'localhost:8765', 'ok'))
        self.assertFalse(authorized({}, 'localhost:8765', 'ok'))
        self.assertTrue(authorized({'Origin': 'http://localhost:8765', 'X-Snooze-Token': 'ok'}, 'localhost:8765', 'ok'))

    def test_unsafe_links_rejected(self):
        self.assertIsNone(safe_link('javascript:alert(1)'))
        self.assertIsNone(safe_link('https://user:secret@example.org'))
        self.assertEqual(safe_link('https://app.lightsprint.ai'), 'https://app.lightsprint.ai')

    def test_private_v2_routes_require_auth_and_cookie_works_same_origin(self):
        with tempfile.TemporaryDirectory() as root:
            class Store:
                def snapshot(self, project):
                    return {'project': project, 'workers': [{'id': 't1', 'instruction': 'safe detail',
                            'state': 'running', 'observation': None}], 'incidents': [], 'settings': {'interval': 300}}
            server = _make_server(Store(), 'demo', None, 'secret', 0, {}, Path(root))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            host, port = server.server_address
            base = f'http://127.0.0.1:{port}'
            try:
                with self.assertRaises(HTTPError) as error:
                    urlopen(base + '/api/v2/state')
                self.assertEqual(error.exception.code, 403)
                with self.assertRaises(HTTPError) as error:
                    urlopen(base + '/api/v2/tasks/t1')
                self.assertEqual(error.exception.code, 403)
                request = Request(base + '/api/v2/state', headers={
                    'Origin': f'http://127.0.0.1:{port}', 'Cookie': 'snooze_control=secret'})
                with urlopen(request) as response:
                    self.assertEqual(json.load(response)['schema_version'], 2)
                request = Request(base + '/api/v2/tasks/t1', headers={
                    'Origin': f'http://127.0.0.1:{port}', 'Cookie': 'snooze_control=secret'})
                with urlopen(request) as response:
                    self.assertEqual(json.load(response)['instruction'], 'safe detail')
                with urlopen(base + '/api/health') as response:
                    self.assertEqual(json.load(response), {'name': 'snooze', 'api_version': 2, 'project': 'demo'})
            finally:
                server.shutdown(); server.server_close(); thread.join()

    def test_cross_origin_mutation_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            class Store:
                def snapshot(self, project): return {'project': project, 'workers': [], 'incidents': [], 'settings': {}}
            server = _make_server(Store(), 'demo', None, 'secret', 0, {}, Path(root))
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            host, port = server.server_address
            try:
                request = Request(f'http://127.0.0.1:{port}/api/check', data=b'{}', method='POST',
                                  headers={'Origin': 'http://evil.test', 'X-Snooze-Token': 'secret'})
                with self.assertRaises(HTTPError) as error: urlopen(request)
                self.assertEqual(error.exception.code, 403)
            finally:
                server.shutdown(); server.server_close(); thread.join()

    def test_static_paths_are_confined_and_mime_is_correct(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as outside:
            root, outside = Path(root), Path(outside)
            (root / 'assets').mkdir()
            (root / 'assets' / 'app.abc123.js').write_text('console.log(1)')
            (outside / 'secret.txt').write_text('private marker')
            (root / 'escape').symlink_to(outside / 'secret.txt')
            class Store:
                def snapshot(self, project): return {'project': project, 'workers': [], 'incidents': [], 'settings': {}}
            server = _make_server(Store(), 'demo', None, 'secret', 0, {}, root)
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            host, port = server.server_address; base = f'http://127.0.0.1:{port}'
            try:
                with urlopen(base + '/assets/app.abc123.js') as response:
                    self.assertIn('javascript', response.headers['Content-Type'])
                    self.assertEqual(response.read(), b'console.log(1)')
                for path in ('/%2e%2e/secret.txt', '/escape', '/missing.js'):
                    with self.assertRaises(HTTPError) as error: urlopen(base + path)
                    self.assertEqual(error.exception.code, 404)
            finally:
                server.shutdown(); server.server_close(); thread.join()
