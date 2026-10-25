# Verification of Bitcoin adaptation

2026-10-25: 328 offline unit/integration tests passed, including 13 Bitcoin workflow tests and 500 deterministic sizing scenarios (seed 19). The independent backtest self-test passed coverage, causal indicators, next-bar entry, no overlap, payout arithmetic, aggregation, drawdown, ambiguous stop-first handling and cost deduction.

Commands (repository root):

```sh
python -m unittest discover -s tests -v
python trader-bitcoin/scripts/backtest.py --self-test
```

On restricted Windows runners, set TEMP and TMP to a writable local scratch directory before running legacy tests. Bitcoin integration tests use repository work/ for temporary files. No live orders or account access are part of these tests.

Regression fixes: risk now blocks an observed price at or below the stop even when the planned entry was higher. Sizing and alerts reject unsupported symbols/venues/sides and invalid stop/entry/target ordering. Plan creation rejects nonfinite or numerically collapsed targets. Integration coverage checks JSON handoffs and alert persistence across calls. Repository structure tests now recognize the BTC plugin and preserved upstream documentation.

This verifies software behavior; it is not a new profitability backtest or evidence of trading advantage.

## Integrated eleven-module BTC suite

2026-10-25: 336 offline tests passed after registering all eleven BTC adapters plus the research hub. Eight additional suite tests cover all eleven executable help entrypoints, partial multi-interval scans, absent volume baselines, RSS/Atom parsing, news deduplication and state preservation on parse failure, paper broker risk recomputation, source-attributed exposure distinctions and shared entry dispatch. The backtest self-test also passed through the timemachine adapter. All 12 SKILL.md files passed skill validation.

Public read-only smoke checks succeeded for Binance 5m/1h scanner snapshots and the Bitcoin Core feed. These checks are not automated profitability tests. News is limited to project announcements; disclosures are user-supplied and not automatically verified; analyst statistics describe a recent candle sample; the broker cannot send exchange orders or simulate fills.

Original stock skill documentation is preserved under each module's references/upstream-SKILL.md and its legacy document tests target those files. Active BTC registration and executable adapters have separate checks. Legacy Python stock tools are preserved unchanged.

## Additional edge and adapter handoff checks

2026-10-25: 344 tests passed (29 Bitcoin-specific tests, including the 500 seeded sizing scenarios). Eight new tests cover malformed candle timestamps, bad OHLC/volume, duplicate or insufficient data, complete scanner outage, disclosure field validation, preservation of news state during network failure, backlog/deduplication/date ordering and the full exit -> budget -> risk -> paper broker -> alerts adapter handoff. Paper tickets were blocked for breached stops, insufficient cash, exhausted daily risk, unsuitable reward/risk and unsupported symbols.

Regression fixes: candle open timestamps must align to the interval and close timestamps must match the interval end. Disclosure and news source URLs require an HTTPS host; disclosure entity/action fields must be nonempty text. The older gap fixture now uses an aligned duplicate so it continues to test continuity separately from timestamp validity. A public Binance 5m analyst smoke check passed after the stricter checks. The historical replay self-test also passed.

No trades were placed. These are software reliability tests, not additional strategy profitability results.
