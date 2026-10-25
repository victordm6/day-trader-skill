---
name: trader-broker
description: Prepare a local Bitcoin paper ticket after recomputing risk with public market data. Bitcoin adapter; use BTC spot research without executing orders.
---

# BTC paper ticket

This is the Bitcoin adapter, active in this fork. Use the shared BTC implementation via `btc.py`; the original stock scripts and [original instructions](references/upstream-SKILL.md) are retained only as legacy reference. Do not run legacy stock workflows for BTC.

From the repository root:

```sh
python trader-broker/btc.py --ticket outputs/btc-ticket.json --cash 1000 --max-loss 10 --daily-limit 30 --daily-used 0 --min-rr 1.5 --out outputs/btc-paper-ticket.json
```

Execution is disabled. PAPER_READY is not a submitted or filled order. Never call the legacy stock broker for Bitcoin. No account credentials or private API endpoints are used.

The numeric examples are syntax demonstrations, not personal trade recommendations. Keep data times and provenance in reports. Use only closed candles; no future data, stock-session calendar, whole-share rounding, margin, shorts or Ebinex settlement assumptions. Read [shared workflow](../trader-bitcoin/references/workflow.md) when passing plans, sizing, risk or alerts between modules. Missing personal limits require user input.

No order is submitted by this adapter. Never request credentials. Historical or simulated results are not proof of future profitability.
