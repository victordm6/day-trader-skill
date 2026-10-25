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

## Fixed decision research

2026-10-25: added buy/wait and long-position hold/exit decisions with six regression tests for evidence gating, missing/mismatched/stale/future/invalid evidence, technical conditions, stop/target/timeout, and malformed positions. Replayed verified 183-day Binance data without tuning: 1,143 spot trades, last-two-month segment 378 trades, mean -2.367746 R after illustrative costs. Daily bootstrap interval entirely negative. The included report blocks buy candidates; no validated edge is claimed. Full report and source hashes are versioned in reports/.

Final verification: 350 offline tests passed. A public Binance entry-adapter smoke check returned WAIT with research_gate_passed=false. No exchange order was sent.

## Decision evidence and position regressions

2026-10-25: 355 offline tests passed. Five new decision tests exercise malformed evidence (non-object, empty/reversed uncertainty bounds, infinite sample count), 100-trade and 30-day boundaries, exact volume/breakout thresholds, nonfinite observations, provisional-plan rejection and exit evaluation with a corrupt entry-evidence file. Evidence counts now require integers and intervals require two finite ordered endpoints. Exit checks ignore entry-evidence files because that evidence must not block an exit. Provisional reference plans cannot masquerade as actual positions. The backtest self-test passed again.

No strategy parameters were optimized and no new profitability claim is made. The recorded negative historical result still blocks buy candidates. No account access or trades were performed during these tests.

## Investing economic calendar context

2026-10-25: 363 offline tests passed, including eight macro-context tests. Coverage includes explicit offset conversion to UTC, high-impact USD event proximity, stale/future observation rejection, missing event time/importance, incomplete coverage, unexpected source and timezone-naive inputs, both news/analyst adapter routes, and explicit price-source failure. The three revised skills passed validation.

The public calendar was inspected through web browsing; visible extraction did not establish all event times/importance or complete coverage. The implementation therefore uses assisted browser/user observations rather than claiming automatic calendar scraping. No Investing data is redistributed in this repository; test events are synthetic. A fresh local observation is required for calendar status observed; absent input stays unavailable. Binance remains the price source, macro context does not enable buy candidates or alter the negative strategy evidence gate.

## 10,000 generated property scenarios

2026-10-25: executed exactly 10,000 additional deterministic offline scenarios, seed 20261025. All passed: sizing 2,500; risk 2,500; entry decisions 2,000; position exits 1,500; macro context 1,500. The existing 363-test suite also passed. No production rule or strategy parameter changed in this run.

```sh
python tests/stress_bitcoin.py --out reports/stress-10000.json
```

The runner checks sizing caps using decimal arithmetic, quantity grid alignment, monotonicity under higher costs, risk verdicts versus independently evaluated constraints, evidence/setup gating, stop/target/timeout priorities, timezone offsets, observation freshness and event proximity. Underfunded minimum quantity is an expected rejection, not a valid order; the first harness run had to correct its assumption on this case. No application bug was established by that initial harness failure.

Report: reports/stress-10000.json, with per-family counts, failures and a reproducibility digest of successful cases. These are generated scenarios, not 10,000 independent unit-test functions, historical trades, Monte Carlo profit forecasts or evidence of an edge. No network/account requests or orders were performed by the stress runner. The recorded historical strategy result remains unfavorable.

## Exploratory 24-variant historical sensitivity

2026-10-25: replayed 24 predeclared combinations of fee (0/1/5/10bp per side), next-bar entry delay (0/1 additional M5 bars) and stop (1/2/3 ATR), holding the breakout signal, 2R target, 12-bar timeout and 1bp slippage per side fixed. All final-two-month means were negative. The baseline exactly matches the prior six-month report. No active strategy parameters or decision gate were changed. Four added regression tests cover default compatibility, fee effects on matched trade timing, delay causality and invalid parameters. Full suite: 367 tests passed; backtest self-test passed.

Reports: reports/btc-sensitivity-2026-10-25.md and .json. Bootstrap intervals account approximately for 24 comparisons; reused history and multiple comparisons do not establish independent validation.
