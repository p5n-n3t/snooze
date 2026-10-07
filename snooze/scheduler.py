"""Durable, deterministic scheduler. Routine cycles use no reasoning-model calls."""
import json
import threading
import time
import uuid
from collections import Counter
from dataclasses import asdict
from snooze.domain import CycleReport
from snooze.policy import Policy, DEFAULTS
from snooze.adapters.base import UnsupportedOperation


class Scheduler:
    def __init__(self, repository, registry, validators, clock=time.time):
        self.repo=repository; self.registry=registry; self.validators=validators; self.clock=clock
        self.lock=threading.Lock(); self.wake=threading.Event()

    def settings(self, project):
        with self.repo.connection() as c:
            row=c.execute('SELECT * FROM policy_settings WHERE project=?',(project,)).fetchone()
        return {**DEFAULTS,**(json.loads(row['data']) if row else {}),'revision':row['revision'] if row else 0}

    def configure(self, project, values, actor='operator', expected_revision=None):
        if set(values)-set(DEFAULTS): raise ValueError('Unknown policy setting')
        with self.repo.connection(True) as c:
            row=c.execute('SELECT * FROM policy_settings WHERE project=?',(project,)).fetchone()
            revision=row['revision'] if row else 0
            if expected_revision is not None and expected_revision != revision: raise ValueError('Stale revision')
            settings={**DEFAULTS,**(json.loads(row['data']) if row else {}),**values}
            for key in ('interval','max_concurrent','global_concurrent','max_recoveries','backoff_seconds','native_ceiling'):
                minimum=30 if key=='interval' else (0 if key in ('max_recoveries','native_ceiling') else 1)
                if type(settings[key]) is not int or not minimum<=settings[key]<=86400: raise ValueError('Invalid '+key)
            for key in ('pause_dispatch','emergency_stop','allow_unknown_quota','allow_native'):
                if type(settings[key]) is not bool: raise ValueError('Invalid '+key)
            if settings['max_recoveries'] > 2: raise ValueError('Maximum two recoveries')
            if settings['reserve'] < 0: raise ValueError('Reserve must be nonnegative')
            if settings['mode'] not in ('conservative','balanced','custom'): raise ValueError('Unknown preset')
            if not isinstance(settings['model_limits'],dict) or any(type(v) is not int or v<1 for v in settings['model_limits'].values()): raise ValueError('Invalid model limits')
            revision+=1
            c.execute('INSERT INTO policy_settings VALUES(?,?,?) ON CONFLICT(project) DO UPDATE SET revision=excluded.revision,data=excluded.data',(project,revision,json.dumps(settings)))
            c.execute('INSERT INTO settings_revisions(project,revision,actor,at,data) VALUES(?,?,?,?,?)',(project,revision,actor,self.clock(),json.dumps(settings)))
            self.repo.event(c,project,'policy_configured',{'revision':revision,'actor':actor},now=self.clock())
        self.wake.set(); return {**settings,'revision':revision}

    def _record(self, project, kind, payload, task=None, attempt=None, now=None):
        with self.repo.connection(True) as c: self.repo.event(c,project,kind,payload,task,attempt,now)

    def _validate(self, attempt, artifact, now):
        spec=self.repo.spec(attempt['task']); result=self.validators.validate(spec,artifact)
        accepted=self.repo.record_artifact(attempt['id'],attempt['generation'],artifact)
        with self.repo.connection(True) as c:
            c.execute('INSERT INTO validations VALUES(?,?,?,?,?)',(uuid.uuid4().hex,attempt['id'],result.state,json.dumps(asdict(result)),now))
        if accepted=='accepted' and result.state=='valid':
            self.repo.update_attempt(attempt['id'],'complete',data={'validation':'valid','artifact_hash':result.artifact_hash},now=now)
            self.repo.release(attempt['id'],{'validated':True})
            return {'task':spec.id,'action':'validated_complete'}
        self.repo.update_attempt(attempt['id'],'blocked',data={'validation':'invalid','errors':list(result.errors)},now=now)
        return {'task':spec.id,'action':'validation_failed'}

    def _recover(self, attempt, adapter, status, settings, now):
        if settings['pause_dispatch'] or settings['emergency_stop']: return 'recovery_paused'
        data=attempt['data']; count=data.get('recovery_count',0)
        if now < data.get('recovery_due',0): return 'recovery_backoff'
        if count>=settings['max_recoveries']:
            self.repo.update_attempt(attempt['id'],'blocked',data={'reason':'Recovery limit exhausted'},now=now)
            return 'recovery_exhausted'
        if not adapter.capabilities().get('resume',{}).get('supported'): return 'resume_unsupported'
        next_data={'recovery_count':count+1,'recovery_due':now+settings['backoff_seconds']*(2**count)}
        # Persist the bound before network I/O; a crash cannot reset the budget.
        self.repo.update_attempt(attempt['id'],'awaiting_output',data=next_data,now=now)
        task=self.repo.get(attempt['task'])
        try:
            adapter.resume(attempt['session'],{**attempt,'instructions':task['instructions']})
            return 'resume_requested'
        except Exception:
            self.repo.update_attempt(attempt['id'],'ambiguous',data={'reason':'Resume acceptance uncertain'},now=now)
            return 'resume_ambiguous'

    def tick(self, project_id, now=None, *, manual=False, override_pause=False, only_task=None):
        now=self.clock() if now is None else now
        if not self.lock.acquire(False): return CycleReport(now,self.clock(),[],[{'kind':'cycle_running'}])
        decisions=[]; errors=[]
        try:
            settings=self.settings(project_id); project=self.repo.project(project_id)
            owner=project['executor'] if project else 'external-managed'
            managed=owner=='snooze'
            self._record(project_id,'cycle_started',{},now=now)
            for attempt in self.repo.active(project_id):
                try:
                    adapter=self.registry.adapter(attempt['account'])
                    if attempt['state']=='ambiguous' or (not attempt['session'] and attempt['state']!='reserved'):
                        receipt=adapter.reconcile(attempt) if adapter.capabilities().get('reconcile',{}).get('supported') else None
                        if receipt and receipt.get('session_id'):
                            self.repo.update_attempt(attempt['id'],'running',session=receipt['session_id'],now=now)
                        else: decisions.append({'task':attempt['task'],'action':'needs_reconciliation'})
                        continue
                    if not attempt['session']: continue
                    observation=adapter.observe(attempt['session'])
                    self._record(project_id,'provider_observed',{'account':attempt['account'],**{k:observation.get(k) for k in ('status','model','effort')}},attempt['task'],attempt['id'],now)
                    if attempt['state']=='cancel_pending':
                        if observation.get('status') in ('cancelled','canceled'):
                            self.repo.update_attempt(attempt['id'],'cancelled',now=now)
                            self.repo.release(attempt['id'],{'cancelled':True})
                            decisions.append({'task':attempt['task'],'action':'cancel_confirmed'})
                        else: decisions.append({'task':attempt['task'],'action':'awaiting_cancel_ack'})
                        continue
                    artifact=adapter.collect(attempt) if adapter.capabilities().get('collect',{}).get('supported') else None
                    if artifact is not None:
                        decisions.append(self._validate(attempt,artifact,now)); continue
                    status=observation.get('status','unknown')
                    if status in ('idle','failed','completed'):
                        action=self._recover(attempt,adapter,status,settings,now) if managed and status=='failed' and attempt['state']!='blocked' else 'awaiting_saved_output'
                        decisions.append({'task':attempt['task'],'action':action})
                except Exception as e:
                    errors.append({'task':attempt['task'],'account':attempt['account'],'kind':type(e).__name__})
            active=self.repo.active(project_id); counts=Counter(a['account'] for a in active)
            configs={a['id']:self.registry.get(a['id']) for a in self.registry.list_public()}
            with self.repo.connection() as c: global_count=c.execute('SELECT COUNT(*) FROM attempts WHERE released_at IS NULL').fetchone()[0]
            for task in self.repo.list(project_id):
                if only_task and task['id']!=only_task: continue
                if task['state'] not in ('queued','retry_due') or task['due_at']>now: continue
                spec=self.repo.spec(task['id'])
                if any(not self.repo.get(dep) or self.repo.get(dep)['state']!='complete' for dep in spec.dependencies):
                    decisions.append({'task':spec.id,'action':'dependency_blocked'}); continue
                policy=Policy(settings,counts,configs,len(active),global_count)
                eligible=[]; explanations=[]
                for id in configs:
                    result=policy.evaluate(spec,self.registry.snapshot(id,now),now)
                    if result.eligible: eligible.append((result.rank,id))
                    else: explanations.append({'account':id,'reasons':list(result.reasons)})
                if not managed or settings['emergency_stop'] or (settings['pause_dispatch'] and not (manual and override_pause)):
                    decisions.append({'task':spec.id,'action':'shadow' if not managed else 'dispatch_stopped','routes':explanations}); continue
                if not eligible:
                    decisions.append({'task':spec.id,'action':'no_eligible_route','routes':explanations}); continue
                account=min(eligible)[1]
                try: receipt=self.repo.reserve(spec.id,account,spec.scope_keys,now,policy_revision=settings['revision'],override_pause=manual and override_pause)
                except ValueError as e:
                    decisions.append({'task':spec.id,'action':'reservation_conflict'}); continue
                attempt=self.repo.attempt(receipt.attempt_id)
                self.repo.update_attempt(receipt.attempt_id,'starting',data={'requested_model':spec.requirements.get('model'),'requested_effort':spec.requirements.get('effort','low')},now=now)
                try:
                    launched=self.registry.adapter(account).launch(spec,{**attempt,'instructions':task['instructions']})
                    if not launched.get('session_id'): raise TimeoutError('Missing receipt')
                    self.repo.update_attempt(receipt.attempt_id,'running',session=launched['session_id'],data=launched,now=now)
                    decisions.append({'task':spec.id,'action':'launched','account':account,'attempt':receipt.attempt_id})
                except Exception as e:
                    self.repo.update_attempt(receipt.attempt_id,'ambiguous',data={'reason':'Launch acceptance uncertain','error_kind':type(e).__name__},now=now)
                    errors.append({'task':spec.id,'account':account,'kind':'ambiguous_launch'})
                counts[account]+=1; active=self.repo.active(project_id); global_count+=1
            self._record(project_id,'cycle_finished',{'decisions':decisions,'errors':errors},now=now)
            return CycleReport(now,self.clock(),decisions,errors)
        finally: self.lock.release()
