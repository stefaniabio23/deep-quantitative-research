---
name: time-series-backtest
description: Evaluate whether predictors have useful relationship to target variables. Two modes: KPI prediction (rolling correlation, rank correlation, directionality, MAE / MAPE / RMSE, hit rate, lead-lag profile, OOS degradation) and tradable signal (CAGR, Sharpe, Sortino, max drawdown, turnover, transaction costs, benchmark alpha / beta, walk-forward).
---

# time-series-backtest

**Status:** scaffold. Content fill scheduled for Phase 3 of `BUILD_CHECKLIST.md` (section 7.7).

**Purpose:** distinguish KPI prediction from tradable signal testing every time. Aligns cadences, respects release lags, prevents lookahead.

**Output:** `experiments/runs/<run>/metrics.json` plus a markdown summary.
