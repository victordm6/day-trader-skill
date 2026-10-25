---
name: trader-exit
description: Build a long-only Bitcoin spot stop and target plan. Bitcoin adapter; use BTC spot research without executing orders.
---

# BTC exit planner

This is the Bitcoin adapter, active in this fork. Use the shared BTC implementation via `btc.py`; the original stock scripts and [original instructions](references/upstream-SKILL.md) are retained only as legacy reference. Do not run legacy stock workflows for BTC.

From the repository root:

```sh
python trader-exit/btc.py --entry 80000 --stop 79000 --reward 3 --out outputs/btc-plan.json
```

Require user supplied entry/stop and reward multiple. No NYSE close or mandatory flat-by default applies to 24/7 BTC.

The numeric examples are syntax demonstrations, not personal trade recommendations. Keep data times and provenance in reports. Use only closed candles; no future data, stock-session calendar, whole-share rounding, margin, shorts or Ebinex settlement assumptions. Read [shared workflow](../trader-bitcoin/references/workflow.md) when passing plans, sizing, risk or alerts between modules. Missing personal limits require user input.

No order is submitted by this adapter. Never request credentials. Historical or simulated results are not proof of future profitability.
