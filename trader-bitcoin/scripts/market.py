#!/usr/bin/env python3
"""Read-only Binance BTCUSDT spot snapshot. No keys or account endpoints."""
import argparse
import datetime as dt
import json
import math
import statistics
from pathlib import Path
import urllib.request

from backtest import indicators

BASE = 'https://data-api.binance.vision/api/v3'
INTERVALS = ('1m', '5m', '15m', '1h')


def public(path):
    request = urllib.request.Request(BASE + path, headers={'User-Agent': 'BitcoinResearch/1.0'})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def snapshot(interval):
    if interval not in INTERVALS:
        raise ValueError('Unsupported interval')
    rows = public('/klines?symbol=BTCUSDT&interval=' + interval + '&limit=300')
    # Server time avoids using a locally skewed clock to call a candle closed.
    now = int(public('/time')['serverTime'])
    duration = {'1m': 60, '5m': 300, '15m': 900, '1h': 3600}[interval]
    for row in rows:
        opened, closed_at = int(str(row[0])), int(str(row[6]))
        if opened % (duration*1000) or closed_at != opened+duration*1000-1:
            raise ValueError('Invalid candle timestamp alignment or close time')
    closed = [r for r in rows if int(r[6]) < now]
    if len(closed) < 100:
        raise ValueError('Insufficient completed candles')
    bars = [(int(r[0]) // 1000, *map(float, r[1:6])) for r in closed]
    for i, (t, o, h, l, c, v) in enumerate(bars):
        if not all(math.isfinite(x) for x in (o,h,l,c,v)) or not 0 < l <= min(o,c) <= max(o,c) <= h or v < 0:
            raise ValueError('Malformed market candle')
        if i and t != bars[i-1][0]+duration:
            raise ValueError('Market candle gap or duplicate')
    if now-int(closed[-1][6]) > duration*2000:
        raise ValueError('Stale completed candles')
    ema9, ema21, rsi, atr = indicators(bars)
    last = closed[-1]
    return {
        'venue': 'Binance spot', 'symbol': 'BTCUSDT', 'interval': interval,
        'observed_at_utc': dt.datetime.fromtimestamp(now / 1000, dt.timezone.utc).isoformat(),
        'last_completed_close_time_utc': dt.datetime.fromtimestamp(int(last[6]) / 1000, dt.timezone.utc).isoformat(),
        'completed_candles': len(bars), 'close': bars[-1][4], 'volume_btc': bars[-1][5],
        'ema9': ema9[-1], 'ema21': ema21[-1], 'rsi14': rsi[-1], 'atr14': atr[-1],
        'prior20_high': max(b[2] for b in bars[-21:-1]),
        'volume_ratio_prior20': bars[-1][5]/statistics.mean(b[5] for b in bars[-21:-1]) if sum(b[5] for b in bars[-21:-1]) else None,
        'sample_first_open': bars[0][1],
        'sample_return_pct': (bars[-1][4]/bars[0][1]-1)*100,
        'sample_range_low': min(b[3] for b in bars),
        'sample_range_high': max(b[2] for b in bars),
        'sample_bar_log_return_stdev_pct': statistics.stdev(math.log(bars[i][4]/bars[i-1][4]) for i in range(1,len(bars)))*100,
        'chart': 'https://www.tradingview.com/chart/?symbol=BINANCE%3ABTCUSDT',
        'source': BASE + '/klines',
        'limitation': 'Descriptive snapshot of completed candles; not an entry recommendation or streaming feed.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--interval', choices=INTERVALS, default='5m')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = json.dumps(snapshot(args.interval), indent=2, allow_nan=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(result + '\n', encoding='utf-8')
    print(result)


if __name__ == '__main__':
    main()
