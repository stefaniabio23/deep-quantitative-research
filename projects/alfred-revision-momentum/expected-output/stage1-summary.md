# ALFRED revision-momentum, stage 1

**Revision momentum, Bonferroni at m = 9 trials (alpha = 0.05):**

- Full-sample survivors: **3 of 9**.
- Out-of-sample (>= 2015) survivors: **0 of 9**.

## Momentum trials

| Series | Lag | Full r | Full n | Full p (Bonferroni) | OOS r | OOS n | OOS p (Bonferroni) |
|---|---:|---:|---:|---:|---:|---:|---:|
| INDPRO | 1 | 0.157 | 1190 | 0.000 | 0.012 | 135 | 1.000 |
| INDPRO | 2 | 0.307 | 1189 | 0.000 | 0.040 | 135 | 1.000 |
| INDPRO | 3 | 0.203 | 1188 | 0.000 | 0.024 | 135 | 1.000 |
| PAYEMS | 1 | 0.046 | 852 | 1.000 | 0.052 | 136 | 1.000 |
| PAYEMS | 2 | 0.032 | 851 | 1.000 | 0.079 | 136 | 1.000 |
| PAYEMS | 3 | 0.040 | 850 | 1.000 | 0.094 | 136 | 1.000 |
| RSAFS | 1 | -0.098 | 299 | 0.820 | -0.093 | 136 | 1.000 |
| RSAFS | 2 | -0.011 | 298 | 1.000 | -0.036 | 136 | 1.000 |
| RSAFS | 3 | -0.009 | 297 | 1.000 | 0.003 | 136 | 1.000 |

## Sign persistence (share of consecutive revisions sharing sign)

| Series | Pairs | Same-sign share | z vs 0.5 |
|---|---:|---:|---:|
| PAYEMS | 852 | 0.566 | 3.84 |
| RSAFS | 299 | 0.465 | -1.21 |
| INDPRO | 1190 | 0.568 | 4.70 |

## Point-in-time gap (lag-1 autocorrelation of MoM growth)

| Series | First-vintage AC1 | Final-vintage AC1 | Gap (final - first) |
|---|---:|---:|---:|
| PAYEMS | 0.085 | 0.090 | +0.006 |
| RSAFS | -0.084 | -0.045 | +0.039 |
| INDPRO | 0.225 | 0.504 | +0.279 |

A positive gap means a naive analyst using fully-revised data would see growth autocorrelation that was not knowable in real time.
