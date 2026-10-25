---
name: trader-bitcoin
description: Analyze BTCUSDT spot history from Binance and backtest fixed Bitcoin rules over continuous 24/7 data. Use for Bitcoin historical analysis, six-month backtests, or research adaptations of trader-entry. Does not execute orders or claim to reproduce Ebinex settlement prices.
---

# Bitcoin research adapter

For a current descriptive snapshot, run `python scripts/market.py --interval 5m --out outputs/btc-snapshot.json` from this skill directory. Supported intervals: 1m, 5m, 15m, 1h. Use completed candles only. Report the source, interval and observation time; do not label a snapshot as a continuous feed. A request for monitoring still needs a duration and scheduling mechanism.

For the chart use [TradingView BINANCE:BTCUSDT](https://www.tradingview.com/chart/?symbol=BINANCE%3ABTCUSDT). Keep spot separate from perpetual futures and Ebinex synthetic or settlement quotes. Do not treat descriptive EMA/RSI values as validated entry signals.


Use `scripts/backtest.py` for a reproducible, standard-library-only analysis. Bitcoin trades continuously, including weekends. Do not apply NYSE sessions, opening bells, PDT rules, stock sizing or SEC earnings workflows to BTC. The legacy equity folders remain for upstream reference and are not registered by this plugin.

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
