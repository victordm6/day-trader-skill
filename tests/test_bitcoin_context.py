import datetime as dt
from pathlib import Path
import sys
import unittest
import io
import json
from unittest.mock import patch
from contextlib import redirect_stdout
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'trader-bitcoin'/'scripts'))
import context as c
import suite

class MacroContextTests(unittest.TestCase):
    def test_both_adapters_route_context_without_inventing_calendar(self):
        for module in ('news','analyst'):
            with patch.object(sys,'argv',['suite.py',module,'--context']),patch.object(c.market,'snapshot',return_value={'close':80000}),redirect_stdout(io.StringIO()) as output:
                suite.main()
            result=json.loads(output.getvalue())
            self.assertEqual(result['calendar']['status'],'unavailable')
            self.assertEqual(result['price']['close'],80000)
            self.assertEqual(result['decision_effect'],'context_only')
    def test_price_failure_is_explicit(self):
        with patch.object(sys,'argv',['context.py']),patch.object(c.market,'snapshot',side_effect=ValueError('network')),redirect_stdout(io.StringIO()) as output:
            c.main()
        result=json.loads(output.getvalue())
        self.assertEqual(result['price']['status'],'unavailable')
        self.assertEqual(result['execution'],'disabled')
    def setUp(self):
        self.now=dt.datetime(2026,10,25,15,tzinfo=dt.timezone.utc)
        self.observation={'source_url':c.SOURCE,'observed_at':'2026-10-25T11:59:00-03:00',
            'coverage_start':'2026-10-25T00:00:00-03:00','coverage_end':'2026-10-26T00:00:00-03:00','coverage_complete':True,
            'events':[{'title':'Synthetic release','scheduled_at':'2026-10-25T12:30:00-03:00','importance':'high','currency':'USD','country':'US','actual':None,'forecast':'1','previous':'2'}]}
    def test_offset_conversion_and_upcoming_risk(self):
        r=c.calendar_context(self.observation,self.now)
        self.assertEqual(r['status'],'observed'); self.assertEqual(r['events'][0]['minutes_until'],30)
        self.assertEqual(r['upcoming_usd_high_impact_count'],1)
    def test_missing_calendar_is_not_no_events(self):
        self.assertEqual(c.calendar_context(None,self.now)['status'],'unavailable')
    def test_stale_or_future_observation(self):
        for time in ('2026-10-25T14:00:00Z','2026-10-25T16:00:00Z'):
            self.assertEqual(c.calendar_context(dict(self.observation,observed_at=time),self.now)['status'],'unavailable')
    def test_unknown_event_time_or_importance_marks_partial(self):
        for changes in ({'scheduled_at':None},{'importance':'unknown'}):
            data=dict(self.observation,events=[dict(self.observation['events'][0],**changes)])
            self.assertEqual(c.calendar_context(data,self.now)['status'],'partial')
    def test_naive_time_and_bad_source_rejected(self):
        for changes in ({'observed_at':'2026-10-25T15:00:00'},{'source_url':'https://example.org'}):
            with self.assertRaises(ValueError):c.calendar_context(dict(self.observation,**changes),self.now)
    def test_incomplete_coverage_or_outside_coverage(self):
        self.assertEqual(c.calendar_context(dict(self.observation,coverage_complete=False),self.now)['status'],'partial')
        with self.assertRaises(ValueError):c.calendar_context(dict(self.observation,coverage_end='2026-10-25T15:10:00Z'),self.now)

if __name__=='__main__':unittest.main()
