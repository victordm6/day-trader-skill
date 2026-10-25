#!/usr/bin/env python3
"""Bitcoin adapters for the eleven Day Trader modules. No order endpoints."""
import argparse
import datetime as dt
import hashlib
from email.utils import parsedate_to_datetime
import json
from pathlib import Path
import sys
import urllib.request
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

import backtest
import market
import workflow

MODULES = ('scanner','news','entry','exit','timemachine','budget','risk','broker','alerts','analyst','pelosi')
FEED = 'https://bitcoincore.org/en/rss.xml'


def scan(intervals):
    rows = []
    for interval in intervals:
        try:
            s = market.snapshot(interval)
            ratio = s['volume_ratio_prior20']
            rows.append(dict(s, breakout=s['close'] > s['prior20_high'],
                             breakout_with_volume=s['close'] > s['prior20_high'] and ratio is not None and ratio >= 1.5,
                             trend='up' if s['ema9'] > s['ema21'] else 'down' if s['ema9'] < s['ema21'] else 'flat'))
        except Exception as exc:
            rows.append({'interval': interval, 'status': 'unavailable', 'error': str(exc)})
    return {'symbol':'BTCUSDT','intervals':rows,'partial':any(r.get('status') == 'unavailable' for r in rows),
            'limitation':'Single asset across intervals; descriptive setup scan, not a ranked stock universe or recommendation.'}


def parse_feed(payload):
    root = ET.fromstring(payload)
    atom = '{http://www.w3.org/2005/Atom}'
    result = []
    nodes = root.findall('./channel/item') + root.findall(atom+'entry')
    for node in nodes:
        title = node.findtext('title') or node.findtext(atom+'title')
        link = node.findtext('link')
        if not link:
            child = node.find(atom+'link')
            link = child.get('href') if child is not None else None
        if not title or not link or not valid_https(link):
            continue
        published = node.findtext('pubDate') or node.findtext(atom+'published') or node.findtext(atom+'updated')
        result.append({'id':hashlib.sha256(link.encode()).hexdigest(), 'title':title,
                       'url':link,'published':published,'source':FEED})
    return result


def news(state_path, feed_file=None):
    if feed_file:
        payload = Path(feed_file).read_bytes()
    else:
        request = urllib.request.Request(FEED,headers={'User-Agent':'BitcoinResearch/1.0'})
        with urllib.request.urlopen(request,timeout=20) as response:
            payload = response.read(2_000_001)
        if len(payload) > 2_000_000:
            raise ValueError('Feed too large')
    items = parse_feed(payload)
    initial = not state_path.exists()
    state = workflow.read(state_path) if not initial else {'seen':[]}
    seen = set(state['seen'])
    unseen = []
    for item in items:
        if item['id'] not in seen:
            unseen.append(item)
            seen.add(item['id'])
    def date_key(item):
        try:
            return parsedate_to_datetime(item['published']).timestamp()
        except (ValueError, TypeError, AttributeError):
            try:
                return dt.datetime.fromisoformat(item['published'].replace('Z','+00:00')).timestamp()
            except (ValueError, TypeError, AttributeError):
                return 0
    unseen.sort(key=date_key,reverse=True)
    write(state_path, {'seen':sorted(seen | {item['id'] for item in items})})
    return {'items':unseen,'initial_historical_backlog':initial,'source':FEED,'input':'local_fixture' if feed_file else 'public_feed',
            'limitation':'Bitcoin Core project announcements only. Not comprehensive market, macro or regulatory news. Empty results do not mean no news.'}


def valid_https(value):
    if not isinstance(value,str):
        return False
    try:
        parsed=urlparse(value)
        return parsed.scheme == 'https' and bool(parsed.hostname) and not parsed.username and not parsed.password and not any(c.isspace() for c in value)
    except ValueError:
        return False


