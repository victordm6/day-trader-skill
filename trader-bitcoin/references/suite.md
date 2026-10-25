# Eleven integrated BTC adapters

Run `python trader-MODULE/btc.py --help` for each module. The 11 adapters share `trader-bitcoin/scripts/suite.py`, `market.py`, `workflow.py` and `backtest.py`. Original stock tools remain unchanged but are legacy, not the registered skills' execution path. There are 12 registered skills: the hub plus eleven adapters.

| Module | BTC function | Artifact / boundary |
|---|---|---|
| scanner | BTC across 1m/5m/15m/1h; trend, prior20-high breakout and relative volume | btc-scan.json; descriptive, partial failures explicit |
| news | Bitcoin Core announcements plus assisted Investing economic calendar context | btc-news.json / btc-context.json; explicit source and coverage limits |
| entry | Completed close versus user level | btc-entry.json; not a fresh crossing detector |
| exit | User entry/stop and reward multiple | btc-plan.json; long spot only |
| timemachine | Fixed-rule 24/7 historical BTC replay | results.json and trade CSVs; not arbitrary plan Monte Carlo |
| budget | Fractional BTC, costs, cash/position/risk caps | btc-ticket.json |
| risk | Recompute cash, daily risk and net reward/risk | btc-risk.json; not execution authorization |
| broker | Recompute risk and render paper ticket | btc-paper-ticket.json; execution disabled, no fills |
| alerts | Stop/target observations once per plan | btc-alerts.json plus state; checks completed 1m closes |
| analyst | Price/volume, return/range and bar volatility sample | btc-market-analysis.json; not EPS or on-chain fundamentals |
| pelosi | Source-attributed BTC disclosure register | btc-disclosures.json; user-input only, no automatic tracker |

See each module's SKILL.md for example commands. Entry/stop, sizing and risk limits come from the user; example values are not suggestions. Scanner results and news do not automatically authorize a plan or execution. Plan -> budget -> risk -> broker/alerts use the same files documented in [workflow.md](workflow.md). Risk is recomputed by the paper broker, rather than trusting an old PASS file. No actual holdings, fills, cash or daily usage are inferred.

Disclosure input is a JSON array, for example:

```json
[{"entity":"Example entity","asset":"BTC","exposure":"etf","source_url":"https://example.org/primary-filing","disclosed_date":"2026-01-01","action":"reported holding"}]
```

This is a schema example, not an actual disclosure. Exposure must be `direct`, `etf` or `company`. The parser checks fields and records the source but does not independently verify it; inspect the primary source before presenting a disclosure as fact. No automatic Pelosi/Congress or wallet-address attribution exists.

Source documentation: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints and https://bitcoincore.org/en/rss.xml . Project announcements are not a comprehensive financial news feed. One-shot snapshots are not streaming. No private endpoints, credentials, real orders, futures or shorts are implemented.

For the user-selected Investing calendar with Binance price context, see [macro-context.md](macro-context.md). Use news/analyst `btc.py --context`; this mode requires fresh visible calendar observations and is not an automated data feed.
