import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'trader-bitcoin'/'scripts'))
import suite
import workflow


class BitcoinSuite(unittest.TestCase):
    def test_all_eleven_entrypoints_have_working_help(self):
        for module in suite.MODULES:
            with self.subTest(module=module):
                result = subprocess.run([sys.executable,str(ROOT/('trader-'+module)/'btc.py'),'--help'],capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertIn('usage:',result.stdout)

    def test_scanner_partial_failure_preserves_other_interval(self):
        s = {'close':100,'prior20_high':99,'volume_ratio_prior20':2,'ema9':101,'ema21':100}
        with patch.object(suite.market,'snapshot',side_effect=[s,ValueError('gap')]):
            result=suite.scan(['5m','1h'])
        self.assertTrue(result['partial'])
        self.assertTrue(result['intervals'][0]['breakout_with_volume'])
        self.assertEqual(result['intervals'][1]['status'],'unavailable')

    def test_no_volume_baseline_does_not_trigger(self):
        s = {'close':100,'prior20_high':99,'volume_ratio_prior20':None,'ema9':100,'ema21':100}
        with patch.object(suite.market,'snapshot',return_value=s):
            self.assertFalse(suite.scan(['5m'])['intervals'][0]['breakout_with_volume'])

    def test_rss_atom_and_invalid_links(self):
        rss=b'<rss><channel><item><title>Release</title><link>https://bitcoincore.org/test</link><pubDate>date</pubDate></item><item><title>Bad</title><link>javascript:bad</link></item></channel></rss>'
        self.assertEqual(len(suite.parse_feed(rss)),1)
        atom=b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Release</title><link href="https://bitcoincore.org/test"/><updated>date</updated></entry></feed>'
        self.assertEqual(suite.parse_feed(rss)[0]['id'],suite.parse_feed(atom)[0]['id'])

    def test_news_persistence_and_no_state_loss_on_invalid_feed(self):
        (ROOT/'work').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as temp:
            path=Path(temp); feed=path/'rss.xml'; state=path/'state.json'
            feed.write_text('<rss><channel><item><title>Release</title><link>https://bitcoincore.org/test</link></item></channel></rss>')
            self.assertEqual(len(suite.news(state,feed)['items']),1)
            self.assertEqual(suite.news(state,feed)['items'],[])
            previous=state.read_bytes(); feed.write_text('<invalid')
            with self.assertRaises(Exception): suite.news(state,feed)
            self.assertEqual(state.read_bytes(),previous)

    def test_paper_broker_rechecks_risk_and_never_sends_order(self):
        t=workflow.size(workflow.plan(80000,79000,3),1000,10,900,.00001,11)
        limits=dict(cash=1000,max_loss=10,daily_limit=30,daily_used=0,min_rr=1)
        self.assertEqual(suite.paper_ticket(t,limits,{'close':80000})['status'],'PAPER_READY')
        blocked=suite.paper_ticket(t,limits,{'close':78000})
        self.assertEqual(blocked['status'],'BLOCK')
        self.assertFalse(blocked['exchange_order_sent'])
        self.assertEqual(blocked['execution'],'disabled')

    def test_disclosure_exposure_is_not_inferred_as_direct(self):
        valid={'entity':'Example fund','asset':'BTC','exposure':'etf','source_url':'https://example.com/filing','disclosed_date':'2026-01-01','action':'reported holding'}
        result=suite.disclosures([valid,dict(valid,source_url='file:///private'),dict(valid,exposure='whale')])
        self.assertEqual(len(result['records']),1)
        self.assertEqual(result['records'][0]['exposure'],'etf')
        self.assertIn('not_independently_verified',result['records'][0]['verification'])
        self.assertEqual(len(result['rejected']),2)

    def test_shared_entry_dispatch(self):
        with patch.object(sys,'argv',['suite.py','entry','--level','80000']), patch.object(workflow,'snapshot',return_value={'close':80001}), redirect_stdout(io.StringIO()) as out:
            suite.main()
        self.assertEqual(json.loads(out.getvalue())['status'],'above_level')


if __name__ == '__main__':
    unittest.main()
