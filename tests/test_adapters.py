import unittest
from snooze.adapters.base import UnsupportedOperation
from snooze.adapters.registered import RegisteredAdapter
from snooze.adapters.lightsprint import LightSprintAdapter
from snooze.domain import TaskSpec, AttemptReceipt


class RecordingTransport:
    def __init__(self): self.calls = []
    def request(self, key, method, path, body=None):
        self.calls.append((key, method, path, body))
        if method == 'GET': return {'status': {'sessionStatus': 'idle', 'model': 'gpt-6-luna', 'privateMessages': ['secret']}}
        return {'id': 'session-1', 'status': 'running', 'branchName': 'ls/test'}


class AdapterTests(unittest.TestCase):
    def test_unsupported_launch_rejected_before_network(self):
        transport = RecordingTransport()
        adapter = LightSprintAdapter({'id': 'a', 'mcp_key': 'key'}, transport)
        with self.assertRaises(UnsupportedOperation): adapter.launch(None, None)
        self.assertEqual(transport.calls, [])

    def test_live_observation_fields_are_allowlisted(self):
        transport = RecordingTransport()
        adapter = LightSprintAdapter({'id': 'a', 'mcp_key': 'key'}, transport)
        result = adapter.observe('session-1')
        self.assertEqual(result['status'], 'idle')
        self.assertNotIn('privateMessages', result)
        with self.assertRaises(ValueError): adapter.observe('../../etc')

    def test_resume_is_pending_not_completed(self):
        transport = RecordingTransport()
        adapter = LightSprintAdapter({'id': 'a', 'mcp_key': 'key', 'verified_operations': ['resume', 'cancel']}, transport)
        result = adapter.resume('session-1', {'instructions': 'Continue the exact assignment'})
        self.assertEqual(result['state'], 'pending')
        self.assertEqual(transport.calls[0][2], '/api/agent-sessions/session-1/chat')
        self.assertEqual(adapter.cancel('session-1')['state'], 'pending')

    def test_future_registration_does_not_advertise_execution(self):
        adapter = RegisteredAdapter({'adapter': 'ssh'})
        self.assertFalse(adapter.capabilities()['launch']['supported'])
        with self.assertRaises(UnsupportedOperation): adapter.cancel('s')
