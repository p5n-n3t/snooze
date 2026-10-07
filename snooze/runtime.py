"""One durable owner, observation + approved scheduler + quiet incident delivery."""
import json
import threading
import time
import tomllib
import uuid
from pathlib import Path
from snooze.control import Control
from snooze.credentials import CredentialStore
from snooze.legacy import read_queue
from snooze.monitor import Monitor
from snooze.notifications import NotificationChannels
from snooze.outbox import Outbox
from snooze.providers import ProviderRegistry
from snooze.scheduler import Scheduler
from snooze.store import Store
from snooze.tasks import TaskRepository
from snooze.transport import LightSprint
from snooze.validation import ValidatorRegistry


ALERT_STATES = {'idle','failed','unavailable','ownership_unknown','unknown'}


class Runtime:
    def __init__(self, state, config, observe=None):
        self.state = Path(state); self.config = config
        self.project = config.get('project_id', config['project'])
        self.store = Store(self.state / 'state.sqlite')
        self.repo = TaskRepository(self.store.path)
        self.repo.register_project(self.project, config['repo'], config.get('remote'))
        self.transport = LightSprint(Path(config['config_path']))
        from snooze.artifacts import GitHubArtifacts
        credentials = CredentialStore(self.state / 'credentials.json')
        self.registry = ProviderRegistry(self.repo, self.transport, GitHubArtifacts(credentials))
        self.scheduler = Scheduler(self.repo, self.registry, ValidatorRegistry())
        self.control = Control(self.repo, self.registry, self.scheduler)
        self.monitor = Monitor(self.store, observe or self.transport.observe)
        self.channels = NotificationChannels(config.get('notifications',{}), config.get('approved_commands',()), credentials=credentials)
        self.outbox = Outbox(self.repo, self.channels.deliver)
        self.lock = threading.Lock(); self.stopped = threading.Event()
        with self.repo.connection(True) as c:
            c.execute('CREATE TABLE IF NOT EXISTS incident_episodes(project TEXT,job TEXT,kind TEXT,incident TEXT,PRIMARY KEY(project,job))')
        # Preserve preview cadence without pretending its pause flag controlled an external dispatcher.
        if self.scheduler.settings(self.project)['revision'] == 0:
            self.scheduler.configure(self.project, {'interval': self.store.settings(self.project)['interval']}, 'preview-migration')
        self.discover_accounts()
        self.import_queue()

    def discover_accounts(self):
        path = Path(self.config['config_path'])
        if not path.is_file(): return
        servers = tomllib.loads(path.read_text()).get('mcp_servers',{})
        for key, value in servers.items():
            if value.get('url') != 'https://app.lightsprint.ai/mcp' or value.get('enabled') is False: continue
            if self.registry.get(key): continue
            self.registry.upsert_public_config(key, {'mcp_key':key,'label':key,'enabled':False}, trusted=True)

    def import_queue(self):
        queue = self.config.get('queue')
        if not queue: return
        jobs = read_queue(Path(queue))
        for job in jobs:
            job['server_key'] = self.config.get('ownership',{}).get(job.get('workspace_id'))
        self.store.ingest_jobs(self.project,jobs)

    def interval(self): return self.scheduler.settings(self.project)['interval']

    def _bridge_incidents(self, now):
        workers = self.store.snapshot(self.project)['workers']
        for attempt in self.repo.active(self.project):
            with self.repo.connection() as c:
                observed=c.execute('SELECT at,data FROM events WHERE attempt=? AND kind="provider_observed" ORDER BY id DESC LIMIT 1',(attempt['id'],)).fetchone()
            observation=json.loads(observed['data']) if observed else {}
            if attempt['state'] in ('blocked','ambiguous'):
                observation={'status':'failed' if attempt['state']=='blocked' else 'ownership_unknown'}
            workers.append({'id':'attempt:'+attempt['id'],'session_id':attempt['session'],'server_key':attempt['account'],
                            'observation':observation,'observed_at':observed['at'] if observed else None,'task_id':attempt['task']})
        for job in workers:
            kind = (job.get('observation') or {}).get('status')
            kind = kind if kind in ALERT_STATES else None
            with self.repo.connection(True) as c:
                old = c.execute('SELECT * FROM incident_episodes WHERE project=? AND job=?',(self.project,job['id'])).fetchone()
                if old and old['kind'] == kind: continue
                if old and old['incident']:
                    c.execute('UPDATE outbox SET resolved=1 WHERE incident=?',(old['incident'],))
                    self.repo.event(c,self.project,'incident_resolved',{'kind':old['kind'],'verified_state':kind or 'active'},job['id'],now=now)
                incident = uuid.uuid4().hex if kind else None
                c.execute('INSERT INTO incident_episodes VALUES(?,?,?,?) ON CONFLICT(project,job) DO UPDATE SET kind=excluded.kind,incident=excluded.incident',(self.project,job['id'],kind,incident))
            if incident:
                payload = {'project':self.project,'task':job.get('task_id',job['id']),'account':job.get('server_key'),'session':job.get('session_id'),
                           'kind':kind,'observed_at':job.get('observed_at'),'message':f'Worker is {kind}; saved output must be checked before reassignment.',
                           'suggested_next_step':'Inspect task, artifacts and ownership; reconcile before retry.'}
                channels = list(self.config.get('notifications',{})) or ['inbox']
                for channel in channels: self.outbox.enqueue(incident,channel,payload,now)

    def check(self, project):
        if project != self.project: raise ValueError('Project outside runtime scope')
        if not self.lock.acquire(False): raise RuntimeError('Check already running')
        started = time.time()
        try:
            self.import_queue()
            with self.repo.connection(True) as c: self.repo.event(c,project,'monitor_started',{},now=started)
            result = self.monitor.check(project)
            report = self.scheduler.tick(project)
            self._bridge_incidents(time.time()); receipts = self.outbox.deliver_due(time.time())
            finished = time.time()
            with self.repo.connection(True) as c:
                self.repo.event(c,project,'monitor_finished',{'checked':result['checked'],'started_at':started,'finished_at':finished},now=finished)
            return {**result,'started_at':started,'finished_at':finished,'scheduler_decisions':len(report.decisions),'deliveries':len(receipts)}
        finally: self.lock.release()

    def run(self):
        while not self.stopped.is_set():
            self.scheduler.wake.clear()
            try: self.check(self.project)
            except Exception as exc:
                with self.repo.connection(True) as c: self.repo.event(c,self.project,'monitor_error',{'error_kind':type(exc).__name__},now=time.time())
            self.scheduler.wake.wait(self.interval())

    def stop(self):
        self.stopped.set(); self.scheduler.wake.set()
