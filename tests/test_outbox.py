import tempfile
import unittest
from pathlib import Path
from snooze.tasks import TaskRepository
from snooze.outbox import Outbox


class OutboxTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.repo=TaskRepository(Path(self.tmp.name)/'s.sqlite')
    def test_accepted_delivery_is_not_acknowledged(self):
        box=Outbox(self.repo,lambda channel,payload:{'state':'accepted'})
        id=box.enqueue('incident-1','test',{'project':'p','task':'t','Authorization':'secret'},100)
        receipt=box.deliver_due(100)[0]
        self.assertEqual(receipt.state,'accepted');self.assertIsNone(receipt.acknowledged_at)
        self.assertNotIn('Authorization',str(box.list('p')))
        box.register_coordinator('coord',['p'])
        self.assertTrue(box.acknowledge(id,'coord'))
        self.assertEqual(box.list('p')[0]['state'],'acknowledged')
        self.assertFalse(box.list('p')[0]['resolved'])
    def test_restart_and_recurring_incident_deduplicate(self):
        first=Outbox(self.repo); id=first.enqueue('same','inbox',{'project':'p','message':'Failed'},100)
        restarted=Outbox(TaskRepository(self.repo.path))
        self.assertEqual(restarted.enqueue('same','inbox',{'project':'p','message':'Still failed'},101),id)
        self.assertEqual(len(restarted.list('p')),1)
        self.assertFalse(restarted.acknowledge(id,'unregistered'))
    def test_failed_delivery_has_bounded_persisted_backoff(self):
        calls=[]
        def fail(channel,payload):calls.append(1);raise TimeoutError()
        box=Outbox(self.repo,fail);box.enqueue('i','test',{'project':'p'},100)
        box.deliver_due(100);box.deliver_due(101)
        self.assertEqual(len(calls),1)
        Outbox(TaskRepository(self.repo.path),fail).deliver_due(200)
        box.deliver_due(500);box.deliver_due(1000)
        self.assertEqual(len(calls),3)
        self.assertEqual(box.list('p')[0]['state'],'failed')
