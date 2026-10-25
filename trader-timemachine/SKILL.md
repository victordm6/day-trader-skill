---
name: trader-timemachine
description: Backtest fixed Bitcoin research rules on checksum-verified Binance spot history. Bitcoin adapter; use BTC spot research without executing orders.
---

# BTC historical replay

This is the Bitcoin adapter, active in this fork. Use the shared BTC implementation via `btc.py`; the original stock scripts and [original instructions](references/upstream-SKILL.md) are retained only as legacy reference. Do not run legacy stock workflows for BTC.

From the repository root:

```sh
python trader-timemachine/btc.py --start 2026-04-23 --end 2026-10-23 --cache work/btc-data --out outputs/btc-analysis
```

Read ../trader-bitcoin/SKILL.md for exact strategy assumptions. These fixed-rule replays do not simulate an arbitrary custom plan. Fixed-payout proxy is separate from spot; no Ebinex settlement claims.

The numeric examples are syntax demonstrations, not personal trade recommendations. Keep data times and provenance in reports. Use only closed candles; no future data, stock-session calendar, whole-share rounding, margin, shorts or Ebinex settlement assumptions. Read [shared workflow](../trader-bitcoin/references/workflow.md) when passing plans, sizing, risk or alerts between modules. Missing personal limits require user input.

No order is submitted by this adapter. Never request credentials. Historical or simulated results are not proof of future profitability.
