# BTC spot workflow

Run from the repository root. All amounts are USDT, quantity is fractional BTC. All outputs are local research artifacts. No exchange account, keys or orders are involved.

```sh
python trader-bitcoin/scripts/workflow.py --out outputs/entry.json entry --level 80000 --interval 5m
python trader-bitcoin/scripts/workflow.py --out outputs/plan.json plan --entry 80000 --stop 79000 --reward 3
python trader-bitcoin/scripts/workflow.py --out outputs/ticket.json size --plan outputs/plan.json --cash 1000 --max-loss 10 --cap 900 --step 0.00001 --cost-bps 11
python trader-bitcoin/scripts/workflow.py --out outputs/risk.json risk --ticket outputs/ticket.json --cash 1000 --max-loss 10 --daily-limit 30 --daily-used 0 --min-rr 1.5
python trader-bitcoin/scripts/workflow.py alerts --plan outputs/plan.json --state outputs/alert-state.json
```

Numbers above are syntax examples, not a trade recommendation. Obtain the user's entry/stop and cash/risk limits before producing a personal plan. The entry checker describes whether the latest completed close is above the supplied level; it does not prove a fresh crossing. Plans are long-only spot; no short or futures support. Reward is a gross multiple of stop distance. Sizing rounds BTC down to the user-supplied step, respecting cash including estimated entry costs, notional cap and stop risk including costs on both sides. 11 basis points per side is an illustrative assumption (fees plus slippage), not a verified Binance fee tier. Exchange filters are not fetched or certified.

Risk re-evaluates using the higher of the plan entry and the last completed 1m close. It blocks breached stop/target, insufficient cash, excessive trade/daily risk and insufficient net reward/risk. Daily used risk is provided by the user, not inferred from the exchange. Define the daily budget's timezone and reset it explicitly; the script neither tracks fills nor resets the budget automatically. PASS never places an order. A completed candle close is not an executable bid/ask quote.

Alerts check the last completed 1m close and persist each stop/target event once per plan identity. Preserve the state file between checks. There is no daemon or notification delivery: invoke through a separately authorized scheduler if requested. Polling can miss intrabar touches or round trips between checks; a threshold observation is not a fill or liquidated P&L. Stop and target observations are independent because there is no position lifecycle or execution engine. Do not present alerts as an OCO order.

`backtest.py` remains the historical simulation module. Do not transfer its hypothetical fixed payout results into the spot plan, or imply it validates a custom level/stop. The legacy stock broker, scanner, SEC earnings, news and Congress tools are not Bitcoin modules and are not registered by the plugin.
