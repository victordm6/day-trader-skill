import copy
import datetime as dt
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'trader-bitcoin'/'scripts'))
import ebinex

NOW = dt.datetime(2026, 10, 25, 20, 0, tzinfo=dt.timezone.utc)


def observation():
    return dict(venue='ebinex', product='digital_fixed_payout', symbol='BTCUSDX', mode='demo',
                observed_at_utc=NOW.isoformat(), source_kind='visible_ui_observation',
                evidence='Synthetic test fixture only', expiry_seconds=60,
                payout_ratio=.9, prepared_stake_usdt=1)


def trade(ident='1', status='WIN'):
    return dict(id=ident, mode='demo', symbol='BTCUSDX', product='digital_fixed_payout',
                status=status, confirmation='explicit_platform_result', result_evidence='Synthetic receipt',
                entry_utc='2026-10-25T19:00:00Z', expiry_utc='2026-10-25T19:01:00Z',
                settled_utc='2026-10-25T19:01:01Z', direction='BUY', stake_usdt=1,
                payout_ratio=.9, fees_usdt=0, cash_return_usdt=1.9 if status=='WIN' else 0)


def ledger(rows, complete=True):
    return dict(mode='demo', coverage_complete=complete, coverage_evidence='Synthetic full test scope',trades=rows)


class Ebinex(unittest.TestCase):
    def test_observed_payout_is_not_spot_validation(self):
        r=ebinex.inspect(observation(),NOW)
        self.assertEqual(r['status'],'OBSERVED_ONLY')
        self.assertAlmostEqual(r['theoretical_break_even_without_fees'],1/1.9)
        self.assertFalse(r['strategy_validated']);self.assertFalse(r['rule_14410']['compatible'])
        self.assertFalse(r['prepared_stake_is_investment'])

    def test_stale_future_real_and_non_ebinex_fail_closed(self):
        for change in [dict(observed_at_utc=(NOW-dt.timedelta(seconds=91)).isoformat()),
                       dict(observed_at_utc=(NOW+dt.timedelta(seconds=1)).isoformat()),
                       dict(mode='real'),dict(symbol='BTCUSDT'),dict(expiry_seconds=92160),
                       dict(source_kind='binance'),dict(synthetic_example=True)]:
            with self.subTest(change=change):
                x=observation();x.update(change);self.assertEqual(ebinex.inspect(x,NOW)['status'],'BLOCK')

    def test_timezone_and_amounts_are_not_guessed(self):
        for change in [dict(observed_at_utc='2026-10-25T20:00:00'),
                       dict(prepared_stake_usdt=float('nan')),dict(expiry_seconds=True)]:
            x=observation();x.update(change)
            with self.assertRaises(ValueError):ebinex.inspect(x,NOW)

    def test_win_loss_with_fees(self):
        loss=trade('2','LOSS');loss['fees_usdt']=.01
        r=ebinex.analyze(ledger([trade(),loss]),100)
        self.assertAlmostEqual(r['complete_net_usdt'],-.11)
        self.assertEqual(r['observed_closed_win_rate'],.5)
        self.assertAlmostEqual(r['closed_pnl_balance_usdt'],99.89)
        self.assertAlmostEqual(r['closed_balance_drawdown'],1.01/100.9)

    def test_unresolved_is_not_a_loss_and_incomplete_has_no_complete_profit(self):
        pending=dict(id='2',mode='demo',symbol='BTCUSDX',product='digital_fixed_payout',status='OPEN')
        r=ebinex.analyze(ledger([trade(),pending]),100)
        self.assertEqual(r['closed_count'],1);self.assertEqual(r['losses'],0)
        self.assertIsNone(r['complete_net_usdt']);self.assertFalse(r['complete_results'])
        self.assertIsNone(ebinex.analyze(ledger([trade()],False),100)['complete_net_usdt'])

    def test_no_balance_only_or_spot_confirmation(self):
        for change in [dict(confirmation='balance_debit'),dict(result_evidence=''),
                       dict(product='spot'),dict(mode='real'),dict(symbol='BTCUSDT')]:
            x=trade();x.update(change)
            with self.subTest(change=change),self.assertRaises(ValueError):ebinex.analyze(ledger([x]),100)

    def test_duplicate_and_contradictory_settlement_rejected(self):
        with self.assertRaises(ValueError):ebinex.analyze(ledger([trade(),trade()]),100)
        for change in [dict(cash_return_usdt=1),dict(payout_ratio=90),
                       dict(expiry_utc='2026-10-25T18:59:00Z'),dict(settled_utc='2026-10-25T19:00:30Z')]:
            x=trade();x.update(change)
            with self.subTest(change=change),self.assertRaises(ValueError):ebinex.analyze(ledger([x]),100)

    def test_variable_payout_and_explicit_tie_policy(self):
        a=trade();a.update(payout_ratio=.8,cash_return_usdt=1.8)
        t=trade('2','TIE');t.update(tie_rule='refund',cash_return_usdt=1)
        self.assertAlmostEqual(ebinex.analyze(ledger([a,t]),100)['complete_net_usdt'],.8)
        del t['tie_rule']
        with self.assertRaises(ValueError):ebinex.analyze(ledger([t]),100)

    def test_fixed_stake_risk_uses_full_loss_not_atr_stop(self):
        limits=dict(cash=100,max_loss=.99,daily_limit=10,daily_used=0,fees=0)
        r=ebinex.run_module('risk',observation(),now=NOW,limits=limits)
        self.assertEqual(r['risk']['status'],'BLOCK')
        limits.update(max_loss=1,daily_used=9.1)
        self.assertEqual(ebinex.run_module('risk',observation(),now=NOW,limits=limits)['risk']['status'],'BLOCK')
        self.assertEqual(ebinex.run_module('budget',observation(),now=NOW)['risk']['status'],'BLOCK')

    def test_all_modules_use_disabled_local_ebinex_route(self):
        for module in ebinex.MODULES:
            with self.subTest(module=module):
                r=ebinex.run_module(module,observation(),now=NOW)
                self.assertFalse(r['order_sent']);self.assertFalse(r['strategy_validated'])
                if module in ('entry','exit'):self.assertEqual(r['decision'],'WAIT')
        self.assertEqual(ebinex.run_module('broker',observation(),now=NOW)['status'],'EXECUTION_DISABLED')

    def test_entry_cli_never_fetches_binance_or_sends_order(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'observation.json';p.write_text(json.dumps(observation()))
            for module in ebinex.MODULES:
                with self.subTest(module=module):
                    proc=subprocess.run([sys.executable,str(ROOT/('trader-'+module)/'btc.py'),
                        '--venue','ebinex','--observation',str(p)],capture_output=True,text=True)
                    self.assertEqual(proc.returncode,0,proc.stderr)
                    result=json.loads(proc.stdout);self.assertEqual(result['venue'],'ebinex')
                    self.assertFalse(result['order_sent'])

    def test_empty_ledger_no_fabricated_win_rate(self):
        r=ebinex.analyze(ledger([]),100)
        self.assertEqual(r['closed_count'],0);self.assertIsNone(r['observed_closed_win_rate'])


if __name__=='__main__':unittest.main()
