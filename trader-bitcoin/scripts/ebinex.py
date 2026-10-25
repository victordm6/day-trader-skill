#!/usr/bin/env python3
"""Offline Ebinex contract inspection and confirmed-settlement accounting. No I/O to accounts."""
import argparse
import datetime as dt
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path

UTC = dt.timezone.utc
MODULES = ('scanner', 'news', 'entry', 'exit', 'timemachine', 'budget', 'risk',
           'broker', 'alerts', 'analyst', 'pelosi')


def number(value, label, positive=False):
    if isinstance(value, bool):
        raise ValueError(label + ': require a finite number')
    try:
        n = Decimal(str(value))
    except InvalidOperation:
        raise ValueError(label + ': require a finite number')
    if not n.is_finite() or n < 0 or (positive and n == 0):
        raise ValueError(label + ': invalid nonnegative amount')
    return n


def timestamp(value):
    t = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if t.tzinfo is None or t.utcoffset() is None:
        raise ValueError('Timestamp requires an explicit timezone')
    return t.astimezone(UTC)


def text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Missing text: ' + field)
    return value


def inspect(observation, now=None):
    now = now or dt.datetime.now(UTC)
    observed = timestamp(observation['observed_at_utc'])
    age = (now - observed).total_seconds()
    reasons = []
    for key, expected in [('venue', 'ebinex'), ('product', 'digital_fixed_payout'),
                          ('symbol', 'BTCUSDX'), ('mode', 'demo')]:
        if observation.get(key) != expected:
            reasons.append('Require %s=%s for this research profile' % (key, expected))
    if age < 0 or age > 90:
        reasons.append('Observation is future-dated or older than 90 seconds')
    expiry = number(observation['expiry_seconds'], 'expiry_seconds', True)
    if expiry != 60:
        reasons.append('Observed research profile requires M1 (60 seconds)')
    payout = number(observation['payout_ratio'], 'payout_ratio')
    if payout <= 0 or payout > 1:
        reasons.append('Payout must be a profit/stake ratio in (0,1]')
    stake = number(observation['prepared_stake_usdt'], 'prepared_stake_usdt', True)
    text(observation.get('evidence'), 'evidence')
    if observation.get('source_kind') != 'visible_ui_observation':
        reasons.append('Require visible UI evidence; Binance is not an Ebinex observation')
    if observation.get('synthetic_example') is True:
        reasons.append('Synthetic schema example; not a platform observation')
    return dict(status='BLOCK' if reasons else 'OBSERVED_ONLY', reasons=reasons,
                venue='ebinex', product='digital_fixed_payout', observation=observation,
                observation_age_seconds=age, prepared_stake_is_investment=False,
                theoretical_break_even_without_fees=float(1/(1+payout)) if payout else None,
                maximum_stake_loss_before_fees=float(stake),
                rule_14410=dict(compatible=False, reason='Frozen spot rule holds 92160 seconds, '
                    'uses Binance BTCUSDT and proportional price returns; M1 expiry/payout is a different strategy.'),
                unresolved_contract_fields=['strike_time_rule', 'settlement_price_source',
                    'tie_rule', 'fees', 'entry_latency'],
                execution='disabled', order_sent=False, strategy_validated=False)


def analyze(ledger, initial_balance):
    """Only account for supplied explicit settlements; never infer a fill from balance."""
    initial = number(initial_balance, 'initial_balance', True)
    if type(ledger.get('coverage_complete')) is not bool:
        raise ValueError('coverage_complete must be explicit true/false')
    text(ledger.get('coverage_evidence'), 'coverage_evidence')
    if ledger.get('mode') not in ('demo', 'real'):
        raise ValueError('Explicit single account mode required')
    records = ledger['trades']
    if not isinstance(records, list):
        raise ValueError('trades must be an array')
    ids, closed, pending = set(), [], []
    for row in records:
        ident = text(row.get('id'), 'id')
        if ident in ids:
            raise ValueError('Duplicate operation id: ' + ident)
        ids.add(ident)
        if row.get('mode') != ledger['mode'] or row.get('symbol') != 'BTCUSDX':
            raise ValueError('Do not mix accounts or instruments')
        if row.get('product') != 'digital_fixed_payout':
            raise ValueError('Spot history is not an Ebinex settlement ledger')
        status = row.get('status')
        if status in ('PENDING', 'OPEN', 'UNCERTAIN'):
            pending.append({'id': ident, 'status': status})
            continue
        if status not in ('WIN', 'LOSS', 'TIE'):
            raise ValueError('Require explicit WIN/LOSS/TIE or unresolved status')
        text(row.get('result_evidence'), 'result_evidence')
        if row.get('confirmation') != 'explicit_platform_result':
            raise ValueError('Balance changes or chart markers cannot confirm settlement')
        entry = timestamp(row['entry_utc']); expiry = timestamp(row['expiry_utc'])
        settled = timestamp(row['settled_utc'])
        if not entry < expiry <= settled:
            raise ValueError('Invalid entry/expiry/settlement ordering')
        if row.get('direction') not in ('BUY', 'SELL'):
            raise ValueError('Explicit direction required')
        stake = number(row['stake_usdt'], 'stake_usdt', True)
        payout = number(row['payout_ratio'], 'payout_ratio', True)
        if payout > 1:
            raise ValueError('Payout is a ratio, not percent or total credit')
        fees = number(row['fees_usdt'], 'fees_usdt')
        credit = number(row['cash_return_usdt'], 'cash_return_usdt')
        if status == 'WIN': expected = stake*(1+payout)
        elif status == 'LOSS': expected = Decimal(0)
        else:
            if row.get('tie_rule') not in ('refund', 'loss'):
                raise ValueError('Tie contract rule must be explicit')
            expected = stake if row['tie_rule'] == 'refund' else Decimal(0)
        if abs(credit-expected) > Decimal('.005'):
            raise ValueError('Credit contradicts explicit status/payout: ' + ident)
        closed.append(dict(id=ident, status=status, settled_utc=settled.isoformat(),
                           gross=float(credit-stake), net=float(credit-stake-fees),
                           fees=float(fees), stake=float(stake)))
    closed.sort(key=lambda r: (r['settled_utc'], r['id']))
    balance = peak = initial; dd = Decimal(0)
    for row in closed:
        balance += Decimal(str(row['net'])); peak = max(peak, balance)
        dd = max(dd, 1-balance/peak); row['closed_pnl_balance_usdt'] = float(balance)
    wins = sum(r['status'] == 'WIN' for r in closed)
    complete = ledger['coverage_complete'] and not pending
    return dict(source='user_supplied_explicit_settlements_not_independently_verified',
                mode=ledger['mode'], coverage_complete_claim=ledger['coverage_complete'],
                complete_results=complete, closed_count=len(closed), unresolved=pending,
                wins=wins, losses=sum(r['status']=='LOSS' for r in closed),
                ties=sum(r['status']=='TIE' for r in closed),
                observed_closed_win_rate=wins/len(closed) if closed else None,
                observed_closed_net_usdt=sum(r['net'] for r in closed),
                complete_net_usdt=float(balance-initial) if complete else None,
                initial_balance_usdt=float(initial), closed_pnl_balance_usdt=float(balance),
                closed_balance_drawdown=float(dd), trades=closed,
                limitation='Closed-P&L accounting only, not cash available, open-position equity, '
                           'a price backtest, or evidence of strategy profitability. Deposits/withdrawals excluded.',
                execution='disabled', order_sent=False, strategy_validated=False)


