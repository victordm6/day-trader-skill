---
name: trader-analyst
description: Describe Bitcoin spot price, volume, sample returns, range and realized bar volatility from Binance candles. Bitcoin adapter; use BTC spot research without executing orders.
---

# BTC market analyst

For Ebinex, use `btc.py --venue ebinex --observation FILE` and read the
[separate fixed-payout workflow](../trader-bitcoin/references/ebinex.md).
That route reads local observations/confirmed results only; no Binance settlement
substitution, spot stop/target translation, demo orders or real orders.


This is the Bitcoin adapter, active in this fork. Use the shared BTC implementation via `btc.py`; the original stock scripts and [original instructions](references/upstream-SKILL.md) are retained only as legacy reference. Do not run legacy stock workflows for BTC.

From the repository root:

```sh
python trader-analyst/btc.py --interval 1h --out outputs/btc-market-analysis.json
```

BTC is not a company. Do not fabricate EPS, revenue, earnings, SEC statements or on-chain fundamentals. The statistics cover the displayed candle sample, not a six-month history.

The numeric examples are syntax demonstrations, not personal trade recommendations. Keep data times and provenance in reports. Use only closed candles; no future data, stock-session calendar, whole-share rounding, margin, shorts or Ebinex settlement assumptions. Read [shared workflow](../trader-bitcoin/references/workflow.md) when passing plans, sizing, risk or alerts between modules. Missing personal limits require user input.

No order is submitted by this adapter. Never request credentials. Historical or simulated results are not proof of future profitability.

For Investing.com calendar context alongside Binance price analysis, read [macro context](../trader-bitcoin/references/macro-context.md). Calendar availability is independent of price data and does not validate a trading direction.
