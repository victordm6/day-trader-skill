#!/usr/bin/env python3
"""10,000 deterministic offline property scenarios; no market/account requests."""
import argparse
import datetime as dt
from decimal import Decimal, ROUND_DOWN
import hashlib
import json
from pathlib import Path
import random
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'trader-bitcoin'/'scripts'))
import workflow as w
import decision as d
import context as macro

SEED=20261025
COUNTS={'sizing':2500,'risk':2500,'entry_decision':2000,'position_exit':1500,'macro_context':1500}


def check(condition, message):
    if not condition: raise AssertionError(message)


def scenario(family,rng,index):
    entry=rng.uniform(10000,200000)
    stop=entry*(1-rng.uniform(.001,.2))
    p=w.plan(entry,stop,rng.uniform(.5,5))
    if family=='sizing':
        cash,loss,cap=rng.uniform(100,100000),rng.uniform(.5,1000),rng.uniform(100,50000)
        step=rng.choice([.00000001,.000001,.00001,.0001])
        bps=rng.uniform(0,50)
        def expected_quantity(cost):
            unit=entry-stop+(cost/10000)*(entry+stop)
            raw=min(loss/unit,cash/(entry*(1+cost/10000)),cap/entry)
            return (Decimal(str(raw))/Decimal(str(step))).to_integral_value(rounding=ROUND_DOWN)*Decimal(str(step))
        if expected_quantity(bps)==0:
            try:w.size(p,cash,loss,cap,step,bps)
            except ValueError:pass
            else:raise AssertionError('Unaffordable minimum quantity accepted')
            return {'entry':entry,'stop':stop,'cash':cash,'loss':loss,'cap':cap,'step':step,'bps':bps,'expected_rejection':True}
        t=w.size(p,cash,loss,cap,step,bps)
        q=Decimal(str(t['quantity_btc'])); e=Decimal(str(entry)); s=Decimal(str(stop)); fee=Decimal(str(bps))/10000
        check(q*(e-s+fee*(e+s))<=Decimal(str(loss))+Decimal('0.00000001'),'Stop risk exceeded')
        check(q*e*(1+fee)<=Decimal(str(cash))+Decimal('0.00000001'),'Cash exceeded')
        check(q*e<=Decimal(str(cap))+Decimal('0.00000001'),'Cap exceeded')
        check(q%Decimal(str(step))==0,'Quantity not on grid')
        if expected_quantity(bps+1)==0:
            try:w.size(p,cash,loss,cap,step,bps+1)
            except ValueError:pass
            else:raise AssertionError('Higher-cost unaffordable quantity accepted')
        else:
            less=w.size(p,cash,loss,cap,step,bps+1)
            check(less['quantity_btc']<=t['quantity_btc'],'Higher costs increased size')
        return {'entry':entry,'stop':stop,'cash':cash,'loss':loss,'cap':cap,'step':step,'bps':bps,'quantity':float(q)}
    if family=='risk':
        t=w.size(p,100000,1000,50000,.000001,11)
        price=rng.uniform(stop*.9,p['target']*1.1)
        cash,loss,daily,used,minrr=rng.uniform(1,100000),rng.uniform(1,3000),rng.uniform(1,5000),rng.uniform(0,5000),rng.uniform(.1,4)
        q=t['quantity_btc']; base=max(entry,price); fee=.0011
        loss_amount=q*(base-stop+fee*(base+stop))
        rr=(p['target']-base-fee*(p['target']+base))/(base-stop+fee*(base+stop))
        expected=stop<price<p['target'] and loss_amount<=loss+1e-9 and used+loss_amount<=daily+1e-9 and q*base*(1+fee)<=cash+1e-9 and rr>=minrr
        r=w.risk(t,price,cash,loss,daily,used,minrr)
        check((r['verdict']=='PASS')==expected,'Risk verdict differs from independent constraints')
        return {'price':price,'cash':cash,'loss':loss,'daily':daily,'used':used,'minrr':minrr,'verdict':r['verdict']}
    now=dt.datetime(2026,10,25,15,tzinfo=dt.timezone.utc)
    snapshot={'close':entry,'prior20_high':entry*rng.uniform(.99,1.01),'volume_ratio_prior20':rng.uniform(0,3),
              'atr14':entry*.005,'interval':'5m','last_completed_close_time_utc':now.isoformat()}
    if family=='entry_decision':
        age=rng.randrange(-3,40); count=rng.randrange(0,400); mean=rng.uniform(-1,1); lower=rng.uniform(-1,1)
        report={'rule':d.RULE,'symbol':'BTCUSDT','venue':'Binance spot','end_exclusive_utc':str(now.date()-dt.timedelta(days=age)),
                'holdout':{'trades':count,'mean':mean},'uncertainty':{'mean_per_trade_95pct_day_bootstrap':[lower,lower+1]}}
        expected=snapshot['close']>snapshot['prior20_high'] and snapshot['volume_ratio_prior20']>=1.5 and 0<=age<=30 and count>=100 and mean>0 and lower>0
        result=d.decide(snapshot,report)
        check((result['action']=='BUY_CANDIDATE')==expected,'Entry evidence/setup mismatch')
        check(not result['exchange_order_sent'],'Order sent')
        return {'age':age,'count':count,'mean':mean,'lower':lower,'snapshot':snapshot,'action':result['action']}
    if family=='position_exit':
        elapsed=rng.randrange(0,7201)
        price=rng.uniform(stop*.95,p['target']*1.05)
        snapshot.update(interval='1m',close=price)
        pos=dict(p,quantity_btc=.001,entered_at_utc=(now-dt.timedelta(seconds=elapsed)).isoformat())
        result=d.decide(snapshot,None,pos)
        reason='stop' if price<=stop else 'target' if price>=p['target'] else 'time' if elapsed>=3600 else None
        check(result['action']==('SELL_EXIT' if reason else 'HOLD'),'Exit action mismatch')
        if reason:check(result['reason']==reason,'Exit priority mismatch')
        check(not result['exchange_order_sent'],'Order sent')
        return {'price':price,'stop':stop,'target':p['target'],'elapsed':elapsed,'action':result['action']}
    age=rng.randrange(-60,1201); minutes=rng.randrange(-120,121)
    complete=rng.choice([True,False]); importance=rng.choice(['low','moderate','high','unknown']); currency=rng.choice(['USD','EUR'])
    offset=dt.timezone(dt.timedelta(hours=rng.choice([-5,-3,0,1,8])))
    obs={'source_url':macro.SOURCE,'observed_at':(now-dt.timedelta(seconds=age)).astimezone(offset).isoformat(),
         'coverage_start':(now-dt.timedelta(days=1)).isoformat(),'coverage_end':(now+dt.timedelta(days=1)).isoformat(),
         'coverage_complete':complete,'events':[{'title':'Synthetic event','currency':currency,'importance':importance,'scheduled_at':(now+dt.timedelta(minutes=minutes)).astimezone(offset).isoformat()}]}
    result=macro.calendar_context(obs,now)
    expected='unavailable' if age<0 or age>600 else 'observed' if complete and importance!='unknown' else 'partial'
    check(result['status']==expected,'Macro availability mismatch')
    if expected!='unavailable':
        check(result['upcoming_usd_high_impact_count']==int(currency=='USD' and importance=='high' and 0<=minutes<=60),'Event proximity mismatch')
    return {'age':age,'minutes':minutes,'complete':complete,'importance':importance,'currency':currency,'offset':str(offset),'status':result['status']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    rng=random.Random(SEED); digest=hashlib.sha256(); results={}; failures=[]
    for family,count in COUNTS.items():
        passed=0
        for index in range(count):
            try:
                case=scenario(family,rng,index); passed+=1
                digest.update(json.dumps([family,index,case],sort_keys=True,allow_nan=False).encode())
            except Exception as exc:
                failures.append({'family':family,'index':index,'error':repr(exc)})
        results[family]={'scenarios':count,'passed':passed,'failed':count-passed}
    report={'seed':SEED,'total':sum(COUNTS.values()),'passed':sum(v['passed'] for v in results.values()),
            'failed':len(failures),'families':results,'failures':failures,'successful_case_sha256':digest.hexdigest(),
            'offline':True,'orders_sent':0,'limitation':'Generated software property scenarios, not historical trades, profit simulations or independent test functions.'}
    args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2)); raise SystemExit(1 if failures else 0)


if __name__=='__main__':main()
