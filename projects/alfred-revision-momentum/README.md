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

## Verdict (run 2026-06-21, Tier-1 + Tier-2)

Three monthly series (PAYEMS, RSAFS, INDPRO), ALFRED vintages, restricted
to observations with a genuine timely first release. Revisions are
measured at a fixed 90-day horizon on month-over-month **growth** (not raw
level), the momentum predictor is **point-in-time-safe** (only revisions
already realized by the new number's release date), and every statistic
carries a moving-block-bootstrap 95% CI. Full artifacts in
`expected-output/`.

| Stage | Question | Result |
|---|---|---|
| 1 momentum | PIT-safe growth-revision momentum, Bonferroni m = 3, CI excludes 0 | **1/3 survives: PAYEMS r = 0.098, CI [0.025, 0.176], OOS r = 0.220. INDPRO collapses to r = 0.057 (CI includes 0). RSAFS null.** |
| 1 sign-persistence | do consecutive growth revisions share sign? | **PAYEMS z = 5.08 (significant); RSAFS, INDPRO not** |
| 1 PIT gap | final-vintage minus first-vintage growth autocorrelation | **INDPRO +0.279, CI [+0.126, +0.353] (significant); PAYEMS +0.006 and RSAFS +0.039 not** |
| 2  | revision direction predicts the Treasury-yield move? | pre-registered, not run |

**Read.** The Tier-1 refinements flipped the naive result, which is the
point of running them. A level-based, look-ahead-prone test credited
industrial production with strong revision momentum. Once revisions are
measured on growth (so a benchmark that shifts a block of months by a
constant cannot manufacture momentum) and the predictor is restricted to
what was actually knowable at release, **INDPRO's momentum collapses to
insignificance**. It was an artifact of level-scaling and look-ahead.

The one real, point-in-time-safe revision momentum is in **nonfarm
payrolls**: small (r about 0.10) but significant under Bonferroni, with a
bootstrap CI clear of zero, and it **holds out-of-sample** (OOS r = 0.22).
Sign persistence corroborates it (z = 5.08): payroll revisions repeat
their direction well above chance. So the honest signal is the opposite of
what the naive run reported, payrolls, not industrial production.

The robust structural finding survives: the **industrial-production
point-in-time gap**, with a bootstrap CI that excludes zero. A naive
analyst on fully-revised data sees a lag-1 growth autocorrelation of 0.50;
only 0.22 was knowable in real time. Revised data more than **doubles** the
apparent predictability. That gap, not a tradable signal, is the result: a
quantified demonstration of why final-vintage backtests overstate what was
forecastable.

### Tier-2 robustness (the single-split verdict hid a regime)

- **The payrolls momentum is a modern-era phenomenon, not a stable
  all-history signal.** Across every OOS split from 2005 to 2020, the
  pre-split (older) correlation is ~0.02 to 0.05 while the post-split
  (recent) correlation is ~0.22 to 0.26. Subsample thirds confirm it:
  r = 0.02 (1955-1979), -0.01 (1979-2002), **0.245 (2002-2026)**. Payroll
  revision momentum is essentially absent before ~2002 and present after.
  A plausible mechanism is the BLS net birth-death model, phased into the
  establishment survey in 2001-2003, which changed how revisions accrue.
  This reframes Tier-1's "holds out-of-sample" as "the signal lives in the
  modern measurement regime."
- **Sign persistence, done properly (Wald-Wolfowitz runs test, which does
  not assume independent sign-agreements), still backs payrolls:**
  PAYEMS runs z = -4.08 (p < 0.0001); RSAFS and INDPRO not significant.
- **Industrial-production momentum is dead in every subsample and split**,
  confirming the Tier-1 collapse was not a single-split artifact.
- **The INDPRO point-in-time gap is robust in sign across all eras but its
  magnitude has roughly halved recently:** +0.25 to +0.32 in the first two
  thirds, +0.11 in 2002-2026. The qualitative lesson holds throughout; the
  current-regime gap is smaller than the full-sample +0.279 implies.

The pre-registration lives in `signal-spec.yaml`. Re-run with a
`FRED_API_KEY` and diff your output against `expected-output/`. Tier-2
artifacts: `stage1-oos-sensitivity.csv`, `stage1-subsample-stability.csv`,
`stage1-sign-persistence.csv`.

## Method

Stage 1 uses ALFRED only and is fully self-contained:

1. **Fetch.** `data/fetch_alfred.py` pulls each series with FRED's
   `output_type=3` (new and revised observations only), one call per
   series. FRED returns a wide matrix (one row per observation, a column
   per vintage on which the value changed); the fetcher melts it into a
   long CSV with columns `observation_date, vintage_date, value`.
2. **Reconstruct (timely + growth + fixed horizon).** Observations are
   first restricted to those with a genuine timely first release (first
   vintage within ~one quarter of the observation date), dropping early
   observations whose earliest archived vintage is decades late. The
   revision for each observation is then taken at a **fixed 90-day
   horizon** (the value as-of first-release + 90 days, minus the first
   release) and on **month-over-month growth**, so a benchmark that shifts
   a block of months by a constant cannot manufacture momentum. A
   scale-free relative-level revision is reported alongside as a
   robustness unit.
3. **Momentum test (PIT-safe).** The predictor for observation t is the
   fixed-horizon revision of the most recent earlier observation whose
   revision window had already closed by t's first-release date, so there
   is no look-ahead. Correlate target revision against this predictor;
   Bonferroni over the m = 3 primary family (growth, 90d, one per series);
   out-of-sample split at 2015-01-01; a moving-block bootstrap attaches a
   95% CI to every correlation, and a trial counts as a survivor only if
   the CI also excludes zero. A sign-persistence statistic (share of
   consecutive growth revisions sharing sign) gives a second read.
4. **PIT gap.** Month-over-month growth computed on first-vintage vs
   final-vintage values; report the lag-1 autocorrelation under each and
   the gap, with a moving-block-bootstrap 95% CI on the gap. The gap is
   what a naive final-data backtest would wrongly credit to
   predictability.

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
planted AR(1) revision process (phi = 0.85 on `PAYEMS`, zero on the
others), asserts the predictor alignment is free of look-ahead (each
target's predictor was realized by the target's release date), and checks
the runner recovers the planted momentum (`PAYEMS` survives Bonferroni
with a bootstrap CI clear of zero; the noise series do not). The shared
vintage primitives are covered in `tests/test_vintage.py`.

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
