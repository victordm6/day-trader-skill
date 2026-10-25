from pathlib import Path
import sys
import unittest
import random
import json
import tempfile
import io
from contextlib import redirect_stdout

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'trader-bitcoin'/'scripts'))
import workflow as w
import market
from unittest.mock import patch


class BitcoinWorkflowTests(unittest.TestCase):
    def test_stop_already_breached_blocks_new_entry(self):
        ticket = w.size(w.plan(80000,79000,3),1000,10,1000,.00001,11)
        for price in (78000,79000):
            with self.subTest(price=price):
                self.assertEqual(w.risk(ticket,price,1000,10,30,0,1)['verdict'],'BLOCK')

    def test_sizing_rejects_unsupported_and_malformed_plan(self):
        for changes in ({'symbol':'ETHUSDT'}, {'side':'short'}, {'venue':'futures'}, {'target':79000}, {'target':float('inf')}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                w.size(dict(w.plan(80000,79000,3),**changes),1000,10,1000,.00001,11)

    def test_alerts_reject_invalid_thresholds(self):
        with self.assertRaises(ValueError):
            w.alerts(dict(w.plan(80000,79000,3), stop=85000),80000,{})

    def test_randomized_sizing_limits(self):
        rng = random.Random(19)
        for _ in range(500):
            entry = rng.uniform(10000,150000)
            p = w.plan(entry,entry*rng.uniform(.8,.999),3)
            cash, limit, cap = rng.uniform(20,10000),rng.uniform(1,100),rng.uniform(20,5000)
            t = w.size(p,cash,limit,cap,.000001,rng.uniform(0,30))
            self.assertLessEqual(t['estimated_loss_at_stop_usdt'],limit+1e-8)
            self.assertLessEqual(t['estimated_cash_required_usdt'],cash+1e-8)
            self.assertLessEqual(t['notional_usdt'],cap+1e-8)

    def test_small_budget_rejected(self):
        with self.assertRaises(ValueError):
            w.size(w.plan(80000,79000,3),.01,.01,.01,.001,11)

    def test_target_alert_at_equality_once(self):
        p = w.plan(80000,79000,3)
        events,state = w.alerts(p,83000,{})
        self.assertEqual(events[0]['event'],'target')
        self.assertEqual(w.alerts(p,84000,json.loads(json.dumps(state)))[0],[])

    def test_cli_plan_size_risk_and_persistent_alerts(self):
        scratch = Path(__file__).resolve().parents[1]/'work'
        scratch.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            root = Path(directory)
            def run(args, price=80000):
                with patch.object(sys,'argv',['workflow.py']+args), patch.object(w,'snapshot',return_value={'close':price}), redirect_stdout(io.StringIO()) as output:
                    w.main()
                return json.loads(output.getvalue())
            planfile,ticketfile,statefile = [str(root/name) for name in ('plan.json','ticket.json','state.json')]
            run(['--out',planfile,'plan','--entry','80000','--stop','79000','--reward','3'])
            run(['--out',ticketfile,'size','--plan',planfile,'--cash','1000','--max-loss','10','--cap','900','--step','.00001'])
            result=run(['risk','--ticket',ticketfile,'--cash','1000','--max-loss','10','--daily-limit','30','--daily-used','0','--min-rr','1'])
            self.assertEqual(result['verdict'],'PASS')
            args=['alerts','--plan',planfile,'--state',statefile]
            self.assertEqual(len(run(args,78000)['events']),1)
            self.assertEqual(run(args,78000)['events'],[])

    def test_fractional_size_respects_all_limits(self):
        p = w.plan(80000, 79000, 2)
        ticket = w.size(p, 1000, 10, 900, .00001, 11)
        self.assertLessEqual(ticket['estimated_loss_at_stop_usdt'], 10)
        self.assertLessEqual(ticket['estimated_cash_required_usdt'], 1000)
        self.assertLessEqual(ticket['notional_usdt'], 900)
        self.assertAlmostEqual(ticket['quantity_btc']/.00001, round(ticket['quantity_btc']/.00001))

    def test_invalid_plans_and_nonfinite_inputs(self):
        for values in [(80000, 81000, 2), (float('nan'), 79000, 2), (80000, 79000, -1)]:
            with self.assertRaises(ValueError):
                w.plan(*values)
        with self.assertRaises(ValueError):
            w.size(w.plan(80000,79000,2),1000,10,900,.00001,-1)

    def test_risk_uses_higher_price_and_daily_budget(self):
        ticket = w.size(w.plan(80000,79000,3),1000,10,1000,.00001,11)
        self.assertEqual(w.risk(ticket,80000,1000,10,30,0,1)['verdict'], 'PASS')
        self.assertEqual(w.risk(ticket,81000,1000,10,30,0,1)['verdict'], 'BLOCK')
        self.assertEqual(w.risk(ticket,80000,1000,10,10,9,1)['verdict'], 'BLOCK')
        self.assertEqual(w.risk(ticket,84000,1000,10,30,0,1)['verdict'], 'BLOCK')

    def test_alerts_once_and_plan_reset(self):
        p = w.plan(80000,79000,2)
        events, state = w.alerts(p,78000,{})
        self.assertEqual(events[0]['event'], 'stop')
        self.assertEqual(w.alerts(p,78000,state)[0], [])
        p2 = w.plan(80000,79500,2)
        self.assertEqual(len(w.alerts(p2,78000,state)[0]), 1)

    def test_snapshot_excludes_forming_bar(self):
        rows = [[i*300000,100,101,99,100,10,(i+1)*300000-1] for i in range(101)]
        def fake(path):
            return {'serverTime': 100*300000} if path == '/time' else rows
        with patch.object(market,'public',side_effect=fake):
            result = market.snapshot('5m')
        self.assertEqual(result['completed_candles'],100)

    def test_snapshot_rejects_stale_and_gapped_data(self):
        rows = [[i*300000,100,101,99,100,10,(i+1)*300000-1] for i in range(101)]
        with patch.object(market,'public',side_effect=lambda path: {'serverTime': 200*300000} if path == '/time' else rows):
            with self.assertRaisesRegex(ValueError,'Stale'):
                market.snapshot('5m')
        rows[50][0] += 1000
        with patch.object(market,'public',side_effect=lambda path: {'serverTime': 101*300000} if path == '/time' else rows):
            with self.assertRaisesRegex(ValueError,'gap'):
                market.snapshot('5m')


if __name__ == '__main__':
    unittest.main()
