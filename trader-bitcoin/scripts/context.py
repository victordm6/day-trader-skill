#!/usr/bin/env python3
"""Combine observed Investing calendar context with Binance spot prices."""
import argparse
import datetime as dt
import json
from pathlib import Path

import market
import workflow

SOURCE='https://br.investing.com/economic-calendar'


def instant(value):
    parsed=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
    if parsed.tzinfo is None: raise ValueError('Explicit timezone offset required')
    return parsed.astimezone(dt.timezone.utc)


def calendar_context(observation,now):
    result={'source':SOURCE,'status':'unavailable','events':[],
            'note':'Calendar is macro context, not news coverage or a BTC direction signal. Unknown coverage does not mean no events.'}
    if observation is None:
        result['reason']='Calendar not observed; open source in browser and supply visible observations'
        return result
    if observation.get('source_url') != SOURCE: raise ValueError('Unexpected calendar source')
    observed=instant(observation['observed_at'])
    age=(now-observed).total_seconds()
    if age<0 or age>600:
        result['reason']='Observation is future-dated or older than 10 minutes'
        return result
    start,end=instant(observation['coverage_start']),instant(observation['coverage_end'])
    if start>=end: raise ValueError('Invalid coverage interval')
    complete=observation.get('coverage_complete') is True and start<=now<end
    events=[]
    for item in observation['events']:
        if not isinstance(item.get('title'),str) or not item['title'].strip(): raise ValueError('Event title required')
        importance=item.get('importance')
        if importance not in ('low','moderate','high','unknown'): raise ValueError('Invalid importance')
        timestamp=instant(item['scheduled_at']) if item.get('scheduled_at') else None
        if timestamp is None or importance=='unknown': complete=False
        if timestamp and not start<=timestamp<end: raise ValueError('Event outside observed coverage')
        currency=item.get('currency')
        event={key:item.get(key) for key in ('title','country','currency','importance','actual','forecast','previous')}
        event['scheduled_at_utc']=timestamp.isoformat() if timestamp else None
        event['minutes_until']=(timestamp-now).total_seconds()/60 if timestamp else None
        event['usd_high_impact_within_60m']=bool(timestamp and currency=='USD' and importance=='high' and 0<=(timestamp-now).total_seconds()<=3600)
        events.append(event)
    result.update(status='observed' if complete else 'partial',events=events,
                  observed_at_utc=observed.isoformat(),coverage_start_utc=start.isoformat(),coverage_end_utc=end.isoformat(),
                  input='browser_or_user_observation_not_automatically_verified',
                  upcoming_usd_high_impact_count=sum(e['usd_high_impact_within_60m'] for e in events),
                  reason='Fresh visible observation' if complete else 'Coverage, timezone, timing or importance incomplete')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--calendar-json',type=Path)
    parser.add_argument('--interval',choices=market.INTERVALS,default='5m')
    parser.add_argument('--out',type=Path)
    args=parser.parse_args()
    now=dt.datetime.now(dt.timezone.utc)
    observation=workflow.read(args.calendar_json) if args.calendar_json else None
    result={'calendar':calendar_context(observation,now),'generated_at_utc':now.isoformat(),
            'decision_effect':'context_only','execution':'disabled',
            'limitation':'Economic releases can differ from forecasts; no mechanical above/below-forecast BTC buy/sell mapping is applied.'}
    try:
        result['price']=market.snapshot(args.interval)
    except Exception as exc:
        result['price']={'status':'unavailable','source':'Binance spot','error':str(exc)}
    text=json.dumps(result,indent=2,allow_nan=False)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(text+'\n',encoding='utf-8')
    print(text)


if __name__=='__main__':main()
