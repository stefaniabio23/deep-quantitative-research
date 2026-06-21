# ALFRED revision-momentum, stage 1 (Tier-1 refined)

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

## Sign persistence of growth revisions (vs 0.5)

| Series | Pairs | Same-sign share | z vs 0.5 |
|---|---:|---:|---:|
| PAYEMS | 848 | 0.587 | 5.08 |
| RSAFS | 298 | 0.537 | 1.27 |
| INDPRO | 974 | 0.487 | -0.83 |

## Point-in-time gap (lag-1 AC of MoM growth, with 95% CI)

| Series | First-vintage AC1 | Final-vintage AC1 | Gap | Gap 95% CI |
|---|---:|---:|---:|---|
| PAYEMS | 0.085 | 0.090 | +0.006 | [-0.022, +0.266] |
| RSAFS | -0.084 | -0.045 | +0.039 | [-0.043, +0.115] |
| INDPRO | 0.225 | 0.504 | +0.279 | [+0.126, +0.353] |

A gap whose CI excludes 0 means final-vintage data shows growth autocorrelation that was not knowable in real time.
