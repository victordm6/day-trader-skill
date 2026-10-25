#!/usr/bin/env python3
"""Reproducible 24/7 BTC research. Standard library only; no account access."""
import argparse
import calendar
import csv
import datetime as dt
import hashlib
import io
import json
import math
from pathlib import Path
import random
import statistics as st
import urllib.request
import zipfile

UTC = dt.timezone.utc
BASE = 'https://data.binance.vision/data/spot'


def stamp(day):
    return int(dt.datetime.combine(day, dt.time(), UTC).timestamp())


def date_of(t):
    return dt.datetime.fromtimestamp(t, UTC).date().isoformat()


def month_add(day, n):
    m = day.year * 12 + day.month - 1 + n
    y, mm = divmod(m, 12)
    return dt.date(y, mm + 1, min(day.day, calendar.monthrange(y, mm + 1)[1]))


def archives(start, end):
    day = start
    while day < end:
        following = month_add(day.replace(day=1), 1)
        if day.day == 1 and following <= end:
            yield 'monthly', day.strftime('%Y-%m')
            day = following
        else:
            yield 'daily', day.isoformat()
            day += dt.timedelta(days=1)


def get_file(url, path):
    if not path.exists():
        request = urllib.request.Request(url, headers={'User-Agent': 'BTC-research/1.0'})
        with urllib.request.urlopen(request, timeout=60) as r:
            payload = r.read()
        path.write_bytes(payload)
    return path.read_bytes()


def download(start, end, cache):
    cache.mkdir(parents=True, exist_ok=True)
    bars, manifest = [], []
    for kind, label in archives(start, end):
        name = f'BTCUSDT-1m-{label}.zip'
        url = f'{BASE}/{kind}/klines/BTCUSDT/1m/{name}'
        payload = get_file(url, cache / name)
        checksum = get_file(url + '.CHECKSUM', cache / (name + '.CHECKSUM'))
        expected = checksum.decode().split()[0]
        digest = hashlib.sha256(payload).hexdigest()
        if digest != expected:
            raise ValueError(f'Checksum mismatch: {name}')
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            members = [n for n in z.namelist() if n.endswith('.csv')]
            if len(members) != 1:
                raise ValueError(f'Unexpected ZIP members: {name}')
            rows = csv.reader(io.TextIOWrapper(z.open(members[0]), encoding='utf-8'))
            for row in rows:
                raw = int(row[0])
                t = raw // (1_000_000 if raw >= 10**15 else 1000)
                if stamp(start) <= t < stamp(end):
                    bars.append((t, *map(float, row[1:6])))
        manifest.append({'url': url, 'sha256': digest, 'bytes': len(payload)})
        print(f'Verified {name}', flush=True)
    bars.sort()
    validate(bars, start, end)
    return bars, manifest


def validate(bars, start, end):
    expected = (end - start).days * 1440
    if len(bars) != expected:
        raise ValueError(f'Incomplete period: {len(bars)} minutes, expected {expected}')
    for i, (t, o, h, l, c, v) in enumerate(bars):
        if t != stamp(start) + i * 60:
            raise ValueError(f'Minute gap/duplicate at {date_of(t)}, index {i}')
        if not all(math.isfinite(x) for x in (o, h, l, c, v)) or not (0 < l <= min(o, c) <= max(o, c) <= h) or v < 0:
            raise ValueError(f'Malformed candle at {t}')


def indicators(bars):
    e9, e21, rsi, atr = [], [], [], []
    fast = slow = bars[0][4]
    gain = loss = trmean = 0.0
    for i, (_, o, h, l, c, v) in enumerate(bars):
        fast += 2 / 10 * (c - fast)
        slow += 2 / 22 * (c - slow)
        e9.append(fast)
        e21.append(slow)
        if i:
            delta = c - bars[i - 1][4]
            g, ll = max(delta, 0), max(-delta, 0)
            tr = max(h - l, abs(h - bars[i - 1][4]), abs(l - bars[i - 1][4]))
            if i <= 14:
                gain += g / 14
                loss += ll / 14
                trmean += tr / 14
            else:
                gain = (gain * 13 + g) / 14
                loss = (loss * 13 + ll) / 14
                trmean = (trmean * 13 + tr) / 14
        rsi.append(None if i < 14 else (50 if gain == loss == 0 else 100 if loss == 0 else 100 - 100 / (1 + gain / loss)))
        atr.append(None if i < 14 else trmean)
    return e9, e21, rsi, atr


