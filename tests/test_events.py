import tempfile
import unittest
from pathlib import Path
from snooze.tasks import TaskRepository
from snooze.events import EventFeed


class EventTests(unittest.TestCase):
    def test_cursor_pagination_is_project_scoped_and_allowlisted(self):
        with tempfile.TemporaryDirectory() as d:
            repo=TaskRepository(Path(d)/'s.sqlite')
            with repo.connection(True) as c:
                repo.event(c,'p','incident',{'message':'A','Authorization':'must-not-export'})
                repo.event(c,'q','incident',{'message':'Other project'})
                repo.event(c,'p','incident',{'message':'B'})
            feed=EventFeed(repo)
            first=feed.read('p',after=0,limit=1)
            self.assertEqual(len(first['events']),1)
            self.assertNotIn('Authorization',str(first))
            second=feed.read('p',after=first['cursor'],limit=1)
            self.assertEqual(second['events'][0]['data']['message'],'B')
            self.assertEqual(feed.read('p',after=second['cursor'])['events'],[])
