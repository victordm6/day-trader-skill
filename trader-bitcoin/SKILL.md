---
name: trader-bitcoin
description: Analyze Binance BTCUSDT spot, check completed candles against a level, plan long spot stops and targets, size fractional BTC, check risk budgets, record threshold alerts and backtest 24/7 history. No order execution or Ebinex settlement replication.
---

# Bitcoin research adapter

For fixed-rule buy/wait/hold/exit research decisions, read [references/decision.md](references/decision.md). Use `scripts/decision.py`; missing or unfavorable historical evidence must produce WAIT, not an actionable buy. Historical screening is not independent strategy validation. Never fabricate a position from a candidate plan.

For entry-level checks, stop/target plans, fractional sizing, risk checks and persistent threshold alerts, read [references/workflow.md](references/workflow.md) and use `scripts/workflow.py`. Ask for missing cash/risk limits and entry/stop levels rather than inventing personal trading limits. All amounts are USDT; sizing uses BTC fractions, not whole stock shares. These modules produce local research files and do not send orders. Do not claim a passed risk check validates a strategy.

For a current descriptive snapshot, run `python scripts/market.py --interval 5m --out outputs/btc-snapshot.json` from this skill directory. Supported intervals: 1m, 5m, 15m, 1h. Use completed candles only. Report the source, interval and observation time; do not label a snapshot as a continuous feed. A request for monitoring still needs a duration and scheduling mechanism.

For the chart use [TradingView BINANCE:BTCUSDT](https://www.tradingview.com/chart/?symbol=BINANCE%3ABTCUSDT). Keep spot separate from perpetual futures and Ebinex synthetic or settlement quotes. Do not treat descriptive EMA/RSI values as validated entry signals.


Use `scripts/backtest.py` for a reproducible, standard-library-only analysis. Bitcoin trades continuously, including weekends. Do not apply NYSE sessions, opening bells, PDT rules, stock sizing or SEC earnings workflows to BTC. All eleven module folders now expose BTC adapters through `btc.py` and are registered by the plugin. Their original stock scripts remain legacy; do not call those scripts for BTC. See [suite map](references/suite.md).

```
python scripts/backtest.py --start 2026-04-23 --end 2026-10-23 --cache work/btc-data --out outputs/btc-analysis
```

Dates are UTC, start inclusive and end exclusive. Use completed days only. Download official Binance spot BTCUSDT 1-minute ZIP archives and verify their SHA256 CHECKSUM companions. A missing archive, checksum mismatch, duplicate, malformed candle or minute gap aborts rather than silently shortening the requested period. Daily archives cover partial months; monthly archives cover complete months. Cache files are reusable but are reverified.

The script compares two predefined research rules, without tuning parameters on the requested data:

- Trend baseline: closed 1-minute EMA9/EMA21 and Wilder RSI14 agree above/below 50. Entry at a future bar's open, exit at that bar's close. Report both immediate-next-open and one-bar-delayed entry. Fixed stake, 90% hypothetical payout, exact ties refunded. This is a directional-price proxy, not an Ebinex options backtest. A 1-minute bar cannot reproduce arbitrary intra-minute strikes or platform latency.
- Entry-style breakout: on closed 5-minute bars, close exceeds the previous 20 bars' high, volume is at least 1.5x their mean. Long only, next-bar open, ATR14 stop (1 ATR), 2R target, maximum 12 bars. One position at a time. Stop wins ambiguous intrabar touches; gap exits use the open. Spot results include fixed illustrative fees/slippage on both sides, not historical execution estimates.

Exclude warm-up bars from signals. Preserve UTC ordering and prohibit future information in indicator or signal calculation. Show the last two calendar months separately as a chronological holdout, as well as monthly stability, drawdown, trade count and assumptions. A holdout here is a chronological check, not proof of independence from all research decisions. Report daily-block-bootstrap uncertainty (seed 19) without portraying it as a forecast or Ebinex win probability.

Clearly distinguish directly displayed platform results, historical Binance results, simulated fixed-payout results and inferences. Do not merge deposits/withdrawals into trading profit. Do not optimize payout, indicators, expiry or risk size after inspecting results and then call them out-of-sample. Do not automatically open demo or real trades from research. Real-money operations require a separate user action.

Data format and provenance: https://github.com/binance/binance-public-data . Spot archives since 2025 use microseconds; normalize milliseconds or microseconds explicitly. Keep source URLs, hashes, coverage and strategy parameters in the output JSON.

For Investing.com calendar context alongside Binance price analysis, read [macro context](references/macro-context.md). Calendar availability is independent of price data and does not validate a trading direction.
