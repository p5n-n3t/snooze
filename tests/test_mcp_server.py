import tempfile
import unittest
from pathlib import Path
from snooze.tasks import TaskRepository
from snooze.mcp_server import MCPFacade


class MCPTests(unittest.TestCase):
    def test_scope_and_auth_cannot_be_bypassed_by_tool_calls(self):
        with tempfile.TemporaryDirectory() as d:
            repo=TaskRepository(Path(d)/'s.sqlite')
            facade=MCPFacade(repo,None,'private',['p'])
            with self.assertRaises(PermissionError):facade.call('events',{'project':'p'},'wrong')
            with self.assertRaises(PermissionError):facade.call('events',{'project':'other'},'private')
            self.assertEqual(facade.call('events',{'project':'p'},'private')['events'],[])
            with self.assertRaises(ValueError):facade.call('shell',{'project':'p','command':'bad'},'private')
