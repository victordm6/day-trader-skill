---
name: trader-exit
description: Build a long-only Bitcoin spot stop and target plan. Bitcoin adapter; use BTC spot research without executing orders.
---

# BTC exit planner

For Ebinex, use `btc.py --venue ebinex --observation FILE` and read the
[separate fixed-payout workflow](../trader-bitcoin/references/ebinex.md).
That route reads local observations/confirmed results only; no Binance settlement
substitution, spot stop/target translation, demo orders or real orders.


This is the Bitcoin adapter, active in this fork. Use the shared BTC implementation via `btc.py`; the original stock scripts and [original instructions](references/upstream-SKILL.md) are retained only as legacy reference. Do not run legacy stock workflows for BTC.

From the repository root:

```sh
python trader-exit/btc.py --entry 80000 --stop 79000 --reward 3 --out outputs/btc-plan.json
```

Require user supplied entry/stop and reward multiple. No NYSE close or mandatory flat-by default applies to 24/7 BTC.

The numeric examples are syntax demonstrations, not personal trade recommendations. Keep data times and provenance in reports. Use only closed candles; no future data, stock-session calendar, whole-share rounding, margin, shorts or Ebinex settlement assumptions. Read [shared workflow](../trader-bitcoin/references/workflow.md) when passing plans, sizing, risk or alerts between modules. Missing personal limits require user input.

No order is submitted by this adapter. Never request credentials. Historical or simulated results are not proof of future profitability.

For the fixed breakout decision mode, see [decision rules](../trader-bitcoin/references/decision.md). Use `python trader-exit/btc.py --position position.json` to observe stop/target/time for a user-supplied actual long position. Exit observations do not depend on entry evidence passing.
