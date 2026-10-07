import tempfile
import unittest
from pathlib import Path
from snooze.cli import prime
from snooze.runtime import Runtime


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name) / 'state'; self.folder = Path(self.tmp.name) / 'repo'; self.folder.mkdir()
        self.config = prime(self.folder, self.state, None)
        self.config['config_path'] = str(Path(self.tmp.name) / 'missing.toml')

    def test_runtime_is_external_by_default_and_records_actual_checks(self):
        runtime = Runtime(self.state, self.config, observe=lambda job: {'status':'running'})
        result = runtime.check(runtime.project)
        self.assertEqual(runtime.repo.project(runtime.project)['executor'], 'external-managed')
        with runtime.repo.connection() as c:
            kinds = [r['kind'] for r in c.execute('SELECT kind FROM events WHERE project=?', (runtime.project,))]
        self.assertIn('monitor_finished', kinds)
        self.assertGreaterEqual(result['finished_at'], result['started_at'])
        self.assertEqual(result['checked'], 0)

    def test_repeated_incident_is_quiet_and_state_change_can_reopen_it(self):
        status = ['failed']
        runtime = Runtime(self.state, self.config, observe=lambda job: {'status':status[0]})
        runtime.store.ingest_jobs(runtime.project, [{'id':'job','session_id':'session'}])
        runtime.check(runtime.project); runtime.check(runtime.project)
        self.assertEqual(len(runtime.outbox.list(runtime.project)), 1)
        self.assertEqual(runtime.outbox.list(runtime.project)[0]['state'], 'inbox')
        status[0] = 'running'; runtime.check(runtime.project)
        self.assertTrue(runtime.outbox.list(runtime.project)[0]['resolved'])
        status[0] = 'failed'; runtime.check(runtime.project)
        self.assertEqual(len(runtime.outbox.list(runtime.project)), 2)

    def test_polling_interval_is_policy_backed_and_wakeable(self):
        runtime = Runtime(self.state, self.config, observe=lambda job: {})
        self.assertEqual(runtime.interval(), 300)
        runtime.scheduler.configure(runtime.project, {'interval':30})
        self.assertEqual(runtime.interval(), 30)
        self.assertTrue(runtime.scheduler.wake.is_set())
