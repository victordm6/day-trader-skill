#!/usr/bin/env python3
"""BTC spot research workflow. Local plans and alerts only; never sends orders."""
import argparse
import datetime as dt
from decimal import Decimal, ROUND_DOWN
import json
import math
from pathlib import Path

from market import snapshot, INTERVALS


def positive(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError('Expected a finite positive number')
    return number


def plan(entry, stop, reward):
    entry, stop, reward = map(positive, (entry, stop, reward))
    if stop >= entry:
        raise ValueError('Spot long stop must be below entry')
    target = positive(entry + reward * (entry-stop))
    if target <= entry:
        raise ValueError('Target must exceed entry at numeric precision')
    return {'symbol': 'BTCUSDT', 'venue': 'Binance spot', 'side': 'long',
            'entry': entry, 'stop': stop, 'target': target,
            'reward_risk_before_costs': reward, 'execution': 'research_only'}


def validate_plan(p):
    if p.get('symbol') != 'BTCUSDT' or p.get('venue') != 'Binance spot' or p.get('side') != 'long':
        raise ValueError('Only BTCUSDT spot long is supported')
    entry, stop, target = map(positive, (p['entry'], p['stop'], p['target']))
    if not stop < entry < target:
        raise ValueError('Require stop < entry < target')
    return entry, stop, target


def size(p, cash, max_loss, cap, step, cost_bps):
    entry, stop, _ = validate_plan(p)
    cash, max_loss, cap, step = map(positive, (cash, max_loss, cap, step))
    cost_bps = float(cost_bps)
    if not math.isfinite(cost_bps) or cost_bps < 0:
        raise ValueError('Costs must be finite and nonnegative')
    entry, stop = positive(p['entry']), positive(p['stop'])
    if stop >= entry:
        raise ValueError('Invalid stop')
    cost = cost_bps / 10000
    risk_unit = entry - stop + cost * (entry + stop)
    qty = min(max_loss / risk_unit, cash / (entry*(1+cost)), cap / entry)
    quantity = float((Decimal(str(qty))/Decimal(str(step))).to_integral_value(rounding=ROUND_DOWN)*Decimal(str(step)))
    if quantity <= 0:
        raise ValueError('Budget cannot fund one quantity step')
    return dict(p, quantity_btc=quantity, notional_usdt=quantity*entry,
                estimated_loss_at_stop_usdt=quantity*risk_unit,
                estimated_cash_required_usdt=quantity*entry*(1+cost),
                cost_bps_each_side=cost_bps, quantity_step=step,
                caveat='Stop fills and costs are assumptions, not guaranteed maximum losses. Step is user supplied, not verified exchange filters.')


def risk(ticket, price, cash, max_loss, daily_limit, daily_used, min_rr):
    price, cash, max_loss, daily_limit, min_rr = map(positive, (price, cash, max_loss, daily_limit, min_rr))
    daily_used = float(daily_used)
    if not math.isfinite(daily_used) or daily_used < 0:
        raise ValueError('Daily risk used must be finite and nonnegative')
    q, entry, stop, target = map(positive, (ticket['quantity_btc'], ticket['entry'], ticket['stop'], ticket['target']))
    bps = float(ticket['cost_bps_each_side'])
    if not math.isfinite(bps) or bps < 0:
        raise ValueError('Invalid costs')
    cost = bps/10000
    base = max(entry, price)
    loss_unit = base-stop+cost*(base+stop)
    reward_unit = target-base-cost*(target+base)
    reasons = []
    if ticket.get('symbol') != 'BTCUSDT' or ticket.get('venue') != 'Binance spot' or ticket.get('side') != 'long':
        reasons.append('Only BTCUSDT spot long is supported')
    if not stop < price < target or not stop < entry < target:
        reasons.append('Price/entry must be between stop and target')
    loss = q*loss_unit
    rr = reward_unit/loss_unit if loss_unit > 0 else 0
    if loss > max_loss + 1e-9:
        reasons.append('Per-trade risk exceeded')
    if daily_used+loss > daily_limit + 1e-9:
        reasons.append('Daily risk budget exceeded')
    if q*base*(1+cost) > cash + 1e-9:
        reasons.append('Insufficient cash including costs')
    if rr < min_rr:
        reasons.append('Net reward/risk below minimum')
    return {'verdict': 'BLOCK' if reasons else 'PASS', 'reasons': reasons,
            'evaluated_price': price, 'estimated_loss_usdt': loss, 'net_reward_risk': rr,
            'daily_risk_used_user_supplied': daily_used,
            'execution': 'research_only', 'note': 'PASS is a budget check, not approval to place an order or evidence of an edge.'}


def alerts(p, price, state):
    validate_plan(p)
    price = positive(price)
    identity = [p['symbol'], p['entry'], p['stop'], p['target']]
    if state.get('plan') != identity:
        state = {'plan': identity, 'fired': []}
    events = []
    for kind, hit in [('stop', price <= p['stop']), ('target', price >= p['target'])]:
        if hit and kind not in state['fired']:
            events.append({'event': kind, 'observed_price': price, 'threshold': p[kind]})
            state['fired'].append(kind)
    return events, state


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    sub = parser.add_subparsers(dest='command', required=True)
    ent = sub.add_parser('entry')
    ent.add_argument('--level', type=positive, required=True)
    ent.add_argument('--interval', choices=INTERVALS, default='5m')
    pl = sub.add_parser('plan')
    for key in ('entry', 'stop', 'reward'):
        pl.add_argument('--'+key, type=positive, required=True)
    sz = sub.add_parser('size')
    sz.add_argument('--plan', required=True)
    for key in ('cash', 'max-loss', 'cap', 'step'):
        sz.add_argument('--'+key, type=positive, required=True)
    sz.add_argument('--cost-bps', type=float, default=11)
    rk = sub.add_parser('risk')
    rk.add_argument('--ticket', required=True)
    for key in ('cash', 'max-loss', 'daily-limit', 'min-rr'):
        rk.add_argument('--'+key, type=positive, required=True)
    rk.add_argument('--daily-used', type=float, required=True)
    al = sub.add_parser('alerts')
    al.add_argument('--plan', required=True)
    al.add_argument('--state', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'entry':
        s = snapshot(args.interval)
        result = dict(s, level=args.level, status='above_level' if s['close'] > args.level else 'waiting',
                      rule='Completed close above user level. Not a crossing event or validated recommendation.')
    elif args.command == 'plan':
        result = plan(args.entry, args.stop, args.reward)
    elif args.command == 'size':
        result = size(read(args.plan), args.cash, args.max_loss, args.cap, args.step, args.cost_bps)
    elif args.command == 'risk':
        s = snapshot('1m')
        result = risk(read(args.ticket), s['close'], args.cash, args.max_loss, args.daily_limit, args.daily_used, args.min_rr)
        result['price_source'] = s
    else:
        s = snapshot('1m')
        state = read(args.state) if args.state.exists() else {}
        events, state = alerts(read(args.plan), s['close'], state)
        args.state.parent.mkdir(parents=True, exist_ok=True)
        args.state.write_text(json.dumps(state, indent=2)+'\n', encoding='utf-8')
        result = {'events': events, 'price_source': s, 'limitation': 'One check of the last completed 1m close; intrabar touches and moves between checks may be missed. Not exchange fills.'}
    result['generated_at_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    output = json.dumps(result, indent=2, allow_nan=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output+'\n', encoding='utf-8')
    print(output)


if __name__ == '__main__':
    main()
