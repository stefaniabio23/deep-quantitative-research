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
