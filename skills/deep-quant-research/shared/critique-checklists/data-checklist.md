# Data Checklist

Used by the **data critic** to review Phase 2 data collection and quality audit outputs.

Evaluate against this checklist. Return PASS, REVISE, or FAIL.
Cite the exact checklist item number that failed.
Do not suggest praise unless a checklist item explicitly passes.

---

## D1: Provenance

- [ ] D1.1 — Every dataset has a named source (API, URL, or user-provided)
- [ ] D1.2 — Access date is documented for all web-fetched data
- [ ] D1.3 — Time period is clearly specified for every dataset
- [ ] D1.4 — Universe is defined (which entities are included and why)

## D2: Look-ahead bias

- [ ] D2.1 — For each signal variable: the data was available at the time the signal fires (not using period-end dates when announcement dates are required)
- [ ] D2.2 — Index composition used in backtesting is point-in-time, not current composition
- [ ] D2.3 — Any fundamental data (earnings, revenue) uses announcement date, not period-end date
- [ ] D2.4 — If look-ahead bias is uncertain for any variable, it is flagged as WARN, not silently passed

## D3: Survivorship bias

- [ ] D3.1 — The universe includes entities that failed, were delisted, or were removed from indices (or this is explicitly documented as a limitation)
- [ ] D3.2 — If survivorship-biased data is used, this is disclosed prominently, not buried
- [ ] D3.3 — A conservative discount is applied to results when survivorship bias is known to be present

## D4: Data completeness

- [ ] D4.1 — Missing data rate is reported per variable
- [ ] D4.2 — Any variable with more than 20% missing is flagged before analysis
- [ ] D4.3 — Outliers are documented (what they are, whether they were investigated, how they were handled)
- [ ] D4.4 — Outlier handling decision (keep / adjust / remove) is documented with rationale

## D5: Minimum sample size

- [ ] D5.1 — Sample size meets the minimum in statistical-standards.md for the planned analysis
- [ ] D5.2 — If sample size is below minimum, the output is labelled "exploratory only" and no strong claims are made
