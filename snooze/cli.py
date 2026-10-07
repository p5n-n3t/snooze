"""Small local CLI; no external model calls needed to monitor."""
import argparse
import fcntl
import json
import os
import secrets
import threading
import time
import webbrowser
import uuid
from pathlib import Path
from snooze.legacy import read_queue
from snooze.store import Store
from snooze.monitor import Monitor
from snooze.transport import LightSprint


def prime(repo, state, queue):
    repo = Path(repo).resolve(strict=True)
    state = Path(state)
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    if (state / 'project.json').exists():
        raise ValueError('Project is already initialised; use open, not init, to preserve ownership/history')
    config = {'repo': str(repo), 'queue': str(Path(queue).resolve()) if queue else None,
              'project': repo.name, 'project_id':uuid.uuid4().hex, 'ownership': {}, 'config_path': str(Path.home() / '.codex/config.toml')}
    (state / 'project.json').write_text(json.dumps(config, indent=2))
    token_path = state / 'control-token'
    if not token_path.exists():
        fd = os.open(token_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as f:
            f.write(secrets.token_urlsafe(32))
    return config


def main():
    from snooze.launch import default_state, open_dashboard
    parser = argparse.ArgumentParser(description='Snooze — honest worker visibility')
    parser.add_argument('--state', type=Path, default=default_state())
    subs = parser.add_subparsers(dest='command')
    init = subs.add_parser('init'); init.add_argument('--repo', type=Path, required=True); init.add_argument('--queue', type=Path)
    server = subs.add_parser('serve'); server.add_argument('--open', action='store_true'); server.add_argument('--port', type=int, default=8765)
    opener = subs.add_parser('open'); opener.add_argument('--port',type=int,default=8765); opener.add_argument('--no-browser',action='store_true')
    mcp = subs.add_parser('mcp')
    enqueue = subs.add_parser('enqueue');enqueue.add_argument('--file',type=Path,required=True);enqueue.add_argument('--approve',action='store_true')
    service = subs.add_parser('install-service');service.add_argument('--name',default='snooze.service');service.add_argument('--port',type=int,default=8765)
    for command in ('status', 'incidents', 'check', 'config'):
        subs.add_parser(command)
    args = parser.parse_args()
    state = args.state
    if args.command in (None,'open'):
        print(open_dashboard(state,getattr(args,'port',8765),webbrowser.open if not getattr(args,'no_browser',False) else lambda url:False)); return
    if args.command == 'init':
        print(json.dumps(prime(args.repo, state, args.queue), indent=2)); return
    config = json.loads((state / 'project.json').read_text())
    from snooze.runtime import Runtime
    runtime = Runtime(state,config)
    store = runtime.store; project = runtime.project
    if args.command == 'install-service':
        from snooze.service import install_service
        print(install_service(state,args.name,args.port));return
    if args.command == 'enqueue':
        from snooze.queueing import add_packet
        if args.file.stat().st_size>1024*1024:parser.error('Task packet exceeds 1 MiB')
        row=add_packet(runtime.repo,project,json.loads(args.file.read_text()),approved=args.approve)
        print(json.dumps({'id':row['id'],'state':row['state'],'approved':row['spec']['approved']}));return
    if args.command == 'mcp':
        import sys
        from snooze.mcp_server import MCPFacade
        MCPFacade(runtime.repo,runtime.control,(state / 'control-token').read_text(),[project]).serve_stdio(sys.stdin,sys.stdout); return
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
            print(json.dumps(runtime.check(project))); return
        threading.Thread(target=runtime.run, daemon=True).start()
        if args.open:
            webbrowser.open(f'http://127.0.0.1:{args.port}')
        from snooze.web import serve
        try:
            serve(store, project, runtime, (state / 'control-token').read_text(), args.port,project_config=config,control=runtime.control)
        finally: runtime.stop()
