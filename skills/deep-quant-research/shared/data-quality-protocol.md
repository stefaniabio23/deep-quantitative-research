# Data Quality Protocol

Mandatory checks performed by the `data-quality` agent before any analysis begins.
Every dataset entering the analysis pipeline must pass this protocol.

---

## The Four Critical Biases

These biases silently invalidate results. Failing to check them is not a minor oversight.

### 1. Look-Ahead Bias

**What it is:** Using data in a signal that would not have been available at the time the decision is made.

**Common instances:**
- Using end-of-quarter earnings in a signal triggered mid-quarter
- Using revised economic data (GDP, CPI revisions are often substantial)
- Using current index composition to backtest a strategy (see survivorship bias)
- Using analyst rating changes on the day they occur rather than the following open
- Point-in-time vs. as-reported: Compustat and Bloomberg report data with a lag

**Check procedure:**
1. For each variable in the dataset, confirm the exact date it would have been observable by a market participant
2. Shift signals by at least 1 business day to allow for processing/reporting delay
3. For fundamental data: use announcement date, not period-end date
4. Document the lag assumption for each variable

**Red flag signal:** Suspiciously high in-sample performance that disappears out-of-sample is often look-ahead bias.

---

### 2. Survivorship Bias

**What it is:** Analysing only entities that survived to the present, ignoring those that were delisted, acquired, went bankrupt, or were removed from an index.

**Common instances:**
- Backtesting on current S&P 500 constituents (ignores ~40% historical turnover)
- Analysing drugs currently in development without including failed trials
- Studying funds without including closed/liquidated funds (hedge fund databases are heavily biased)
- Selecting "successful" companies and working backwards

**Check procedure:**
1. Ask: was the universe defined using current or historical composition?
2. For equity datasets: confirm whether delisted stocks are included
3. For clinical data: confirm failed and discontinued trials are included
4. For fund data: confirm closed funds are included
5. If survivorship-biased data must be used: document it prominently and apply a conservative discount to returns (typical survivorship bias in equity returns: 1-3% per year)

---

### 3. Data Snooping / p-Hacking

**What it is:** Running many tests until something significant appears, then reporting only the significant result.

**Common instances:**
- Testing 50 parameter combinations and reporting the best
- Trying multiple subperiods and reporting the one where the strategy works
- Adjusting the signal definition until the backtest looks good
- Reporting only the statistically significant findings from a broader analysis

**Check procedure:**
1. Document all tests run before reporting results
2. Apply multiple testing correction (Bonferroni: divide α by number of tests; or Benjamini-Hochberg for FDR)
3. Report the full distribution of results, not just the best
4. Use a hold-out sample not touched during exploration
5. Calculate the Probability of Backtest Overfitting (PBO) for strategy backtests if more than 10 parameter combinations were tested

---

### 4. Selection Bias

**What it is:** The sample used does not represent the population being studied.

**Common instances:**
- Studying drugs that reached Phase 3 (ignores Phase 1/2 failures)
- Analysing only large-cap stocks (ignores small-cap where many factors are stronger)
- Using a short data period that happens to include an anomaly
- Voluntary reporting bias (e.g., companies that disclose ESG data may differ systematically)

**Check procedure:**
1. Define the target population explicitly
2. Assess how the sample differs from the population
3. Check whether selection is correlated with the outcome variable
4. If selection is endogenous, flag this as a primary limitation

---

## Data Provenance Checklist

For every dataset entering analysis:

```
Source: [where the data came from]
Access date: [when retrieved]
Coverage: [time period, geography, asset class]
Frequency: [daily/weekly/monthly/quarterly]
Universe: [what entities are included and excluded]
Known survivorship bias: [yes / no / unknown]
Point-in-time: [yes / no / unknown]
Revisions: [is this revised or as-originally-reported data?]
Missing data handling: [how gaps are treated]
Outliers: [any extreme values investigated and explained]
```

---

## Outlier Investigation

Outliers are not automatically errors, but they must be explained.

**Procedure:**
1. Flag observations beyond 4 standard deviations from the mean (or 3× IQR)
2. For each flagged observation, determine: genuine extreme event, data error, or corporate action
3. Corporate actions (splits, dividends, M&A) should be adjusted for, not removed
4. Data errors: remove and document
5. Genuine extreme events: keep, but test sensitivity of conclusions to their inclusion

---

## Minimum Sample Size Guidelines

| Analysis type | Minimum observations | Preferred |
|--------------|---------------------|-----------|
| Correlation | 30 | 100+ |
| Linear regression (k predictors) | 10k | 20k+ |
| Factor model | 60 months | 120+ months |
| Event study | 30 events | 100+ events |
| Strategy backtest | 5 years daily | 10+ years |
| Clinical trial signal | 50 patients | 200+ |

Below minimum: flag as exploratory only; no causal language; no strong recommendations.

---

## Missing Data

- Report the rate of missing data by variable
- If missing rate > 20% for any key variable: flag before proceeding
- Missing completely at random (MCAR): safe to use complete cases
- Missing at random (MAR): multiple imputation may be appropriate
- Missing not at random (MNAR): selection problem; document carefully
- Never impute forward into the future (look-ahead bias)

---

## Output

The `data-quality` agent must produce a **Data Quality Report** before analysis begins:

```
DATA QUALITY REPORT
===================
Dataset: [name]
Period: [start] to [end]
Observations: [N]

Bias Assessment
---------------
Look-ahead bias: PASS / WARN / FAIL — [explanation]
Survivorship bias: PASS / WARN / FAIL — [explanation]
Data snooping risk: PASS / WARN / FAIL — [explanation]
Selection bias: PASS / WARN / FAIL — [explanation]

Data Completeness
-----------------
[Variable]: [N obs], [% missing], [outliers flagged]

Verdict: PROCEED / PROCEED WITH CAVEATS / DO NOT PROCEED
[If caveats: list them here]
```

A FAIL on look-ahead or survivorship bias is a DO NOT PROCEED unless the user explicitly acknowledges the limitation and instructs otherwise.
