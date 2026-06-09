# Visual display principles

Reference for the `visual-display` sub-skill and the matplotlib
defaults in `src/deep_quantitative_research/dashboard/charts.py`. Lifted
from Tufte's `The Visual Display of Quantitative Information` and shaped
to fit the project's quantitative-research outputs.

## Three rules that override everything else

1. **The chart must serve the claim.** If the claim is "predictor leads
   target by one quarter", the chart must show that lead explicitly. If
   the claim is "OOS holds across regimes", a single regime is not
   enough.
2. **The chart must not lie, even gently.** No truncated axes that
   exaggerate change. No log scales without a log-scale label. No
   smoothing that hides the data.
3. **The chart must say less than it could.** Every gridline, legend
   item, label, and tick is a deduction from the data-ink ratio. If
   removing it does not cost the reader information, remove it.

## What this project ships

`dashboard/charts.py` exposes three primitives:

- `signal_vs_target_chart(predictor, target, train_end=...)`. Two lines
  standardised on a shared axis. Train / test boundary annotated. Series
  labelled at their endpoints, not in a legend.
- `lead_lag_chart(profile, ...)`. Bar chart of correlation at successive
  lags. Sign-coloured bars. Numeric label above each bar.
- `confidence_strip(confidence)`. Single horizontal strip with one
  filled cell for the active tier. Mirrors a status indicator without
  pretending tier differences are linear.

Plus `tufte_style()` (matplotlib rc context manager) and
`fig_to_base64(fig)` (PNG serialiser for inline HTML).

## Settings in `TUFTE_RC`

- **Serif title font, sans body** so the title reads as authored text
  and the data reads as data.
- **Small font sizes (8–10 pt)** to keep type subordinate to the
  visual encoding.
- **No top or right spines.** No internal gridlines unless absolutely
  needed.
- **Soft grey axes (#666 / #aaa).** Strong contrast is reserved for
  the data itself.
- **Single accent colour (#1f77b4).** Use sparingly for the active
  series. Negative values get a muted red (#cc6677) when sign matters.
- **No legend frames.** When a legend is necessary, it is frameless and
  inline.

## The chart-junk refusal list

- 3D bars.
- Shadow effects, gradients, beveled edges.
- Drop caps on axis labels.
- Pie charts for more than three categories.
- Stacked area charts where the layers cannot be ranked.
- "Spaghetti charts" with more than ~6 series on a single panel.
- Bubble charts where the area encodes the magnitude (the eye reads
  diameter, not area).

## Common edge cases

- **Returns data.** Negative returns are real; the y-axis must include
  them with a zero line marked. MAPE is meaningless near zero and is
  surfaced as `n/a` in our metrics panel.
- **Stock series.** Levels can dwarf the wiggle. Use a log axis only if
  the span is more than ~1.5 orders of magnitude AND label the axis as
  log.
- **Sparse event series.** Plot the events as scatter, not interpolated
  lines. Add jitter only when overlapping events would otherwise hide
  count.
- **Mixed-cadence overlays.** Either resample to a common cadence
  before plotting (and label that you did) or use small multiples.

## Further reading

- Tufte, *The Visual Display of Quantitative Information* (1983).
- Tufte, *Envisioning Information* (1990) — sections on layering and
  separation.
- Stephen Few, *Show Me the Numbers* — operational dashboard guidance.
- Existing public skill packs to mine for matplotlib defaults:
  `gnurio/tufte-vdqi-plugin`, `aparente/e48c353755958621b3c0004593105a90`.
