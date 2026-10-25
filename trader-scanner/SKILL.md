---
name: trader-scanner
description: Scan Binance BTCUSDT spot on 1m, 5m, 15m and 1h for descriptive trend, prior-20-bar breakout and volume conditions. Bitcoin adapter; use BTC spot research without executing orders.
---

# BTC chart scanner

This is the Bitcoin adapter, active in this fork. Use the shared BTC implementation via `btc.py`; the original stock scripts and [original instructions](references/upstream-SKILL.md) are retained only as legacy reference. Do not run legacy stock workflows for BTC.

From the repository root:

```sh
python trader-scanner/btc.py --out outputs/btc-scan.json
```

This scans one BTC pair across intervals, not thousands of assets. Partial data is explicitly marked; do not rank unavailable intervals.

The numeric examples are syntax demonstrations, not personal trade recommendations. Keep data times and provenance in reports. Use only closed candles; no future data, stock-session calendar, whole-share rounding, margin, shorts or Ebinex settlement assumptions. Read [shared workflow](../trader-bitcoin/references/workflow.md) when passing plans, sizing, risk or alerts between modules. Missing personal limits require user input.

No order is submitted by this adapter. Never request credentials. Historical or simulated results are not proof of future profitability.
