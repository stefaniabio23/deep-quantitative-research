# Biotech sell-the-news

**Claim (pre-registered).** For single-asset biotech catalysts (Phase 2/3
readouts, PDUFA / FDA decisions, pivotal presentations), the pre-event
run-up and the pre-event news attention predict **negative** post-event
abnormal drift. A stock that has run up and been loudly covered going into
a readout tends to underperform after it, largely regardless of the
outcome, because the catalyst was already priced in and event-driven
holders exit on the news.

This rebuilds an institutional sell-the-news workflow (originally done with
paid social-sentiment data) on **only captured public datasets**: AACT for
catalyst dates, GDELT for historical news volume and tone, yfinance for
returns. Lineage: the EL/Meta playbook found the segment consensus could
not see; here the run-up and news intensity measure how *priced-in* a
binary event is, which is what determines whether good news still sells off.

## Verdict

Starter run on an 18-event verified seed (run 2026-06-21). **Result:
not confirmed on this sample, and the run is dominated by survivorship
bias**, which is the finding.

| Test | Result |
|---|---|
| Events analyzed | **12 of 18** seeded (6 dropped, see below) |
| Primary: pre-run-up coefficient on post-drift | **-0.044, 95% CI [-0.104, +0.036]** — sell-the-news direction, but CI includes 0 |
| Directional consistency (top-tercile down) | 0.500 (a coin flip) |
| R(run-up, post-drift) | -0.094 |
| pre-news coefficient | not used (GDELT rate-limited; news coverage < 50%) |

**Read.** On the survivors, the run-up coefficient leans the right way
(negative = sell-the-news) but is statistically indistinguishable from
zero on n = 12. The dominant effect is the **data-availability bias the
spec pre-registered**: 6 of 18 events dropped, and the dropouts are not
random.

- **5 acquired/delisted names vanish from yfinance:** ITCI (acquired by
  J&J), KRTX (BMS), ICPT (Alfasigma), SAGE (Supernus), AKRO. Acquired
  *winners* and delisted *failures* both disappear, biasing the sample.
- **1 ticker collision:** `AXON` today is Axon Enterprise (the Taser
  company), not Axovant Sciences (the 2017 Alzheimer's failure). yfinance
  silently returned the wrong company; the event was removed.

This is the project's own caveat made flesh, and the real lesson of the
starter run: a credible version needs a survivorship-clean, point-in-time
price source (delisted tickers included), not yfinance. The methodology is
verified (self-test); the verdict here is **illustrative and underpowered**,
not a finding. Re-run after expanding the universe and adding a clean price
source.

## Method

Cross-sectional event study; the unit is one (ticker, catalyst) event. On
market-adjusted returns (ticker minus XBI):

- **pre_runup**: cumulative abnormal return over [-60, -2] trading days.
- **pre_news**: summed GDELT article volume over [-30, -2] calendar days;
  **pre_tone**: mean GDELT tone over the same window.
- **event_reaction**: cumulative AR over [-1, +1] (a control).
- **post_drift**: cumulative AR over [+2, +21] (the outcome).

Analysis: OLS of `post_drift` on `z(pre_runup) + z(pre_news) +
event_reaction`, with cross-sectional bootstrap 95% CIs; a quintile sort by
run-up (the Q5-Q1 spread); directional consistency (share of top-tercile
run-up events that drift down); and R. Sell-the-news is confirmed only if
the `pre_runup` coefficient is negative with a CI clear of zero. An
out-of-sample cut at 2021 checks stability.

## Populate the event universe

`data/events_seed.csv` ships with placeholder rows. Replace them with real
catalysts (one row per event):

```
event_id,ticker,company_name,catalyst_date,catalyst_type,nct_id
```

Sourcing, in order of reliability: FDA PDUFA calendar (decision dates),
press-release readout dates, and AACT `studies.primary_completion_date` for
trials mapped to a public sponsor. Include names that **delisted after a
failed readout**, or the study inherits survivorship bias from yfinance.
The catalyst types are `phase2_readout | phase3_readout | pdufa |
conference`.

## Run

```bash
./run.sh                              # fetch prices + news, then analyze
python3 run_sell_the_news.py --self-test   # methodology check, no network
```

Both data sources are free and need no key.

## Verification

`run_sell_the_news.py --self-test` builds 300 synthetic events with a
planted sell-the-news effect (post-drift = -0.45 z(run-up) - 0.25 z(news) +
noise) and asserts the runner recovers a significantly negative run-up
coefficient (bootstrap CI clear of zero) and a negative Q5-Q1 spread, while
a null (post-drift independent of run-up) is rejected.

## Caveats

- **Sponsor-to-ticker mapping is the binding constraint.** AACT sponsor
  names are messy; v0 uses a curated, human-verified seed rather than an
  automated crawl. Scaling the universe is the main follow-on work.
- **Catalyst-date precision.** AACT `primary_completion_date` is an
  estimate and gets revised; actual readouts leak via press releases. The
  seed should record the best known date; the registry-estimated date is
  the PIT-safe fallback (and its revisions are themselves the AACT
  amendment-velocity signal).
- **Survivorship bias.** yfinance silently drops delisted tickers; failed
  names must come from the seed, not be back-filled.
- **News matching.** GDELT is queried by company name, so common or
  renamed names need disambiguation. Coverage starts 2015.
