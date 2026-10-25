import datetime as dt
from pathlib import Path
import sys
import unittest
import io
import json
import tempfile
from unittest.mock import patch
from contextlib import redirect_stdout

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'trader-bitcoin'/'scripts'))
import decision as d
import workflow


class DecisionTests(unittest.TestCase):
    def test_malformed_evidence_blocks_instead_of_crashing(self):
        for report in ([1],dict(self.report(),uncertainty={'mean_per_trade_95pct_day_bootstrap':[]}),dict(self.report(),holdout={'trades':float('inf'),'mean':1}),dict(self.report(),uncertainty={'mean_per_trade_95pct_day_bootstrap':[.2,.1]})):
            with self.subTest(report=report):self.assertEqual(d.decide(self.snap(),report)['action'],'WAIT')

    def test_provisional_reference_is_not_an_actual_position(self):
        with self.assertRaises(ValueError):d.decide(self.snap(),None,dict(self.position(),reference_only=True))

    def test_nonfinite_observation_is_not_hold(self):
        with self.assertRaises(ValueError):d.decide(dict(self.snap(),close=float('nan')),None,self.position())

    def test_exit_cli_does_not_read_broken_entry_evidence(self):
        root=Path(__file__).resolve().parents[1]/'work'; root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as directory:
            p=Path(directory)/'position.json'; p.write_text(json.dumps(self.position()))
            bad=Path(directory)/'bad.json'; bad.write_text('broken')
            with patch.object(sys,'argv',['decision.py','check','--position',str(p),'--evidence',str(bad)]),patch.object(d.market,'snapshot',return_value=dict(self.snap(),interval='1m',close=79000)),redirect_stdout(io.StringIO()) as out:
                d.main()
            self.assertEqual(json.loads(out.getvalue())['action'],'SELL_EXIT')

    def test_gate_boundary_volume_equality_and_breakout_strictness(self):
        self.assertEqual(d.decide(dict(self.snap(),volume_ratio_prior20=1.5),self.report())['action'],'BUY_CANDIDATE')
        self.assertEqual(d.decide(dict(self.snap(),close=79900),self.report())['action'],'WAIT')
        report=self.report(); report['holdout']['trades']=100
        self.assertTrue(d.gate(report,dt.datetime(2026,11,22,tzinfo=dt.timezone.utc))[0])
        self.assertFalse(d.gate(report,dt.datetime(2026,11,23,tzinfo=dt.timezone.utc))[0])
    def snap(self):
        return dict(close=80000,prior20_high=79900,volume_ratio_prior20=2,atr14=100,interval='5m',last_completed_close_time_utc='2026-10-25T12:59:59.999+00:00')

    def report(self):
        return dict(rule=d.RULE,symbol='BTCUSDT',venue='Binance spot',end_exclusive_utc='2026-10-23',holdout={'trades':200,'mean':.1},uncertainty={'mean_per_trade_95pct_day_bootstrap':[.01,.2]})

    def test_no_evidence_means_wait_even_with_setup(self):
        r=d.decide(self.snap())
        self.assertTrue(r['technical_setup'])
        self.assertEqual(r['action'],'WAIT')
        self.assertTrue(r['provisional_plan']['reference_only'])

    def test_negative_evidence_cannot_be_overridden_by_label(self):
        report=self.report(); report['holdout']['mean']=-.1; report['research_gate']='FAVORABLE'
        self.assertEqual(d.decide(self.snap(),report)['action'],'WAIT')

    def test_candidate_requires_both_setup_and_research_criteria(self):
        self.assertEqual(d.decide(self.snap(),self.report())['action'],'BUY_CANDIDATE')
        for changes in ({'close':79900},{'volume_ratio_prior20':1.49},{'volume_ratio_prior20':None}):
            self.assertEqual(d.decide(dict(self.snap(),**changes),self.report())['action'],'WAIT')

    def test_evidence_mismatch_future_stale_small_sample_nonfinite(self):
        for changes in ({'rule':'other'},{'end_exclusive_utc':'2026-12-01'},{'end_exclusive_utc':'2026-01-01'},{'holdout':{'trades':99,'mean':1}},{'holdout':{'trades':200,'mean':float('nan')}}):
            self.assertEqual(d.decide(self.snap(),dict(self.report(),**changes))['action'],'WAIT')

    def position(self):
        return dict(workflow.plan(80000,79000,2),quantity_btc=.001,entered_at_utc='2026-10-25T12:30:00+00:00')

    def test_exit_stop_target_timeout_and_hold_independent_of_evidence(self):
        for changes,action,reason in [({},'HOLD',None),({'close':79000},'SELL_EXIT','stop'),({'close':82000},'SELL_EXIT','target'),({'last_completed_close_time_utc':'2026-10-25T13:30:00+00:00'},'SELL_EXIT','time')]:
            r=d.decide(dict(self.snap(),interval='1m',**changes),None,self.position())
            self.assertEqual(r['action'],action)
            if reason:self.assertEqual(r['reason'],reason)
            self.assertFalse(r['exchange_order_sent'])

    def test_bad_position_or_entry_interval_rejected(self):
        with self.assertRaises(ValueError):d.decide(dict(self.snap(),interval='1h'))
        for changes in ({'entered_at_utc':'2026-10-25T14:00:00+00:00'},{'entered_at_utc':'2026-10-25T12:00:00'},{'quantity_btc':0},{'side':'short'}):
            with self.assertRaises(ValueError):d.decide(self.snap(),None,dict(self.position(),**changes))


if __name__=='__main__':unittest.main()
