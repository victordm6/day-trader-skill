import datetime as dt
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'trader-bitcoin'/'scripts'))
import backtest as b

class SensitivityTests(unittest.TestCase):
    def bars(self):
        start=b.stamp(dt.date(2026,1,1))
        x=[(start+i*300,100.,101.,99.,100.,10.) for i in range(150)]
        x[100]=(x[100][0],100.,103.,99.,102.,30.)
        x[101]=(x[101][0],102.,110.,90.,102.,10.)
        return x
    def test_default_unchanged(self):
        self.assertEqual(b.breakout(self.bars()),b.breakout(self.bars(),fee_bps=10,delay=0,stop_atr=1))
    def test_fee_changes_pnl_not_trade_timing(self):
        cheap=b.breakout(self.bars(),fee_bps=0); costly=b.breakout(self.bars(),fee_bps=10)
        self.assertEqual(len(cheap),1)
        self.assertEqual(cheap[0]['entry_time'],costly[0]['entry_time'])
        self.assertGreater(cheap[0]['pnl'],costly[0]['pnl'])
    def test_delay_causality(self):
        for delay in (0,1):
            for trade in b.breakout(self.bars(),delay=delay):
                self.assertGreaterEqual(trade['entry_time'],trade['signal']+delay*300)
    def test_invalid_parameters(self):
        for values in ({'fee_bps':-1},{'fee_bps':float('nan')},{'delay':-1},{'delay':1.5},{'stop_atr':0}):
            with self.assertRaises(ValueError):b.breakout(self.bars(),**values)

if __name__=='__main__':unittest.main()
