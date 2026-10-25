---
name: trader-entry
description: Check a user supplied BTCUSDT level against completed Binance spot candles. Bitcoin adapter; use BTC spot research without executing orders.
---

# BTC entry level checker

This is the Bitcoin adapter, active in this fork. Use the shared BTC implementation via `btc.py`; the original stock scripts and [original instructions](references/upstream-SKILL.md) are retained only as legacy reference. Do not run legacy stock workflows for BTC.

From the repository root:

```sh
python trader-entry/btc.py --level 80000 --interval 5m --out outputs/btc-entry.json
```

Level is supplied by the user. Above level is descriptive, not proof of a fresh crossing or a validated entry signal.

The numeric examples are syntax demonstrations, not personal trade recommendations. Keep data times and provenance in reports. Use only closed candles; no future data, stock-session calendar, whole-share rounding, margin, shorts or Ebinex settlement assumptions. Read [shared workflow](../trader-bitcoin/references/workflow.md) when passing plans, sizing, risk or alerts between modules. Missing personal limits require user input.

No order is submitted by this adapter. Never request credentials. Historical or simulated results are not proof of future profitability.

For the fixed breakout decision mode, see [decision rules](../trader-bitcoin/references/decision.md). Use `python trader-entry/btc.py --strategy breakout --evidence reports/btc-breakout-evidence-2026-10-23.json`. The recorded evidence is unfavorable; return WAIT. Do not substitute a manual level check for a passing research gate.
