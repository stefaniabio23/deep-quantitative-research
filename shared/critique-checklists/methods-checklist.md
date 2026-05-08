# Methods Checklist

Used by the **methods critic** to review Phase 3 statistical and analytical outputs.

Evaluate against this checklist. Return PASS, REVISE, or FAIL.
Cite the exact checklist item number that failed.
Do not suggest praise unless a checklist item explicitly passes.

---

## M1: Test appropriateness

- [ ] M1.1 — The statistical test used is appropriate for the data type and hypothesis (e.g., t-test requires approximately normal data; Pearson requires linearity)
- [ ] M1.2 — Time series data: the test accounts for autocorrelation (Newey-West SE used, or equivalent)
- [ ] M1.3 — Multiple testing: if more than one test was run, a correction was applied (Bonferroni, BH, or equivalent) and documented
- [ ] M1.4 — The null hypothesis is stated before results are reported, not inferred from them

## M2: Validation

- [ ] M2.1 — An out-of-sample or walk-forward validation was run (not in-sample only)
- [ ] M2.2 — If no OOS validation is possible, this is explicitly acknowledged with an estimate of the in-sample optimism
- [ ] M2.3 — Subperiod analysis was performed on the primary finding (minimum: split sample in half)
- [ ] M2.4 — Robustness check: at least one alternative specification was tested

## M3: Estimation quality

- [ ] M3.1 — Standard errors are reported alongside coefficients (not just coefficients)
- [ ] M3.2 — Confidence intervals are reported for the primary result
- [ ] M3.3 — Effect sizes are reported alongside p-values
- [ ] M3.4 — Sample size is sufficient for the test used (reference: statistical-standards.md minimum sample size table)

## M4: Backtest-specific (if backtest was run)

- [ ] M4.1 — Walk-forward or expanding-window validation was used (not single in-sample backtest)
- [ ] M4.2 — Transaction costs are included and documented
- [ ] M4.3 — Signal is shifted by at least 1 period to prevent look-ahead
- [ ] M4.4 — Results reported separately: in-sample and out-of-sample

## M5: Stationarity (time series only)

- [ ] M5.1 — Stationarity was tested before any regression or correlation on time series
- [ ] M5.2 — Non-stationary series were appropriately transformed (differenced, log-differenced, or cointegrated)
- [ ] M5.3 — Transformation applied is documented in the output
