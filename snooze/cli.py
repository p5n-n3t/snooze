"""Small local CLI; no external model calls needed to monitor."""
import argparse
import fcntl
import json
import os
import secrets
import threading
import time
import webbrowser
from pathlib import Path
from snooze.legacy import read_queue
from snooze.store import Store
from snooze.monitor import Monitor
from snooze.transport import LightSprint


def prime(repo, state, queue):
    repo = Path(repo).resolve(strict=True)
    state = Path(state)
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    config = {'repo': str(repo), 'queue': str(Path(queue).resolve()) if queue else None,
              'project': repo.name, 'ownership': {}, 'config_path': str(Path.home() / '.codex/config.toml')}
    (state / 'project.json').write_text(json.dumps(config, indent=2))
    token_path = state / 'control-token'
    if not token_path.exists():
        fd = os.open(token_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as f:
            f.write(secrets.token_urlsafe(32))
    return config


def main():
    parser = argparse.ArgumentParser(description='Snooze — honest worker visibility')
    parser.add_argument('--state', type=Path, default=Path.home() / '.local/state/snooze')
    subs = parser.add_subparsers(dest='command', required=True)
    init = subs.add_parser('init'); init.add_argument('--repo', type=Path, required=True); init.add_argument('--queue', type=Path)
    server = subs.add_parser('serve'); server.add_argument('--open', action='store_true'); server.add_argument('--port', type=int, default=8765)
    for command in ('status', 'incidents', 'check', 'config'):
        subs.add_parser(command)
    args = parser.parse_args()
    state = args.state
    if args.command == 'init':
        print(json.dumps(prime(args.repo, state, args.queue), indent=2)); return
    config = json.loads((state / 'project.json').read_text())
    store = Store(state / 'state.sqlite')
    project = config['project']
    def import_queue():
        if config['queue']:
            jobs = read_queue(Path(config['queue']))
            for job in jobs:
                job['server_key'] = config.get('ownership', {}).get(job.get('workspace_id'))
            store.ingest_jobs(project, jobs)
    import_queue()
    monitor = Monitor(store, LightSprint(Path(config['config_path'])).observe)
    if args.command in ('status', 'incidents', 'config'):
        result = store.snapshot(project)
        if args.command == 'incidents': result = result['incidents']
        if args.command == 'config': result = config
        print(json.dumps(result, indent=2)); return
    with (state / 'daemon.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error('A Snooze process already owns this state; use dashboard Check now')
        if args.command == 'check':
            print(json.dumps(monitor.check(project))); return
        def loop():
            while True:
                try:
                    import_queue()
                    result = monitor.check(project)
                    print(json.dumps(result), flush=True)
                except Exception as exc:
                    store.incident(project, 'monitor', 'cycle_error', type(exc).__name__)
                time.sleep(store.settings(project)['interval'])
        threading.Thread(target=loop, daemon=True).start()
        if args.open:
            webbrowser.open(f'http://127.0.0.1:{args.port}')
        from snooze.web import serve
        serve(store, project, monitor, (state / 'control-token').read_text(), args.port)
