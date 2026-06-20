# ALFRED revision-momentum

**Claim (pre-registered).** The first revision to a major US macro
series is not white noise. Its sign is serially correlated: an initial
release revised up is followed by a next-period release that is also
more likely to be revised up. We test this on three heavily-revised
monthly series (nonfarm payrolls `PAYEMS`, advance retail sales
`RSAFS`, industrial production `INDPRO`) using ALFRED vintage archives,
and we report the point-in-time vs final-vintage gap as a first-class
result: a backtest on fully-revised data sees structure that was not
knowable in real time, and the size of that gap is the finding.

This project is the pipeline's proof that point-in-time discipline
changes conclusions. It turns `revisions_possible` from a recorded-but-
ignored flag into a measured effect, exercising the vintage primitives
(`first_vintage_series`, `final_vintage_series`, `first_revisions`,
`as_of_series`) end to end.

## Verdict

Pending the live ALFRED fetch (needs a free `FRED_API_KEY`; see Run).
The analysis machinery is verified against a synthetic planted signal,
see "Verification" below. No real-data numbers are committed until the
fetch runs, so this table is a placeholder, not a result:

| Stage | Question | Status |
|---|---|---|
| 1a | Does revision_t correlate with revision_{t-k}? (Bonferroni, m = 9) | pending fetch |
| 1b | Final-vintage growth autocorrelation minus first-vintage (the PIT gap) | pending fetch |
| 2  | Does revision direction predict the Treasury-yield move around release? | pre-registered, not run |

The pre-registration lives in `signal-spec.yaml`. Re-run and diff your
output against `expected-output/` once it is populated.

## Method

Stage 1 uses ALFRED only and is fully self-contained:

1. **Fetch.** `data/fetch_alfred.py` pulls each series with FRED's
   `output_type=3` (new and revised observations only), which returns
   the full revision history in one call, tagged by the vintage date
   each value took effect. It lands as a long CSV with columns
   `observation_date, vintage_date, value`.
2. **Reconstruct.** `first_vintage_series` gives the real-time initial
   release; `final_vintage_series` gives today's fully-revised value;
   `first_revisions` gives the signed second-minus-first revision per
   observation.
3. **Momentum test.** For each series and lag k in {1,2,3}, correlate
   revision_t against revision_{t-k}. Bonferroni over the m = 3 x 3 = 9
   family, with an out-of-sample split at 2015-01-01. A sign-persistence
   statistic (share of consecutive revisions sharing sign, z vs 0.5)
   gives a second, distribution-light read on the same question.
4. **PIT gap.** Month-over-month growth computed on first-vintage vs
   final-vintage values; report the lag-1 autocorrelation under each.
   The difference is what a naive final-data backtest would wrongly
   credit to predictability.

### Stage 2 (pre-registered, not yet run)

Map the real-time revision direction onto a contemporaneous asset move:
does the sign of the first revision (and the real-time release surprise)
predict the change in 10Y / 2Y Treasury yields (`DGS10`, `DGS2`) around
the release window? This is correlational until release-time alignment
and costs are modeled, so it is staged separately and not claimed as a
tradable backtest.

## Run

```bash
# one-time: add a free FRED key (https://fred.stlouisfed.org/docs/api/api_key.html)
cp ../../.env.example ../../.env   # then set FRED_API_KEY=...

./run.sh                           # fetch + stage 1, writes expected-output/
```

To check the analysis without a key or network:

```bash
python3 run_revision_momentum.py --self-test
```

## Verification

`run_revision_momentum.py --self-test` builds synthetic vintages with a
planted AR(1) revision process (phi = 0.6 on `PAYEMS`, zero on the
others) and asserts the runner recovers the planted momentum
(`PAYEMS` lag-1 survives Bonferroni; the noise series do not). The
shared vintage primitives are covered in `tests/test_vintage.py`.

## Caveats

- ALFRED first-vintage reconstruction assumes the earliest archived
  vintage is the genuine first release. Observations predating a
  series' archive start have no real first vintage and are dropped,
  not back-filled.
- Revision magnitudes are in each series' native units. The momentum
  test is per-series (scale-free under correlation); only pooled views
  would need standardizing.
- The 2015 out-of-sample split is a fixed pre-registration choice, not
  tuned to the data.
