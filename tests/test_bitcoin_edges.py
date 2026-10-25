import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
from urllib.error import URLError

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'trader-bitcoin'/'scripts'))
import market
import suite
import workflow


class BitcoinEdges(unittest.TestCase):
    def rows(self):
        return [[i*300000,100,101,99,100,10,(i+1)*300000-1] for i in range(101)]

    def snap(self,rows):
        with patch.object(market,'public',side_effect=lambda path: {'serverTime':101*300000} if path=='/time' else rows):
            return market.snapshot('5m')

    def test_candle_time_alignment_and_close_time(self):
        for change in ('alignment','close'):
            rows=self.rows()
            if change=='alignment':
                for row in rows: row[0]+=1
            else: rows[50][6]=rows[50][0]-1
            with self.subTest(change=change),self.assertRaises(ValueError): self.snap(rows)

    def test_bad_prices_volume_duplicates_and_short_history(self):
        variants=[]
        for index,value in ((1,float('nan')),(2,98),(5,-1)):
            rows=self.rows(); rows[50][index]=value; variants.append(rows)
        rows=self.rows(); rows[50]=rows[49]; variants.extend([rows,self.rows()[:20]])
        for rows in variants:
            with self.assertRaises(ValueError): self.snap(rows)

    def test_scanner_all_unavailable_is_partial(self):
        with patch.object(market,'snapshot',side_effect=URLError('offline')):
            result=suite.scan(['1m','5m'])
        self.assertTrue(result['partial'])
        self.assertTrue(all(r['status']=='unavailable' for r in result['intervals']))

    def test_disclosure_requires_url_host_and_text_entity(self):
        record=dict(asset='BTC',exposure='direct',source_url='https://example.org/filing',entity='Example',action='holding',disclosed_date='2026-01-01')
        for change in ({'source_url':'https:missing-host'},{'entity':123},{'action':['buy']},{'disclosed_date':'2999-01-01'}):
            with self.subTest(change=change):
                self.assertEqual(len(suite.disclosures([dict(record,**change)])['rejected']),1)

    def test_network_failure_preserves_news_state(self):
        (ROOT/'work').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as directory:
            state=Path(directory)/'state.json'; state.write_text('{"seen":["existing"]}')
            original=state.read_bytes()
            with patch.object(suite.urllib.request,'urlopen',side_effect=URLError('offline')),self.assertRaises(URLError): suite.news(state)
            self.assertEqual(state.read_bytes(),original)

    def test_news_deduplicates_orders_and_marks_backlog(self):
        (ROOT/'work').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as directory:
            root=Path(directory); feed=root/'rss'; state=root/'state'
            feed.write_text('<rss><channel>'+''.join('<item><title>'+name+'</title><link>https://example.org/'+name+'</link><pubDate>'+date+'</pubDate></item>' for name,date in [('old','2026-01-01T00:00:00Z'),('new','2026-02-01T00:00:00Z'),('new','2026-02-01T00:00:00Z')])+'</channel></rss>')
            result=suite.news(state,feed)
            self.assertTrue(result['initial_historical_backlog'])
            self.assertEqual([i['title'] for i in result['items']],['new','old'])
            self.assertFalse(suite.news(state,feed)['initial_historical_backlog'])

    def test_adapter_plan_budget_risk_broker_alert_handoff(self):
        (ROOT/'work').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as directory:
            root=Path(directory); p=str(root/'plan'); t=str(root/'ticket')
            def run(module,args,price=80000):
                with patch.object(sys,'argv',['suite.py',module]+args),patch.object(market,'snapshot',return_value={'close':price}),patch.object(workflow,'snapshot',return_value={'close':price}),redirect_stdout(io.StringIO()) as out:
                    suite.main()
                return json.loads(out.getvalue())
            run('exit',['--entry','80000','--stop','79000','--reward','3','--out',p])
            run('budget',['--plan',p,'--cash','1000','--max-loss','10','--cap','900','--step','.00001','--out',t])
            args=['--ticket',t,'--cash','1000','--max-loss','10','--daily-limit','30','--daily-used','0','--min-rr','1']
            self.assertEqual(run('risk',args)['verdict'],'PASS')
            self.assertEqual(run('broker',args)['status'],'PAPER_READY')
            self.assertEqual(run('broker',args,79000)['status'],'BLOCK')
            self.assertEqual(run('alerts',['--plan',p,'--state',str(root/'state')],83000)['events'][0]['event'],'target')

    def test_broker_blocks_insufficient_cash_daily_budget_and_wrong_symbol(self):
        ticket=workflow.size(workflow.plan(80000,79000,3),1000,10,900,.00001,11)
        limits=dict(cash=1000,max_loss=10,daily_limit=30,daily_used=0,min_rr=1)
        for change in ({'cash':1},{'daily_used':29},{'min_rr':100}):
            self.assertEqual(suite.paper_ticket(ticket,dict(limits,**change),{'close':80000})['status'],'BLOCK')
        self.assertEqual(suite.paper_ticket(dict(ticket,symbol='ETHUSDT'),limits,{'close':80000})['status'],'BLOCK')


if __name__=='__main__': unittest.main()
