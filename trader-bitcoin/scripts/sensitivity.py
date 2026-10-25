#!/usr/bin/env python3
"""Exploratory 24-case BTC historical sensitivity grid; no strategy promotion."""
import argparse
import datetime as dt
import itertools
import json
from pathlib import Path
import random

import backtest as b


def interval(trades,start,end,comparisons):
    days=[[] for _ in range((end-start).days)]
    for trade in trades:
        days[(dt.date.fromisoformat(b.date_of(trade['entry_time']))-start).days].append(trade['pnl'])
    daily=[(sum(x),len(x)) for x in days]
    rng=random.Random(19); values=[]
    for _ in range(10000):
        sample=rng.choices(daily,k=len(daily)); n=sum(x[1] for x in sample)
        if n:values.append(sum(x[0] for x in sample)/n)
    values.sort()
    if not values:return None
    tail=.05/(2*comparisons)
    return {'seed':19,'replays':10000,'comparisons':comparisons,
            'bonferroni_day_bootstrap_mean_r':[values[int(tail*len(values))],values[min(len(values)-1,int((1-tail)*len(values)))]]}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--start',type=dt.date.fromisoformat,required=True)
    p.add_argument('--end',type=dt.date.fromisoformat,required=True)
    p.add_argument('--cache',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.start>=args.end or args.end>dt.datetime.now(dt.timezone.utc).date():p.error('Completed UTC days only')
    cutoff=b.month_add(args.end,-2)
    if cutoff<=args.start:p.error('Need more than two months')
    bars,manifest=b.download(args.start,args.end,args.cache); five=b.aggregate(bars)
    grid=list(itertools.product((0,1,5,10),(0,1),(1,2,3)))
    results=[]
    for fee,delay,stop in grid:
        trades=b.breakout(five,fee_bps=fee,delay=delay,stop_atr=stop)
        final=[t for t in trades if t['entry_time']>=b.stamp(cutoff)]
        early=[t for t in trades if t['exit_time']<=b.stamp(cutoff)]
        assert all(t['entry_time']>=t['signal']+delay*300 for t in trades)
        assert all(a['exit_time']<=c['entry_time'] for a,c in zip(trades,trades[1:]))
        row={'fee_bps_each_side':fee,'entry_delay_m5_bars':delay,'stop_atr':stop,
             'overall':b.summarize(trades),'early':b.summarize(early),'final_two_months':b.summarize(final),
             'uncertainty':interval(final,cutoff,args.end,len(grid))}
        results.append(row)
        print('Completed',fee,delay,stop,flush=True)
    report={'start_utc':str(args.start),'end_exclusive_utc':str(args.end),'cutoff_utc':str(cutoff),'minutes':len(bars),
            'variant_count':len(grid),'manifest':manifest,'results':results,
            'fixed_assumptions':'M5 prior20-high breakout, volume1.5x; 1bp adverse slippage each side; target2R; max12bars after entry; stop-first; no overlap.',
            'limitation':'Exploratory reused history; all 24 variants examined, approximate familywise bootstrap intervals, no untouched validation. Fee zero still includes slippage. R units differ with stop distance. No account sizing or macro filters.',
            'execution':'disabled','strategy_promoted':False}
    args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('Saved',args.out)


if __name__=='__main__':main()
