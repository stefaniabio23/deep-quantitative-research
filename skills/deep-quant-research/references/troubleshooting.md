# Troubleshooting

## Python package errors

```bash
pip install pandas numpy scipy statsmodels yfinance requests pyyaml matplotlib seaborn
```

For FRED API: free key required at fred.stlouisfed.org/docs/api/api_key.html

---

## Data not available

**yfinance returning empty DataFrame:** Ticker may be delisted, on a non-US exchange, or misspelled. Try appending exchange suffix (e.g., `.L` for LSE, `.PA` for Euronext Paris).

**ClinicalTrials returns fewer results than expected:** API defaults to 10 results. Use `--n 1000` flag. International trials may not be registered.

**PubMed rate limiting:** NCBI allows 3 requests/second without API key, 10/second with. Add API key via `NCBI_API_KEY` environment variable.

**OpenTargets GraphQL timeout:** Query is too broad. Add disease or target filters.

---

## Confidence score stuck below 6 after 2 iterations

Common causes:
1. **Insufficient N:** Expand universe (geography, time period, indication)
2. **Confounded variable:** The main predictor correlates with an obvious confounder. Add controls or use a cleaner proxy.
3. **Wrong time period:** The effect is regime-dependent. Restrict to a single regime or test regimes separately.
4. **Effect is genuinely null:** Document as a null result. This is a finding.

After 3 iterations: terminate with null result. Do not force a conclusion.

---

## Critique cluster: one critic fails in non-thorough mode

Set `degraded_output: true` on the critique phase. `findings-evaluator` proceeds and notes the missing critique dimension. Affected conclusions carry `low_confidence: true`.

## Critique cluster: one critic fails in thorough mode

Pipeline pauses. Inform user. Options: retry, proceed with degraded output, or abort.

---

## Pipeline status shows unexpected state

```bash
python scripts/validate_output.py --all --output_dir ./[slug]/ --report
```

Check `pipeline_status.yaml` for the specific phase that failed and the failure reason.

---

## Web search returning low-quality results

Use site-specific searches:
```
site:clinicaltrials.gov [drug] [condition]
site:pubmed.ncbi.nlm.nih.gov [query]
site:europepmc.org [query]
site:sec.gov [company] 10-K [year]
site:fred.stlouisfed.org [series name]
site:mba.tuck.dartmouth.edu french data [factor]
```
