import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from snooze.transport import LightSprint
from snooze.transport import normalize_status


class TransportTests(unittest.TestCase):
    def test_progress_age_and_liveness_are_safe_observed_fields(self):
        value=normalize_status({'status':{'sessionStatus':'running','relayHealth':{'alive':True,'lastEventAgoMs':900000,'relayPid':42},'userId':'private'}})
        self.assertEqual(value['last_event_age_ms'],900000)
        self.assertIs(value['relay_alive'],True)
        self.assertNotIn('relayPid',str(value))

    def test_nested_provider_status_is_flattened_without_sensitive_fields(self):
        value = normalize_status({'status': {'sessionStatus': 'idle', 'model': 'small', 'userId': 'private', 'credentialRef': 'private'}})
        self.assertEqual(value['status'], 'idle')
        self.assertEqual(value['model'], 'small')
        self.assertNotIn('private', str(value))

    def test_provider_compatible_user_agent_is_sent(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'config.toml'
            path.write_text('[mcp_servers.demo]\nurl="https://app.lightsprint.ai/mcp"\n')
            class Response:
                headers = {}; status = 200
                def __enter__(self): return self
                def __exit__(self, *args): pass
                def read(self): return b'{"result":{"content":[{"type":"text","text":"{}"}]}}'
            def open_request(request, timeout):
                self.assertEqual(request.get_header('User-agent'), 'Codex MCP')
                return Response()
            with patch('urllib.request.urlopen', side_effect=open_request):
                LightSprint(path).request('demo', 'GET', '/api/repos')
