---
name: trader-budget
description: Size fractional BTC against cash, position cap and estimated stop loss including costs. Bitcoin adapter; use BTC spot research without executing orders.
---

# BTC position sizing

For Ebinex, use `btc.py --venue ebinex --observation FILE` and read the
[separate fixed-payout workflow](../trader-bitcoin/references/ebinex.md).
That route reads local observations/confirmed results only; no Binance settlement
substitution, spot stop/target translation, demo orders or real orders.


This is the Bitcoin adapter, active in this fork. Use the shared BTC implementation via `btc.py`; the original stock scripts and [original instructions](references/upstream-SKILL.md) are retained only as legacy reference. Do not run legacy stock workflows for BTC.

From the repository root:

```sh
python trader-budget/btc.py --plan outputs/btc-plan.json --cash 1000 --max-loss 10 --cap 900 --step 0.00001 --out outputs/btc-ticket.json
```

Use user limits. All money is USDT; quantity is BTC. The step and fees are assumptions, not verified exchange filters or fee tiers. Round down and account for costs.

The numeric examples are syntax demonstrations, not personal trade recommendations. Keep data times and provenance in reports. Use only closed candles; no future data, stock-session calendar, whole-share rounding, margin, shorts or Ebinex settlement assumptions. Read [shared workflow](../trader-bitcoin/references/workflow.md) when passing plans, sizing, risk or alerts between modules. Missing personal limits require user input.

No order is submitted by this adapter. Never request credentials. Historical or simulated results are not proof of future profitability.
