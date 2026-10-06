"""Small durable store. Queue history is imported, never rewritten."""
import json
import sqlite3
import time
from pathlib import Path
from snooze.transport import normalize_status


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            self.close()


class Store:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as c:
            c.executescript('''
              CREATE TABLE IF NOT EXISTS jobs(project TEXT,id TEXT,session TEXT,data TEXT,PRIMARY KEY(project,id));
              CREATE TABLE IF NOT EXISTS observations(session TEXT,at REAL,data TEXT);
              CREATE TABLE IF NOT EXISTS incidents(project TEXT,job TEXT,kind TEXT,message TEXT,at REAL,acked INTEGER DEFAULT 0,PRIMARY KEY(project,job,kind));
              CREATE TABLE IF NOT EXISTS settings(project TEXT PRIMARY KEY,data TEXT);
            ''')

    def connect(self):
        return sqlite3.connect(self.path, timeout=10, factory=ClosingConnection)

    def ingest_jobs(self, project_id: str, jobs: list[dict]) -> None:
        with self.connect() as c:
            for job in jobs:
                c.execute('INSERT INTO jobs VALUES(?,?,?,?) ON CONFLICT(project,id) DO UPDATE SET session=excluded.session,data=excluded.data',
                          (project_id, job['id'], job.get('session_id', ''), json.dumps(job)))

    def observe(self, session_id: str, observation: dict) -> None:
        observation = normalize_status(observation)
        with self.connect() as c:
            c.execute('INSERT INTO observations VALUES(?,?,?)', (session_id, time.time(), json.dumps(observation)))

    def incident(self, project, job, kind, message):
        with self.connect() as c:
            c.execute('INSERT INTO incidents VALUES(?,?,?,?,?,0) ON CONFLICT(project,job,kind) DO UPDATE SET message=excluded.message,at=excluded.at',
                      (project, job, kind, message, time.time()))

    def ack(self, project, job, kind):
        with self.connect() as c:
            c.execute('UPDATE incidents SET acked=1 WHERE project=? AND job=? AND kind=?', (project, job, kind))

    def retire_other_incidents(self, project, job, current_kind):
        with self.connect() as c:
            c.execute('UPDATE incidents SET acked=1 WHERE project=? AND job=? AND kind != ?', (project, job, current_kind))

    def settings(self, project):
        with self.connect() as c:
            row = c.execute('SELECT data FROM settings WHERE project=?', (project,)).fetchone()
        return json.loads(row[0]) if row else {'interval': 300, 'pause_dispatch': True}

    def set_settings(self, project, values):
        if not isinstance(values.get('interval', 300), int) or values.get('interval', 300) < 30:
            raise ValueError('Interval must be at least 30 seconds')
        with self.connect() as c:
            c.execute('INSERT INTO settings VALUES(?,?) ON CONFLICT(project) DO UPDATE SET data=excluded.data', (project, json.dumps(values)))

    def snapshot(self, project_id: str) -> dict:
        workers = []
        with self.connect() as c:
            for session, data in c.execute('SELECT session,data FROM jobs WHERE project=? ORDER BY id', (project_id,)):
                job = json.loads(data)
                row = c.execute('SELECT at,data FROM observations WHERE session=? ORDER BY rowid DESC LIMIT 1', (session,)).fetchone()
                job['observation'] = normalize_status(json.loads(row[1])) if row else None
                job['observed_at'] = row[0] if row else None
                job['observation_status'] = ('fresh' if time.time() - row[0] < 600 else 'stale') if row else 'unobserved'
                workers.append(job)
            incidents = [dict(zip(('job', 'kind', 'message', 'at'), r)) for r in c.execute('SELECT job,kind,message,at FROM incidents WHERE project=? AND acked=0', (project_id,))]
        return {'project': project_id, 'workers': workers, 'incidents': incidents, 'settings': self.settings(project_id)}