def disclosures(records):
    accepted, rejected = [], []
    for index, record in enumerate(records):
        try:
            if not isinstance(record,dict):
                raise ValueError('Record must be an object')
            if record.get('asset') != 'BTC' or record.get('exposure') not in ('direct','etf','company'):
                raise ValueError('Require BTC asset and explicit direct/etf/company exposure')
            if not valid_https(record['source_url']):
                raise ValueError('Require HTTPS primary source URL')
            if not all(isinstance(record.get(key),str) and record[key].strip() for key in ('entity','action')):
                raise ValueError('Missing entity or action')
            date = dt.date.fromisoformat(record['disclosed_date'])
            if date > dt.datetime.now(dt.timezone.utc).date():
                raise ValueError('Future disclosure date')
            accepted.append(dict(record,verification='user_supplied_source_not_independently_verified'))
        except (ValueError, KeyError, TypeError) as exc:
            rejected.append({'index':index,'reason':str(exc)})
    return {'records':accepted,'rejected':rejected,
            'limitation':'Source-backed input register only. No automatic Congress/whale tracking; ETF or company exposure is not a direct BTC purchase. No inference of undisclosed positions.'}


def paper_ticket(ticket, limits, snapshot):
    verdict = workflow.risk(ticket,snapshot['close'],**limits)
    return {'status':'PAPER_READY' if verdict['verdict']=='PASS' else 'BLOCK',
            'ticket':ticket,'risk':verdict,'price_source':snapshot,
            'execution':'disabled','exchange_order_sent':False,
            'limitation':'Local paper ticket only, not a fill, exchange order or profit record.'}


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in MODULES:
        raise SystemExit('Module required: '+', '.join(MODULES))
    module, rest = sys.argv[1], sys.argv[2:]
    if module in ('news','analyst') and '--context' in rest:
        import context
        sys.argv=[sys.argv[0]]+[arg for arg in rest if arg!='--context']
        context.main()
        return
    if module == 'entry' and '--strategy' in rest:
        index=rest.index('--strategy')
        if index+1 >= len(rest) or rest[index+1] != 'breakout':
            raise SystemExit('Supported strategy: breakout')
        import decision
        sys.argv=[sys.argv[0],'check']+rest[:index]+rest[index+2:]
        decision.main()
        return
    if module == 'exit' and '--position' in rest:
        import decision
        sys.argv=[sys.argv[0],'check']+rest
        decision.main()
        return
    # Reuse the same implementations and JSON handoffs instead of divergent stock rules.
    delegated = {'entry':'entry','exit':'plan','budget':'size','risk':'risk','alerts':'alerts'}
    if module in delegated:
        # --out belongs to the shared parent parser; allow it in adapter arguments.
        output = []
        if '--out' in rest:
            i = rest.index('--out'); output = rest[i:i+2]; rest = rest[:i]+rest[i+2:]
        sys.argv = [sys.argv[0]]+output+[delegated[module]]+rest
        workflow.main()
        return
    if module == 'timemachine':
        sys.argv = [sys.argv[0]]+rest
        backtest.main()
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path)
    if module == 'scanner':
        parser.add_argument('--intervals',nargs='+',choices=market.INTERVALS,default=list(market.INTERVALS))
    elif module == 'news':
        parser.add_argument('--state',type=Path,required=True)
        parser.add_argument('--feed-file',type=Path)
    elif module == 'analyst':
        parser.add_argument('--interval',choices=market.INTERVALS,default='1h')
    elif module == 'pelosi':
        parser.add_argument('--records',type=Path,required=True)
    elif module == 'broker':
        parser.add_argument('--ticket',required=True)
        for key in ('cash','max-loss','daily-limit','min-rr'):
            parser.add_argument('--'+key,type=workflow.positive,required=True)
        parser.add_argument('--daily-used',type=float,required=True)
    args = parser.parse_args(rest)
    if module == 'scanner':
        result = scan(args.intervals)
    elif module == 'news':
        result = news(args.state,args.feed_file)
    elif module == 'analyst':
        result = {'market':market.snapshot(args.interval),
                  'limitation':'Market price/volume/volatility sample only. BTC has no corporate revenue, earnings or EPS. No on-chain fundamentals are fetched.'}
    elif module == 'pelosi':
        records = workflow.read(args.records)
        if not isinstance(records,list):
            raise ValueError('Disclosure input must be a JSON list')
        result = disclosures(records)
    else:
        limits = {key:getattr(args,key) for key in ('cash','max_loss','daily_limit','daily_used','min_rr')}
        result = paper_ticket(workflow.read(args.ticket),limits,market.snapshot('1m'))
    result['module'] = 'trader-'+module
    result['generated_at_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    if args.out:
        write(args.out,result)
    print(json.dumps(result,indent=2,allow_nan=False))


if __name__ == '__main__':
    main()