def run_module(module, observation, ledger=None, initial_balance=None, now=None, limits=None):
    if module not in MODULES:
        raise ValueError('Unknown Ebinex module')
    result = inspect(observation, now)
    result['module'] = module
    if ledger is not None:
        if initial_balance is None:
            raise ValueError('Ledger analysis requires explicit initial balance')
        if ledger.get('mode') != observation.get('mode'):
            raise ValueError('Observation and ledger modes differ')
        result['settlements'] = analyze(ledger, initial_balance)
    if module in ('budget', 'risk'):
        reasons = ['Observation is blocked'] if result['status'] == 'BLOCK' else []
        limits = limits or {}
        for key in ('cash', 'max_loss', 'daily_limit', 'daily_used', 'fees'):
            if limits.get(key) is None: reasons.append('Missing limit: ' + key)
        if all(limits.get(k) is not None for k in ('cash','max_loss','daily_limit','daily_used','fees')):
            vals = {k:number(v,k) for k,v in limits.items()}
            loss = number(observation['prepared_stake_usdt'],'stake',True)+vals['fees']
            if loss > vals['cash']: reasons.append('Stake plus fees exceeds cash')
            if loss > vals['max_loss']: reasons.append('Full stake loss exceeds per-operation limit')
            if loss+vals['daily_used'] > vals['daily_limit']: reasons.append('Daily loss budget exceeded')
        result['risk'] = dict(status='BLOCK' if reasons else 'WITHIN_SUPPLIED_LIMITS',reasons=reasons,
                              strategy_validated=False, authorizes_order=False)
    if module == 'broker': result['status'] = 'EXECUTION_DISABLED'
    elif module in ('news', 'pelosi'):
        result['module_scope'] = 'No automated Ebinex news/disclosure feed; supplied observations only'
    elif module in ('entry', 'exit'):
        result['decision'] = 'WAIT'
        result['decision_reason'] = 'No validated Ebinex entry/expiry strategy; no spot stop/target translation'
    elif module == 'timemachine' and ledger is None:
        result['data_status'] = 'WAIT_FOR_EBINEX_SETTLEMENT_DATA'
    return result


def module_main(module, argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--venue', choices=['ebinex'], default='ebinex')
    p.add_argument('--observation', type=Path, required=True)
    p.add_argument('--ledger', type=Path)
    p.add_argument('--initial-balance', type=str)
    for name in ('cash', 'max-loss', 'daily-limit', 'daily-used', 'fees'):
        p.add_argument('--'+name)
    p.add_argument('--out', type=Path)
    a = p.parse_args(argv)
    try:
        obs = json.loads(a.observation.read_text(encoding='utf-8'))
        ledger = json.loads(a.ledger.read_text(encoding='utf-8')) if a.ledger else None
        result = run_module(module, obs, ledger, a.initial_balance,
            limits={k:getattr(a,k) for k in ('cash','max_loss','daily_limit','daily_used','fees')})
        result['inputs_sha256'] = {str(f):hashlib.sha256(f.read_bytes()).hexdigest()
                                  for f in [a.observation]+([a.ledger] if a.ledger else [])}
        payload = json.dumps(result, indent=2, allow_nan=False)+'\n'
    except (ValueError, KeyError, TypeError, AttributeError, OSError) as exc:
        p.error(str(exc))
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(payload,encoding='utf-8')
    print(payload, end='')


if __name__ == '__main__':
    module_main('analyst')
