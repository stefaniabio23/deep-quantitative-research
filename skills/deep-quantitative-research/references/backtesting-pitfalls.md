# Backtesting pitfalls

Background for the `time-series-backtest` sub-skill. The metrics are easy. Avoiding subtle wins that are not wins is the work.

## The category error

KPI prediction and tradable signal are not the same backtest. Mixing them produces "this signal predicts retail sales" presented next to a Sharpe ratio. The Sharpe is meaningless for KPI prediction. The correlation is misleading for tradable signals. Pick one mode per run; do not show metrics from the other.

## Lookahead leaks

The most common silent failure.

- A value timestamped T was only observable at T + `release_lag_days`. Using earlier is leakage.
- Survivorship cleanup applied to historical universes is leakage.
- Index reconstitution after a known delisting is leakage.
- Volatility scaling using future-window variance is leakage.

Probe test: shift every predictor by `+1 period` more than the contract says. The backtest score should drop materially. If it stays flat, the leak is somewhere else.

## Survivorship bias

Equity universes constructed from "currently listed" stocks are the textbook case. Less obvious examples:

- Active mutual funds today: backtest on these and you have eliminated every fund that closed.
- Drugs that have approval today: backtest demand prediction on these and you have eliminated every failed candidate.
- News topics that survived in the archive.

Build the universe point-in-time. If you cannot, name the bias and cap confidence at `medium`.

## Multiple-testing exhaust

If you tried 500 feature-lag combinations and reported the best, the apparent p-value is not the real p-value. Apply the correction. Report the count of features tested and the correction method.

## Walk-forward vs single split

A single train / test split caps confidence at `medium`. Walk-forward (training window rolls forward through the test period, retraining each step) is the minimum for `high`. The walk-forward window length matters: too short and the model has no estimation power; too long and the validation is contaminated by stale parameters.

## Regime split

Performance on one regime says nothing about another. Examples:

- Pre-2008 vs post-2008 macro.
- Pre-COVID vs post-COVID consumer.
- Sub-2% real rates vs 2-5% real rates.

If the binding constraint of the validation gate is `regime_split`, the signal is conditionally useful, not universally true. Say so.

## Transaction costs in tradable mode

A signal with a 4 Sharpe pre-cost and 0.2 Sharpe post-cost is a 0.2 Sharpe signal. Always report post-cost. Always model bid-ask, market impact at the size you would actually trade, and turnover-driven costs. A backtest at $10k size is not a strategy at $100m size.

## OOS degradation rules of thumb

| OOS / IS ratio | What it usually means |
|---|---|
| > 80% | Robust |
| 50-80% | Real but weaker than fitted |
| 30-50% | Edge of meaningful; check feature search size |
| < 30% | Overfit or regime change; treat as failure unless explained |

## Probe tests to run

- Shuffle the test window labels: the test metric should collapse.
- Drop the top 1% of observations: the metric should not change much.
- Shift the predictor by ±1 period: the metric should peak at the stated lag, not at an undeclared lag.
- Bootstrap the test sample: the metric distribution should not include zero in its 95% interval for a `high` confidence call.
