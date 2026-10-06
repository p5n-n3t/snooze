"""Additive SQLite migrations with a consistent, recoverable preview backup."""
import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MigrationReport:
    changed: bool
    version: int
    backup_path: Path | None


SCHEMA = (
    'CREATE TABLE IF NOT EXISTS schema_versions(version INTEGER PRIMARY KEY, at REAL)',
    'CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, folder TEXT, remote TEXT, executor TEXT NOT NULL DEFAULT "external-managed")',
    'CREATE TABLE IF NOT EXISTS project_aliases(alias TEXT PRIMARY KEY, project TEXT REFERENCES projects(id))',
    'CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY, project TEXT NOT NULL, spec TEXT NOT NULL, instructions TEXT NOT NULL, state TEXT NOT NULL, priority INTEGER DEFAULT 0, due_at REAL DEFAULT 0, created_at REAL, updated_at REAL, revision INTEGER DEFAULT 0)',
    'CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY, task TEXT NOT NULL, project TEXT NOT NULL, account TEXT NOT NULL, generation INTEGER NOT NULL, idempotency_key TEXT UNIQUE NOT NULL, session TEXT, state TEXT NOT NULL, scopes TEXT NOT NULL, started_at REAL, lease_until REAL, released_at REAL, recovery_count INTEGER DEFAULT 0, due_at REAL DEFAULT 0, data TEXT NOT NULL DEFAULT "{}")',
    'CREATE UNIQUE INDEX IF NOT EXISTS one_active_task ON attempts(task) WHERE released_at IS NULL',
    'CREATE INDEX IF NOT EXISTS active_project_attempts ON attempts(project,released_at)',
    'CREATE TABLE IF NOT EXISTS artifacts(id TEXT PRIMARY KEY, attempt TEXT NOT NULL, generation INTEGER, state TEXT NOT NULL, reference TEXT NOT NULL, at REAL)',
    'CREATE TABLE IF NOT EXISTS validations(id TEXT PRIMARY KEY, attempt TEXT NOT NULL, state TEXT NOT NULL, data TEXT NOT NULL, at REAL)',
    'CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT, project TEXT NOT NULL, task TEXT, attempt TEXT, kind TEXT NOT NULL, at REAL NOT NULL, data TEXT NOT NULL, source_id TEXT, source_event_id TEXT, UNIQUE(source_id,source_event_id))',
    'CREATE INDEX IF NOT EXISTS event_project_time ON events(project,at)',
    'CREATE TABLE IF NOT EXISTS provider_configs(id TEXT PRIMARY KEY, data TEXT NOT NULL, revision INTEGER DEFAULT 0)',
    'CREATE TABLE IF NOT EXISTS policy_settings(project TEXT PRIMARY KEY, revision INTEGER NOT NULL, data TEXT NOT NULL)',
    'CREATE TABLE IF NOT EXISTS settings_revisions(id INTEGER PRIMARY KEY AUTOINCREMENT, project TEXT NOT NULL, revision INTEGER NOT NULL, actor TEXT, at REAL, data TEXT NOT NULL)',
    'CREATE TABLE IF NOT EXISTS capability_snapshots(account TEXT, at REAL, data TEXT)',
)


def migrate_state(path: Path, before_commit=None) -> MigrationReport:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    backup_path = None
    try:
        exists = connection.execute("SELECT 1 FROM sqlite_master WHERE name='schema_versions'").fetchone()
        if exists and connection.execute('SELECT 1 FROM schema_versions WHERE version=1').fetchone():
            return MigrationReport(False, 1, None)
        # sqlite backup handles WAL and concurrent observations consistently.
        backup_path = path.with_name(path.name + '.pre-v1-backup')
        if not backup_path.exists():
            backup = sqlite3.connect(backup_path)
            try: connection.backup(backup)
            finally: backup.close()
            backup_path.chmod(0o600)
        connection.execute('PRAGMA journal_mode=WAL')
        connection.execute('BEGIN IMMEDIATE')
        for statement in SCHEMA: connection.execute(statement)
        if before_commit is not None: before_commit(connection)
        connection.execute('INSERT OR IGNORE INTO schema_versions VALUES(1,unixepoch())')
        connection.commit()
        path.chmod(0o600)
        return MigrationReport(True, 1, backup_path)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
