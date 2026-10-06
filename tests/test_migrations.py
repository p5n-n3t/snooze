import sqlite3
import tempfile
import unittest
from pathlib import Path
from snooze.store import Store
from snooze.migrations import migrate_state


class MigrationTests(unittest.TestCase):
    def test_backup_retains_preview_history_and_replay_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'state.sqlite'
            store = Store(path)
            store.ingest_jobs('p', [{'id': 'a', 'session_id': 's'}])
            store.observe('s', {'status': 'idle'})
            store.incident('p', 'a', 'idle', 'No result')
            first = migrate_state(path)
            self.assertTrue(first.backup_path.exists())
            with sqlite3.connect(first.backup_path) as c:
                self.assertEqual(c.execute('SELECT COUNT(*) FROM jobs').fetchone()[0], 1)
                self.assertEqual(c.execute('SELECT COUNT(*) FROM observations').fetchone()[0], 1)
                self.assertEqual(c.execute('SELECT COUNT(*) FROM incidents').fetchone()[0], 1)
            second = migrate_state(path)
            self.assertFalse(second.changed)
            self.assertEqual(Store(path).snapshot('p')['workers'][0]['id'], 'a')

    def test_failed_migration_rolls_back(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'state.sqlite'
            store = Store(path); store.ingest_jobs('p', [{'id': 'a'}])
            def fail(connection):
                connection.execute('CREATE TABLE must_not_persist(x)')
                raise RuntimeError('fixture failure')
            with self.assertRaises(RuntimeError): migrate_state(path, before_commit=fail)
            with sqlite3.connect(path) as c:
                self.assertIsNone(c.execute("SELECT name FROM sqlite_master WHERE name='must_not_persist'").fetchone())
            self.assertEqual(Store(path).snapshot('p')['workers'][0]['id'], 'a')
