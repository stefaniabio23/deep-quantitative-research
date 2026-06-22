# ALFRED revision-momentum, stage 1 (Tier-1 + Tier-2)

**PIT-safe momentum, primary family (growth, 90d), Bonferroni m = 3, CI excludes 0:**

- Survivors: **1 of 3**.

## Momentum trials (PIT-safe; * = primary)

| Series | Unit | Horizon | Full r | 95% CI | n | Bonferroni p | OOS r | OOS n |
|---|---|---:|---:|---|---:|---:|---:|---:|
| INDPRO * | growth_rev | 90 | 0.057 | [-0.040, 0.150] | 1188 | 0.151 | 0.002 | 136 |
| INDPRO | growth_rev | 365 | -0.072 | [-0.155, 0.022] | 1179 | - | 0.179 | 136 |
| INDPRO | rel_level_rev | 90 | 0.000 | [-0.018, 0.018] | 1188 | - | -0.098 | 136 |
| INDPRO | rel_level_rev | 365 | -0.057 | [-0.098, -0.013] | 1179 | - | -0.213 | 136 |
| PAYEMS * | growth_rev | 90 | 0.098 | [0.025, 0.176] | 850 | 0.012 | 0.220 | 137 |
| PAYEMS | growth_rev | 365 | 0.080 | [0.007, 0.135] | 841 | - | 0.129 | 137 |
| PAYEMS | rel_level_rev | 90 | 0.044 | [-0.006, 0.082] | 850 | - | 0.070 | 137 |
| PAYEMS | rel_level_rev | 365 | 0.076 | [-0.084, 0.197] | 841 | - | 0.243 | 137 |
| RSAFS * | growth_rev | 90 | 0.016 | [-0.160, 0.193] | 297 | 1.000 | 0.012 | 137 |
| RSAFS | growth_rev | 365 | 0.055 | [-0.086, 0.179] | 287 | - | 0.099 | 137 |
| RSAFS | rel_level_rev | 90 | -0.042 | [-0.155, 0.130] | 297 | - | 0.059 | 137 |
| RSAFS | rel_level_rev | 365 | 0.105 | [-0.084, 0.318] | 287 | - | 0.035 | 137 |

## Sign persistence of growth revisions (Wald-Wolfowitz runs test)

Negative runs-z = fewer runs than chance = same-sign clustering (directional persistence).

| Series | Pairs | Same-sign share | Share 95% CI | Runs z | Runs p |
|---|---:|---:|---|---:|---:|
| PAYEMS | 848 | 0.587 | [0.550, 0.625] | -4.08 | 0.0000 |
| RSAFS | 298 | 0.537 | [0.490, 0.591] | -0.43 | 0.6649 |
| INDPRO | 974 | 0.487 | [0.457, 0.519] | 0.88 | 0.3812 |

## OOS-split sensitivity (primary momentum, train/test r by split)

| Series | Split | Train r | Train n | Test r | Test n |
|---|---|---:|---:|---:|---:|
| PAYEMS | 2005-01-01 | 0.014 | 593 | 0.252 | 257 |
| PAYEMS | 2008-01-01 | 0.015 | 629 | 0.260 | 221 |
| PAYEMS | 2010-01-01 | 0.044 | 653 | 0.231 | 197 |
| PAYEMS | 2012-01-01 | 0.044 | 677 | 0.231 | 173 |
| PAYEMS | 2015-01-01 | 0.048 | 713 | 0.220 | 137 |
| PAYEMS | 2018-01-01 | 0.049 | 749 | 0.229 | 101 |
| PAYEMS | 2020-01-01 | 0.053 | 773 | 0.227 | 77 |
| RSAFS | 2005-01-01 | -0.143 | 40 | 0.024 | 257 |
| RSAFS | 2008-01-01 | 0.012 | 76 | 0.016 | 221 |
| RSAFS | 2010-01-01 | 0.037 | 100 | 0.011 | 197 |
| RSAFS | 2012-01-01 | 0.083 | 124 | 0.001 | 173 |
| RSAFS | 2015-01-01 | 0.023 | 160 | 0.012 | 137 |
| RSAFS | 2018-01-01 | -0.004 | 196 | 0.024 | 101 |
| RSAFS | 2020-01-01 | -0.011 | 220 | 0.029 | 77 |
| INDPRO | 2005-01-01 | 0.058 | 932 | -0.002 | 256 |
| INDPRO | 2008-01-01 | 0.058 | 968 | -0.001 | 220 |
| INDPRO | 2010-01-01 | 0.058 | 992 | -0.009 | 196 |
| INDPRO | 2012-01-01 | 0.058 | 1016 | -0.010 | 172 |
| INDPRO | 2015-01-01 | 0.058 | 1052 | 0.002 | 136 |
| INDPRO | 2018-01-01 | 0.057 | 1088 | 0.015 | 100 |
| INDPRO | 2020-01-01 | 0.057 | 1112 | 0.020 | 76 |

## Subsample stability (disjoint time-thirds)

| Series | Metric | Third | Period | Value | n |
|---|---|---:|---|---:|---:|
| PAYEMS | momentum_r | 1 | 1955-08-01..1979-03-01 | 0.022 | 284 |
| PAYEMS | momentum_r | 2 | 1979-04-01..2002-10-01 | -0.007 | 283 |
| PAYEMS | momentum_r | 3 | 2002-11-01..2026-05-01 | 0.245 | 283 |
| PAYEMS | pit_gap | 1 | 1955-05-01..1979-01-01 | 0.154 | 285 |
| PAYEMS | pit_gap | 2 | 1979-02-01..2002-09-01 | 0.202 | 284 |
| PAYEMS | pit_gap | 3 | 2002-10-01..2026-05-01 | -0.004 | 284 |
| RSAFS | momentum_r | 1 | 2001-09-01..2009-11-01 | 0.039 | 99 |
| RSAFS | momentum_r | 2 | 2009-12-01..2018-02-01 | -0.055 | 99 |
| RSAFS | momentum_r | 3 | 2018-03-01..2026-05-01 | 0.024 | 99 |
| RSAFS | pit_gap | 1 | 2001-06-01..2009-09-01 | 0.130 | 100 |
| RSAFS | pit_gap | 2 | 2009-10-01..2018-01-01 | 0.133 | 100 |
| RSAFS | pit_gap | 3 | 2018-02-01..2026-05-01 | 0.018 | 100 |
| INDPRO | momentum_r | 1 | 1927-05-01..1960-04-01 | 0.059 | 396 |
| INDPRO | momentum_r | 2 | 1960-05-01..1993-04-01 | -0.010 | 396 |
| INDPRO | momentum_r | 3 | 1993-05-01..2026-05-01 | 0.074 | 396 |
| INDPRO | pit_gap | 1 | 1927-02-01..1960-02-01 | 0.253 | 397 |
| INDPRO | pit_gap | 2 | 1960-03-01..1993-03-01 | 0.318 | 397 |
| INDPRO | pit_gap | 3 | 1993-04-01..2026-05-01 | 0.113 | 397 |

## Point-in-time gap (lag-1 AC of MoM growth, with 95% CI)

| Series | First-vintage AC1 | Final-vintage AC1 | Gap | Gap 95% CI |
|---|---:|---:|---:|---|
| PAYEMS | 0.085 | 0.090 | +0.006 | [-0.022, +0.266] |
| RSAFS | -0.084 | -0.045 | +0.039 | [-0.043, +0.115] |
| INDPRO | 0.225 | 0.504 | +0.279 | [+0.126, +0.353] |

A gap whose CI excludes 0 means final-vintage data shows growth autocorrelation that was not knowable in real time.
