from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'trader-bitcoin'/'scripts'))
import workflow as w
import market
from unittest.mock import patch


class BitcoinWorkflowTests(unittest.TestCase):
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