def trend(bars, delay):
    fast, slow, rsi, _ = indicators(bars)
    trades, available = [], 0
    for i in range(100, len(bars) - delay - 1):
        if i < available:
            continue
        side = 1 if fast[i] > slow[i] and rsi[i] > 50 else -1 if fast[i] < slow[i] and rsi[i] < 50 else 0
        if not side:
            continue
        j = i + 1 + delay
        entry, exit_price = bars[j][1], bars[j][4]
        change = round((exit_price - entry) * side, 8)
        pnl = .9 if change > 0 else -1.0 if change < 0 else 0.0
        trades.append({'signal': bars[i][0] + 60, 'entry_time': bars[j][0], 'exit_time': bars[j][0] + 60,
                       'side': side, 'entry': entry, 'exit': exit_price, 'pnl': pnl,
                       'result': 'win' if pnl > 0 else 'loss' if pnl < 0 else 'tie'})
        available = j
    return trades


def aggregate(bars):
    result = []
    for i in range(0, len(bars), 5):
        chunk = bars[i:i+5]
        if len(chunk) != 5 or chunk[0][0] % 300:
            raise ValueError('Incomplete/alignment error in 5-minute aggregate')
        result.append((chunk[0][0], chunk[0][1], max(x[2] for x in chunk), min(x[3] for x in chunk), chunk[-1][4], sum(x[5] for x in chunk)))
    return result


def breakout(bars, fee_bps=10, delay=0, stop_atr=1):
    if not math.isfinite(fee_bps) or fee_bps<0 or type(delay) is not int or delay<0 or not math.isfinite(stop_atr) or stop_atr<=0:
        raise ValueError('Invalid research sensitivity parameters')
    _, _, _, atr = indicators(bars)
    trades, available = [], 0
    for i in range(100, len(bars) - 13 - delay):
        if i < available:
            continue
        past = bars[i-20:i]
        if bars[i][4] <= max(b[2] for b in past) or bars[i][5] < 1.5 * st.mean(b[5] for b in past):
            continue
        j = i + 1 + delay
        entry = bars[j][1] * 1.0001  # 1 bp adverse entry slippage
        risk = atr[i] * stop_atr
        if not risk or entry <= risk:
            continue
        stop, target = entry - risk, entry + 2 * risk
        exit_price, outcome, k = None, 'time', j + 11
        for k in range(j, j + 12):
            t, o, h, l, c, v = bars[k]
            if o <= stop:
                exit_price, outcome = o, 'stop_gap'
            elif o >= target:
                exit_price, outcome = o, 'target_gap'
            elif l <= stop:
                exit_price, outcome = stop, 'stop'
            elif h >= target:
                exit_price, outcome = target, 'target'
            if exit_price is not None:
                break
        if exit_price is None:
            exit_price = bars[k][4]
        fill = exit_price * .9999  # 1 bp adverse exit slippage
        net = fill - entry - (fee_bps/10000) * (entry + fill)
        trades.append({'signal': bars[i][0] + 300, 'entry_time': bars[j][0], 'exit_time': bars[k][0] + 300,
                       'side': 1, 'entry': entry, 'exit': fill, 'pnl': net / risk,
                       'gross_r': (exit_price - entry) / risk, 'result': outcome})
        available = k
    return trades


def summarize(trades):
    if not trades:
        return {'trades': 0}
    pnl = [t['pnl'] for t in trades]
    wins, losses = sum(x > 0 for x in pnl), sum(x < 0 for x in pnl)
    equity = peak = dd = 0.0
    for x in pnl:
        equity += x
        peak = max(peak, equity)
        dd = max(dd, peak - equity)
    return {'trades': len(trades), 'wins': wins, 'losses': losses, 'ties': len(trades)-wins-losses,
            'win_rate': wins/len(trades), 'mean': st.mean(pnl), 'total': sum(pnl), 'max_drawdown': dd,
            'profit_factor': sum(x for x in pnl if x > 0)/-sum(x for x in pnl if x < 0) if losses else None}


def bootstrap(trades, start, end):
    # Resample complete UTC days, retaining dependence within each day's trades.
    buckets = {(start + dt.timedelta(days=i)).isoformat(): [] for i in range((end-start).days)}
    for t in trades:
        # Attribute to entry date, including trades that exit at the end boundary.
        buckets[date_of(t['entry_time'])].append(t['pnl'])
    days = [(sum(v), len(v)) for v in buckets.values()]
    rng = random.Random(19)
    means = []
    for _ in range(10000):
        sample = rng.choices(days, k=len(days))
        n = sum(x[1] for x in sample)
        if n:
            means.append(sum(x[0] for x in sample)/n)
    means.sort()
    return {'seed': 19, 'replays': 10000, 'mean_per_trade_95pct_day_bootstrap': [means[int(.025*len(means))], means[int(.975*len(means))]]} if means else None


