import tempfile
import unittest
from pathlib import Path
from snooze.store import Store


class StoreTests(unittest.TestCase):
    def test_import_is_idempotent_and_stale_until_observed(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'state.db'
            s = Store(path)
            jobs = [{'id': 'one', 'session_id': 's1', 'state': 'running', 'requested_model': 'small'}]
            s.ingest_jobs('p', jobs)
            s.ingest_jobs('p', jobs)
            state = s.snapshot('p')
            self.assertEqual(len(state['workers']), 1)
            self.assertEqual(state['workers'][0]['observation_status'], 'unobserved')
            s.observe('s1', {'status': 'idle', 'model': 'confirmed'})
            restored = Store(path).snapshot('p')['workers'][0]
            self.assertEqual(restored['requested_model'], 'small')
            self.assertEqual(restored['observation']['model'], 'confirmed')

    def test_incidents_deduplicate_and_acknowledge(self):
        with tempfile.TemporaryDirectory() as d:
            s = Store(Path(d) / 'state.db')
            s.incident('p', 'one', 'failed', 'Worker failed')
            s.incident('p', 'one', 'failed', 'Worker failed again')
            self.assertEqual(len(s.snapshot('p')['incidents']), 1)
            s.ack('p', 'one', 'failed')
            self.assertEqual(s.snapshot('p')['incidents'], [])
