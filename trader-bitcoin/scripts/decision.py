#!/usr/bin/env python3
"""Fixed BTC spot research decisions. Never sends orders or assumes fills."""
import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path

import backtest
import market
import workflow

RULE = 'btc-m5-breakout20-volume1.5-atr14-stop1-target2-time12-v1'


def evidence(start,end,cache):
    if start >= end or end > dt.datetime.now(dt.timezone.utc).date():
        raise ValueError('Require completed UTC days with start < exclusive end')
    cutoff = backtest.month_add(end,-2)
    if cutoff <= start:
        raise ValueError('Need more than two months for a separate chronological check')
    bars,manifest = backtest.download(start,end,cache)
    trades = backtest.breakout(backtest.aggregate(bars))
    holdout = [t for t in trades if t['entry_time'] >= backtest.stamp(cutoff)]
    stats = backtest.summarize(holdout)
    uncertainty = backtest.bootstrap(holdout,cutoff,end)
    lower = uncertainty['mean_per_trade_95pct_day_bootstrap'][0] if uncertainty else None
    favorable = stats['trades'] >= 100 and stats.get('mean',0)>0 and lower is not None and lower>0
    return {'rule':RULE,'symbol':'BTCUSDT','venue':'Binance spot','start_utc':str(start),
            'end_exclusive_utc':str(end),'holdout_start_utc':str(cutoff),
            'overall':backtest.summarize(trades),'holdout':stats,'uncertainty':uncertainty,
            'research_gate':'FAVORABLE' if favorable else 'NOT_SUPPORTED',
            'criteria':'At least 100 holdout trades; net mean > 0; day-bootstrap 95% lower bound > 0.',
            'assumptions':'5m close>prior20high; volume>=1.5xprior20mean; next open; ATR14 stop; 2R target; 12 bars; stop-first; 10bp fee + 1bp slippage each side.',
            'manifest':manifest,'minutes':len(bars),'execution':'disabled',
            'limitation':'Chronological research check only; this period was previously examined. Not independent validation or a forecast. No parameter optimization performed.'}


def gate(report, now):
    if not report:
        return False,'No historical evidence file'
    if report.get('rule') != RULE or report.get('symbol') != 'BTCUSDT' or report.get('venue') != 'Binance spot':
        return False,'Evidence does not match rule/market'
    try:
        end=dt.date.fromisoformat(report['end_exclusive_utc'])
        age=(now.date()-end).days
        stats=report['holdout']; lower=report['uncertainty']['mean_per_trade_95pct_day_bootstrap'][0]
        mean=float(stats['mean']); lower=float(lower)
        supported=stats['trades']>=100 and math.isfinite(mean) and math.isfinite(lower) and mean>0 and lower>0
        if not 0 <= age <= 30: return False,'Evidence is future-dated or older than 30 days'
        return supported,'Historical research criteria met; edge still unproven' if supported else 'Historical research criteria failed'
    except (KeyError,TypeError,ValueError,OverflowError):
        return False,'Invalid or incomplete evidence'


def decide(snapshot, report=None, position=None):
    observed=dt.datetime.fromisoformat(snapshot['last_completed_close_time_utc'])
    if observed.tzinfo is None: raise ValueError('Require timezone-aware observation')
    result={'rule':RULE,'symbol':'BTCUSDT','price_source':snapshot,'execution':'disabled','exchange_order_sent':False}
    if position is not None:
        workflow.validate_plan(position)
        workflow.positive(position['quantity_btc'])
        entered=dt.datetime.fromisoformat(position['entered_at_utc'])
        if entered.tzinfo is None or entered > observed:
            raise ValueError('Position entry must be timezone-aware and precede observation')
        reason='stop' if snapshot['close']<=position['stop'] else 'target' if snapshot['close']>=position['target'] else 'time' if (observed-entered).total_seconds()>=3600 else None
        result.update(action='SELL_EXIT' if reason else 'HOLD',reason=reason or 'No observed exit condition',
                      position_source='user_supplied_not_exchange_verified',
                      limitation='Exit observation at completed candle close, not a fill. Intrabar touches may be missed. No short sale.')
        return result
    if snapshot['interval'] != '5m': raise ValueError('Entry rule requires 5m candles')
    volume=snapshot['volume_ratio_prior20']
    setup=snapshot['close']>snapshot['prior20_high'] and volume is not None and volume>=1.5
    allowed,reason=gate(report,observed)
    result.update(action='BUY_CANDIDATE' if setup and allowed else 'WAIT',technical_setup=setup,
                  research_gate_passed=allowed,reason=reason if not allowed else 'Breakout with volume' if setup else 'Entry conditions absent',
                  limitation='Research candidate only. Historical entry assumes next-bar open; current close is not a fill or executable quote. Risk sizing and explicit user decision remain separate.')
    if setup:
        atr=workflow.positive(snapshot['atr14'])
        if atr>=snapshot['close']: raise ValueError('ATR exceeds reference price')
        result['provisional_plan']=dict(workflow.plan(snapshot['close'],snapshot['close']-atr,2),
                                        reference_only=True,max_hold_minutes=60,
                                        note='Recompute from actual entry and frozen signal ATR. Do not fabricate a position from this plan.')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    val=sub.add_parser('validate')
    val.add_argument('--start',type=dt.date.fromisoformat,required=True)
    val.add_argument('--end',type=dt.date.fromisoformat,required=True)
    val.add_argument('--cache',type=Path,required=True)
    val.add_argument('--out',type=Path,required=True)
    check=sub.add_parser('check')
    check.add_argument('--evidence',type=Path)
    check.add_argument('--position',type=Path)
    check.add_argument('--out',type=Path)
    args=parser.parse_args()
    if args.command=='validate':
        result=evidence(args.start,args.end,args.cache)
    else:
        report=workflow.read(args.evidence) if args.evidence else None
        position=workflow.read(args.position) if args.position else None
        result=decide(market.snapshot('1m' if position else '5m'),report,position)
        if args.evidence: result['evidence_sha256']=hashlib.sha256(args.evidence.read_bytes()).hexdigest()
    result['generated_at_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
    text=json.dumps(result,indent=2,allow_nan=False)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(text+'\n',encoding='utf-8')
    print(text)


if __name__=='__main__': main()
