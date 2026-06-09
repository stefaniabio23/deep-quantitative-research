# Chart Style Guide

All charts use `scripts/chart_theme.py`. Import it at the top of any plotting script:

```python
from chart_theme import apply_theme, COLORS, save_chart
apply_theme()
```

Do not hardcode colors, fonts, or figure sizes in individual scripts.

---

## Visual language

**Background:** Warm off-white `#f7f5f0`. Not pure white.
**Grid:** Subtle horizontal dashes only, `#e0ddd8`. No vertical grid lines.
**Spines:** Remove top and right. Left and bottom visible but thin.
**Tick marks:** Length 0. Labels do the work.

---

## Color palette

```python
COLORS = {
    # Primary sequence — use in order
    "blue":       "#2563eb",
    "red":        "#dc2626",
    "green":      "#16a34a",
    "orange":     "#ea580c",
    "purple":     "#7c3aed",
    "teal":       "#0891b2",
    # Semantic
    "positive":   "#16a34a",
    "negative":   "#dc2626",
    "neutral":    "#6b7280",
    "warning":    "#d97706",
    # Pathway position (biotech)
    "upstream":   "#dc2626",
    "downstream": "#f59e0b",
    "receptor":   "#3b82f6",
    "immune":     "#10b981",
    # Backgrounds
    "bg":         "#f7f5f0",
    "grid":       "#e0ddd8",
    "muted":      "#888888",
}
```

---

## Figure sizes (inches)

| Type | Width x Height |
|------|---------------|
| Single panel | 10 x 6 |
| Two panels side by side | 14 x 6 |
| Three panels | 18 x 6 |
| Tall (heatmap, divergence) | 12 x 8 |
| Small inline | 7 x 4.5 |

Always: `bbox_inches="tight"`, `dpi=150`.

---

## Titles

State the finding, not the variable.

Not: "Phase 2 completion rate by indication"
Yes: "Upstream drugs complete Phase 2 at similar rates but advance to Phase 3 half as often"

Title case for the first word only. Bold.

---

## Source line

Always present. Bottom-right, muted, 7.5pt.

```python
fig.text(0.99, 0.01, "Source: ClinicalTrials.gov + OpenTargets",
         ha="right", fontsize=7.5, color=COLORS["muted"])
```

---

## Annotations

Annotate: the key finding, outlier points that carry the story, regime boundaries, sample sizes.

Do not annotate: every data point, things obvious from the axis, things already in the title.

Never rely on colour alone to convey a category. Use colour plus label, or colour plus shape.

Sample sizes: show them. Either on bars/cells or in axis tick labels as `NSCLC\n(n=34)`.

Baseline reference lines for comparisons:
```python
ax.axhline(0, color=COLORS["neutral"], linewidth=0.8, linestyle="--")
```

---

## Saving

```python
save_chart(fig, "indication_heatmap", output_dir)
# Saves to output_dir/chart_indication_heatmap.png
```

Naming: `chart_[slug].png`. No spaces, no uppercase.

---

## Diagnostic charts

Every analysis report ships a sample-size diagnostic alongside the headline chart. A reader should never have to dig into a CSV to find out which cells the headline rests on. Burying the per-cell N table is the most common reason analysis reports survive review and then collapse on a careful re-read.

**Three diagnostic chart conventions to use whenever the analysis aggregates by category.**

### 1. Sample-size heatmap

Same axes as the headline chart. Colour intensity = N (drugs, trials, observations). Cells below the pre-registered minimum-N filter are greyed out, not coloured.

```python
# Example: sample-size heatmap for (target, indication) cells
import numpy as np
fig, ax = plt.subplots(figsize=(12, 8))
mask = pivot_n < min_n
ax.imshow(np.where(mask, np.nan, pivot_n), cmap="Blues", aspect="auto")
# annotate cells with N; below-threshold cells annotated with "•"
```

Place this directly above the headline chart, on the same horizontal scale, in any report.

### 2. Coverage table

A small chart, not a markdown table. One bar per category showing N. Pre-registered minimum-N threshold drawn as a vertical line. Sort descending. Cap at 20 categories — the long tail goes in an appendix.

This makes "what fraction of cells survive the filter" visually obvious at a glance. In the biotech-pos session 14 of 663 cells survived; reporting that as "2.1% of cells" is honest, but a coverage chart makes it impossible to skim past.

### 3. Before-and-after stratification side-by-side

Whenever an analysis introduces a stratification or adjustment that materially changes the headline (sponsor stratification, factor adjustment, regime conditioning), produce a two-panel side-by-side:

- Left panel: unadjusted version of the headline chart
- Right panel: adjusted/stratified version
- Same axes, same colour scale, same cell ordering

If the right panel looks dramatically different from the left, that **is** the finding. Forcing the reader to flip between two single-panel charts hides the comparison.

```python
fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(14, 6), sharey=True)
# left: raw P3-ratio per cell
# right: sponsor-adjusted P3-ratio per cell
fig.suptitle("Sponsor adjustment collapses the divergence pattern", fontweight="bold")
```

### When to skip diagnostic charts

If the headline analysis runs on a single, dense, well-balanced dataset (e.g., daily S&P 500 returns over 30 years), diagnostic charts add noise. Use judgement. The trigger is: aggregation by category with cells of unequal size. Whenever that's true, ship the diagnostic.
