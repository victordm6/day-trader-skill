---
name: trader-news
description: Provide BTC macro context using the Investing.com economic calendar with Binance prices, and deduplicate Bitcoin Core announcements. Use for Bitcoin news and scheduled economic events; no order execution.
---

# BTC project news

For Ebinex, use `btc.py --venue ebinex --observation FILE` and read the
[separate fixed-payout workflow](../trader-bitcoin/references/ebinex.md).
That route reads local observations/confirmed results only; no Binance settlement
substitution, spot stop/target translation, demo orders or real orders.


This is the Bitcoin adapter, active in this fork. Use the shared BTC implementation via `btc.py`; the original stock scripts and [original instructions](references/upstream-SKILL.md) are retained only as legacy reference. Do not run legacy stock workflows for BTC.

From the repository root:

```sh
python trader-news/btc.py --state outputs/btc-news-state.json --out outputs/btc-news.json
```

Coverage is Bitcoin Core announcements only, not comprehensive market news. On request use available browsing tools to supplement with primary-source macro/regulatory news, cite sources, and label unavailable coverage. Never infer no news from an empty feed.

The numeric examples are syntax demonstrations, not personal trade recommendations. Keep data times and provenance in reports. Use only closed candles; no future data, stock-session calendar, whole-share rounding, margin, shorts or Ebinex settlement assumptions. Read [shared workflow](../trader-bitcoin/references/workflow.md) when passing plans, sizing, risk or alerts between modules. Missing personal limits require user input.

No order is submitted by this adapter. Never request credentials. Historical or simulated results are not proof of future profitability.

For the user-selected Investing.com economic calendar plus price context, read [macro context](../trader-bitcoin/references/macro-context.md). Use `btc.py --context --calendar-json outputs/calendar-observation.json`. Calendar input is assisted visible observation, not an automatic scraper. Preserve unknown fields and timezone/coverage limits.