def self_test():
    day = dt.date(2026, 1, 1)
    synthetic = [(stamp(day)+i*60, 100+i*.01, 100.02+i*.01, 99.98+i*.01, 100.01+i*.01, 10.) for i in range(1440)]
    validate(synthetic, day, day+dt.timedelta(days=1))
    try:
        validate(synthetic[1:], day, day+dt.timedelta(days=1))
        raise AssertionError('missing candle accepted')
    except ValueError:
        pass
    prefix = indicators(synthetic[:300])
    full = indicators(synthetic)
    assert all(a == b[:300] for a, b in zip(prefix, full)), 'Indicators use future data'
    for delay in (0, 1):
        trades = trend(synthetic, delay)
        assert trades and all(t['entry_time'] >= t['signal']+delay*60 for t in trades)
        assert all(a['exit_time'] <= b['entry_time'] for a, b in zip(trades, trades[1:])), 'Overlapping trades'
        assert all(t['pnl'] == .9 for t in trades)
    assert len(aggregate(synthetic)) == 288
    assert summarize([{'pnl': x} for x in (.9, -1, -1, .9)])['max_drawdown'] == 2
    five = [(stamp(day)+i*300, 100., 101., 99., 100., 10.) for i in range(150)]
    five[100] = (five[100][0], 100., 103., 99., 102., 30.)
    five[101] = (five[101][0], 102., 110., 90., 102., 10.)
    simulated = breakout(five)
    assert len(simulated) == 1 and simulated[0]['result'] == 'stop', 'Ambiguous candle not stop-first'
    assert simulated[0]['pnl'] < simulated[0]['gross_r'], 'Costs not deducted'
    assert simulated[0]['entry_time'] >= simulated[0]['signal']
    print('PASS: coverage, causality, future entry, non-overlap, payouts, aggregation, drawdown, ambiguous stop, costs')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--start', type=dt.date.fromisoformat)
    p.add_argument('--end', type=dt.date.fromisoformat)
    p.add_argument('--cache', type=Path, default=Path('work/btc-data'))
    p.add_argument('--out', type=Path, default=Path('outputs/btc-analysis'))
    p.add_argument('--self-test', action='store_true')
    args = p.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.start or not args.end or args.start >= args.end:
        p.error('Require --start < --end, ISO dates, exclusive end')
    if args.end > dt.datetime.now(UTC).date():
        p.error('End must exclude the current unfinished UTC day')
    bars, manifest = download(args.start, args.end, args.cache)
    cutoff = month_add(args.end, -2)
    args.out.mkdir(parents=True, exist_ok=True)
    strategies = {'trend_m1_next_open': trend(bars, 0), 'trend_m1_delayed_open': trend(bars, 1), 'breakout_m5_spot': breakout(aggregate(bars))}
    daily = []
    for i in range(0, len(bars), 1440):
        x = bars[i:i+1440]
        daily.append({'date': date_of(x[0][0]), 'open': x[0][1], 'high': max(b[2] for b in x), 'low': min(b[3] for b in x), 'close': x[-1][4]})
    peak, dd = bars[0][4], 0.
    for b in bars:
        peak = max(peak, b[4])
        dd = max(dd, 1-b[4]/peak)
    results = {'symbol': 'BTCUSDT', 'venue': 'Binance spot', 'start_utc': str(args.start), 'end_exclusive_utc': str(args.end),
               'holdout_start_utc': str(cutoff), 'minutes': len(bars), 'days': len(daily), 'manifest': manifest,
               'market': {'first_open': bars[0][1], 'last_close': bars[-1][4], 'return_pct': (bars[-1][4]/bars[0][1]-1)*100,
                          'high': max(b[2] for b in bars), 'low': min(b[3] for b in bars), 'max_close_drawdown_pct': dd*100},
               'assumptions': {'trend': 'EMA9/21, Wilder RSI14, warmup100, fixed 1 unit stake, 90% payout, tie refund, next 1m open/close, delay0 and1, no overlap',
                               'breakout': '5m long close>prior20high, volume>=1.5xprior20mean, nextopen, ATR14 stop,2R target,12bar timeout, stop-first,10bp fee+1bp slippage EACH side'}, 'strategies': {}}
    for name, trades in strategies.items():
        months = sorted({date_of(t['entry_time'])[:7] for t in trades})
        holdout = [t for t in trades if t['entry_time'] >= stamp(cutoff)]
        training = [t for t in trades if t['exit_time'] <= stamp(cutoff)]
        results['strategies'][name] = {'overall': summarize(trades), 'first_four_months': summarize(training), 'last_two_months': summarize(holdout),
            'monthly': {m: summarize([t for t in trades if date_of(t['entry_time']).startswith(m)]) for m in months},
            'holdout_uncertainty': bootstrap(holdout, cutoff, args.end)}
        with (args.out / (name+'.csv')).open('w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(trades[0]) if trades else ['entry_time'])
            w.writeheader()
            w.writerows(trades)
    (args.out/'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    with (args.out/'daily.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(daily[0])); w.writeheader(); w.writerows(daily)
    print(json.dumps({k:v for k,v in results.items() if k not in ('manifest', 'assumptions')}, indent=2))


if __name__ == '__main__':
    main()
