import tempfile
import threading
import unittest
from pathlib import Path
from snooze.domain import TaskSpec
from snooze.tasks import TaskRepository
from snooze.providers import ProviderRegistry
from snooze.scheduler import Scheduler
from snooze.validation import ValidatorRegistry


class FakeAdapter:
    def __init__(self): self.launches=[]; self.resumes=[]; self.artifact=None; self.state='running'; self.timeout=False
    def capabilities(self): return {op:{'supported':True,'reason':None} for op in ('launch','observe','collect','resume','cancel','reconcile')}
    def launch(self, task, attempt):
        self.launches.append(attempt['idempotency_key'])
        if self.timeout: raise TimeoutError('Acceptance uncertain')
        return {'session_id':'session-'+task.id,'state':'running'}
    def observe(self, session): return {'status':self.state,'model':'small','effort':'low'}
    def collect(self, attempt): return self.artifact
    def reconcile(self, attempt): return None
    def resume(self, session, attempt): self.resumes.append(session); return {'state':'pending'}
    def cancel(self, session): return {'state':'pending'}


class SchedulerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.repo=TaskRepository(Path(self.tmp.name)/'s.sqlite'); self.repo.register_project('p','/p')
        self.registry=ProviderRegistry(self.repo)
        self.registry.upsert_public_config('a',{'adapter':'ssh','models':['small'],'efforts':['low'],'capacity':1,'health':'healthy','allow_unknown_quota':True},trusted=True)
        self.adapter=FakeAdapter(); self.registry.overrides['a']=self.adapter
        self.scheduler=Scheduler(self.repo,self.registry,ValidatorRegistry(),clock=lambda:100)
        self.scheduler.configure('p',{'pause_dispatch':False,'allow_unknown_quota':True})
        self.repo.set_executor('p','snooze',quiesced=True,reconciled=True)
    def add(self,id='t',scope='1'):
        self.repo.add(TaskSpec(id,'p',('record:'+scope,),'fixture','h',{'model':'small','effort':'low'},{'ids':[scope],'fields':['id']},'json-records',True),now=90)
    def test_idle_without_artifact_is_not_complete(self):
        self.add(); self.scheduler.tick('p',100); self.adapter.state='idle'; self.scheduler.tick('p',101)
        self.assertNotEqual(self.repo.get('t')['state'],'complete')
        self.assertEqual(len(self.adapter.launches),1)
    def test_valid_output_finishes_before_replacement(self):
        self.add(); self.add('u','2'); self.scheduler.tick('p',100)
        self.adapter.artifact={'records':[{'id':'1'}]}; self.adapter.state='idle'
        self.scheduler.tick('p',101)
        self.assertEqual(self.repo.get('t')['state'],'complete')
        self.assertEqual(len(self.adapter.launches),2)
    def test_timeout_stays_reserved_across_restart_no_duplicate_launch(self):
        self.add(); self.adapter.timeout=True; self.scheduler.tick('p',100)
        new=Scheduler(self.repo,self.registry,ValidatorRegistry())
        new.tick('p',10000)
        self.assertEqual(len(self.adapter.launches),1)
        self.assertEqual(self.repo.active('p')[0]['state'],'ambiguous')
    def test_pause_emergency_external_and_shadow_never_launch(self):
        self.add(); self.scheduler.configure('p',{'pause_dispatch':True}); self.scheduler.tick('p',100)
        self.assertEqual(self.adapter.launches,[])
        self.scheduler.configure('p',{'pause_dispatch':False,'emergency_stop':True}); self.scheduler.tick('p',101)
        self.assertEqual(self.adapter.launches,[])
        self.scheduler.configure('p',{'emergency_stop':False})
        for owner in ('external-managed','shadow'):
            self.repo.set_executor('p',owner); self.scheduler.tick('p',102)
            self.assertEqual(self.adapter.launches,[])
    def test_two_ticks_share_exclusive_reservation(self):
        self.add(); other=Scheduler(self.repo,self.registry,ValidatorRegistry())
        threads=[threading.Thread(target=s.tick,args=('p',100)) for s in (self.scheduler,other)]
        for t in threads:t.start()
        for t in threads:t.join()
        self.assertEqual(len(self.adapter.launches),1)
    def test_recoveries_have_persisted_backoff_and_stop_after_two(self):
        self.add(); self.scheduler.tick('p',100); self.adapter.state='failed'
        self.scheduler.tick('p',101); self.scheduler.tick('p',102)
        self.assertEqual(len(self.adapter.resumes),1)
        self.scheduler.tick('p',500); self.scheduler.tick('p',1000)
        self.assertEqual(len(self.adapter.resumes),2)
        self.assertEqual(self.repo.active('p')[0]['state'],'blocked')
