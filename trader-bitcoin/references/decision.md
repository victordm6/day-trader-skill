# Fixed research decision rule

Entry rule `btc-m5-breakout20-volume1.5-atr14-stop1-target2-time12-v1`: completed 5m BTCUSDT spot close strictly exceeds the previous 20 highs; volume >= 1.5 times the previous 20 volumes. ATR14 is frozen at the signal. Historical entry is the next bar open with 1bp adverse slippage. Stop is 1 ATR below entry, target 2 ATR above entry, maximum holding 12 five-minute bars. Spot long only. Fee assumption: 10bp per side plus 1bp slippage per side. No EMA/RSI filter is added after inspecting results.

```sh
python trader-bitcoin/scripts/decision.py validate --start 2026-04-23 --end 2026-10-23 --cache work/btc-data --out outputs/evidence.json
python trader-entry/btc.py --strategy breakout --evidence reports/btc-breakout-evidence-2026-10-23.json --out outputs/decision.json
python trader-exit/btc.py --position position.json --out outputs/exit-decision.json
```

The validation downloads/reverifies Binance archives and replays exactly the historical breakout implementation. The last two months form a chronological research segment. The research gate requires >=100 segment trades, positive net mean and positive lower endpoint of a 95% daily bootstrap interval. It rejects missing/mismatched reports, nonfinite statistics and reports ending more than 30 days ago or in the future. These are screening criteria, not proof of an edge; previously inspected history is not an independent holdout.

Outputs:

- `WAIT`: setup absent or historical research criteria not met. `technical_setup` can still be true. A provisional reference plan is not a position.
- `BUY_CANDIDATE`: both technical setup and research criteria met; research only, not an order, fill or personalized recommendation. Recheck actual entry, size and risk separately. A stored report is local evidence, not an authenticated certificate.
- `HOLD`: user-supplied long position has no observed exit condition.
- `SELL_EXIT`: user-supplied position observed at/below stop, at/above target, or held at least 60 minutes. It means exit a long position, never short BTC. A failed entry research gate does not block exits.

`position.json` must contain actual user-supplied information, never automatically converted from the provisional plan:

```json
{"symbol":"BTCUSDT","venue":"Binance spot","side":"long","entry":80000,"stop":79900,"target":80200,"quantity_btc":0.001,"entered_at_utc":"2026-10-25T12:00:00+00:00"}
```

Values above are schema examples, not a trading suggestion. To match this rule, stop/target should be based on actual entry and the signal's frozen ATR; positions with other levels are checked as supplied, not claimed as this backtest. Entry checks use completed 5m candles and exits completed 1m closes. Intrabar touches, gaps and movement between checks may be missed; historical OHLC exits are more detailed than periodic close observations. There is no automatic position tracking, order execution or continuous monitor. Candidate checks can repeat for the same candle.

## Recorded result

2026-04-23 through 2026-10-23 exclusive: 263,520 verified minute candles; 1,143 simulated spot trades. Last two months: 378 trades, mean -2.367746 R, profit factor 0.049784, daily bootstrap mean interval [-2.805815, -1.976330] R/trade. R is price risk at the stop; costs can exceed one R when stops are tight. This is not account P&L or a percentage return. `NOT_SUPPORTED`: no buy candidate is enabled by this report. Parameters were not retuned to remove this unfavorable result.

Full evidence including source hashes is in [reports](../../reports/btc-breakout-evidence-2026-10-23.json). This test reused previously examined history and cannot establish independent validation. Software tests remain separate from profitability research.
