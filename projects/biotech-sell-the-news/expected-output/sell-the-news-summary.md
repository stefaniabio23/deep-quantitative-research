# Biotech sell-the-news event study

**Events analyzed: 12.**

**Verdict: not confirmed** (pre-run-up coefficient negative with CI excluding 0).

## Cross-sectional OLS (post-drift on standardized predictors)

| Predictor | Coefficient | 95% CI |
|---|---:|---|
| pre_runup (z) | -0.0442 | [-0.1043, +0.0355] |
| pre_news (z) | n/a | (news coverage < 50% of events) |

## Quintile sort by pre-run-up (mean post-drift)

| Q1 (low run-up) | Q2 | Q3 | Q4 | Q5 (high run-up) | Q5-Q1 |
|---:|---:|---:|---:|---:|---:|
| +0.0288 | +0.2510 | +0.0814 | -0.0301 | +0.0215 | -0.0073 |

Directional consistency (top-tercile run-up events drifting down): **0.500**. R(run-up, post-drift) = -0.094.
