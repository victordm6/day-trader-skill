---
name: trader-alerts
description: Check Bitcoin stop/target thresholds once and persist events to avoid duplicate alerts. Bitcoin adapter; use BTC spot research without executing orders.
---

# BTC threshold alerts

This is the Bitcoin adapter, active in this fork. Use the shared BTC implementation via `btc.py`; the original stock scripts and [original instructions](references/upstream-SKILL.md) are retained only as legacy reference. Do not run legacy stock workflows for BTC.

From the repository root:

```sh
python trader-alerts/btc.py --plan outputs/btc-plan.json --state outputs/btc-alert-state.json --out outputs/btc-alerts.json
```

This is one completed-1m-close check. Monitoring and notification delivery require a separately authorized scheduler. Intrabar touches may be missed; threshold observations are not fills or P&L.

The numeric examples are syntax demonstrations, not personal trade recommendations. Keep data times and provenance in reports. Use only closed candles; no future data, stock-session calendar, whole-share rounding, margin, shorts or Ebinex settlement assumptions. Read [shared workflow](../trader-bitcoin/references/workflow.md) when passing plans, sizing, risk or alerts between modules. Missing personal limits require user input.

No order is submitted by this adapter. Never request credentials. Historical or simulated results are not proof of future profitability.
