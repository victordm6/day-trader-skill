---
name: trader-pelosi
description: Review source-attributed Bitcoin exposure disclosures provided by the user, distinguishing direct BTC, ETFs and corporate exposure. Bitcoin adapter; use BTC spot research without executing orders.
---

# BTC disclosure register

This is the Bitcoin adapter, active in this fork. Use the shared BTC implementation via `btc.py`; the original stock scripts and [original instructions](references/upstream-SKILL.md) are retained only as legacy reference. Do not run legacy stock workflows for BTC.

From the repository root:

```sh
python trader-pelosi/btc.py --records disclosures.json --out outputs/btc-disclosures.json
```

Legacy command name retained for compatibility. This is an input register, not automatic Pelosi, Congress or whale tracking. It does not assert anyone owns BTC. Records remain unverified until their primary source is checked; no invented holdings or transactions.

The numeric examples are syntax demonstrations, not personal trade recommendations. Keep data times and provenance in reports. Use only closed candles; no future data, stock-session calendar, whole-share rounding, margin, shorts or Ebinex settlement assumptions. Read [shared workflow](../trader-bitcoin/references/workflow.md) when passing plans, sizing, risk or alerts between modules. Missing personal limits require user input.

No order is submitted by this adapter. Never request credentials. Historical or simulated results are not proof of future profitability.
