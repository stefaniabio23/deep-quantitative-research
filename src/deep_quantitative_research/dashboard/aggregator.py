"""Multi-signal family dashboard.

Reads multiple run directories (each containing ``run.yaml``,
``validation-report.yaml``, ``backtest-result.yaml``) and emits a
family-level HTML dashboard with:

- Current read summary: counts by confidence tier and relationship type.
- Per-signal row: name, confidence cap, binding constraint, best feature,
  OOS verdict, links to the run-specific artefacts.
- Contradiction map: pairwise sign agreement of the headline test
  correlation across signals (when both are non-null).

Phase 8 ships the static version. Phase 9 will add semantic relatedness
once a signal-tagging convention exists.
"""

from __future__ import annotations

import html
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .charts import confidence_strip


_CSS = """
:root {
  --ink: #1a1a1a;
  --muted: #6b6b6b;
  --rule: #d6d6d6;
  --pass: #2e8540;
  --warn: #b58900;
  --fail: #c0392b;
}
* { box-sizing: border-box; }
body {
  font-family: Georgia, "Times New Roman", serif;
  color: var(--ink);
  margin: 0 auto;
  padding: 32px;
  max-width: 1000px;
  line-height: 1.5;
}
header { border-bottom: 1px solid var(--rule); padding-bottom: 16px; margin-bottom: 24px; }
h1 { margin: 0; font-size: 1.6em; font-weight: normal; }
h2 {
  font-size: 1.1em;
  font-weight: normal;
  margin: 28px 0 12px 0;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--rule);
}
.meta { color: var(--muted); font-size: 0.9em; }
.summary {
  display: flex;
  gap: 24px;
  margin: 12px 0;
}
.tier-card {
  border: 1px solid var(--rule);
  border-radius: 4px;
  padding: 10px 14px;
  min-width: 100px;
  font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
}
.tier-card .label { color: var(--muted); font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.04em; }
.tier-card .value { font-size: 1.5em; font-weight: 600; }
table { border-collapse: collapse; width: 100%; font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; font-size: 0.92em; }
th, td { padding: 6px 10px; text-align: left; border-bottom: 1px solid #efefef; }
th { font-weight: 600; color: var(--muted); border-bottom: 1px solid var(--rule); }
.cap-low { color: var(--fail); }
.cap-medium { color: var(--warn); }
.cap-high { color: var(--pass); }
.cap-tag { display: inline-block; padding: 1px 7px; border-radius: 3px; font-size: 0.85em; font-weight: 600; }
.cap-tag.low { background: #fde2e0; color: var(--fail); }
.cap-tag.medium { background: #fbeed0; color: var(--warn); }
.cap-tag.high { background: #d8efd8; color: var(--pass); }
code { font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 0.92em; background: #f3f3f3; padding: 1px 4px; border-radius: 3px; }
.contradiction-table th, .contradiction-table td { text-align: center; padding: 4px 6px; min-width: 28px; }
.cell-agree { background: #ebf5e9; color: var(--pass); }
.cell-disagree { background: #fdeae8; color: var(--fail); }
.cell-na { background: #f3f3f3; color: var(--muted); font-size: 0.8em; }
.cell-diag { background: #d6d6d6; color: var(--muted); font-size: 0.8em; }
footer { color: var(--muted); font-size: 0.85em; margin-top: 32px; border-top: 1px solid var(--rule); padding-top: 12px; }
"""


@dataclass
class FamilySignal:
    """One row in the family dashboard."""

    signal_id: str
    signal_name: str
    confidence_cap: str
    binding_constraint: str | None
    relationship_type: str
    best_feature: str | None
    survives_oos: bool | None
    correlation_test: float | None
    run_dir: Path
    run_yaml: dict[str, Any] = field(default_factory=dict)
    validation_yaml: dict[str, Any] = field(default_factory=dict)
    backtest_yaml: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_run_dir(cls, run_dir: Path | str) -> "FamilySignal":
        run_dir = Path(run_dir)
        run_path = run_dir / "run.yaml"
        validation_path = run_dir / "validation-report.yaml"
        backtest_path = run_dir / "backtest-result.yaml"
        if not validation_path.exists():
            raise FileNotFoundError(f"missing validation-report.yaml in {run_dir}")
        if not backtest_path.exists():
            raise FileNotFoundError(f"missing backtest-result.yaml in {run_dir}")

        run_yaml = yaml.safe_load(run_path.read_text()) if run_path.exists() else {}
        validation_yaml = yaml.safe_load(validation_path.read_text()) or {}
        backtest_yaml = yaml.safe_load(backtest_path.read_text()) or {}

        return cls(
            signal_id=str(validation_yaml.get("signal_id") or run_yaml.get("signal_id") or run_dir.name),
            signal_name=str(run_yaml.get("signal_name") or validation_yaml.get("signal_id") or run_dir.name),
            confidence_cap=str(validation_yaml.get("confidence_cap") or "unknown"),
            binding_constraint=validation_yaml.get("binding_constraint"),
            relationship_type=str(validation_yaml.get("relationship_type") or "unknown"),
            best_feature=backtest_yaml.get("best_feature"),
            survives_oos=(backtest_yaml.get("verdict") or {}).get("survives_oos"),
            correlation_test=((backtest_yaml.get("metrics_kpi") or {}).get("correlation_test")),
            run_dir=run_dir,
            run_yaml=run_yaml,
            validation_yaml=validation_yaml,
            backtest_yaml=backtest_yaml,
        )


def _e(value: Any) -> str:
    if value is None:
        return ""
    return html.escape(str(value))


def _cap_tag(cap: str) -> str:
    cap_safe = _e(cap)
    cls = cap.lower() if cap in {"low", "medium", "high"} else "low"
    return f'<span class="cap-tag {cls}">{cap_safe}</span>'


def _summary_cards(signals: list[FamilySignal]) -> str:
    by_tier: dict[str, int] = {"low": 0, "medium": 0, "high": 0}
    for s in signals:
        if s.confidence_cap in by_tier:
            by_tier[s.confidence_cap] += 1
    cards = []
    for tier in ("low", "medium", "high"):
        cards.append(
            f'<div class="tier-card"><div class="label">{tier}</div>'
            f'<div class="value cap-{tier}">{by_tier[tier]}</div></div>'
        )
    return f'<div class="summary">{"".join(cards)}</div>'


def _relationship_rollup(signals: list[FamilySignal]) -> str:
    counts: dict[str, int] = {}
    for s in signals:
        counts[s.relationship_type] = counts.get(s.relationship_type, 0) + 1
    if not counts:
        return ""
    items = ", ".join(f"<code>{_e(k)}</code> ({v})" for k, v in sorted(counts.items()))
    return f"<p class='meta'>Relationship types: {items}</p>"


def _signals_table(signals: list[FamilySignal]) -> str:
    rows = []
    for s in signals:
        oos = "yes" if s.survives_oos else ("no" if s.survives_oos is False else "n/a")
        corr = f"{s.correlation_test:.2f}" if isinstance(s.correlation_test, (int, float)) else "n/a"
        rows.append(
            "<tr>"
            f"<td>{_e(s.signal_name)}<div class='meta'>{_e(s.signal_id)}</div></td>"
            f"<td>{_cap_tag(s.confidence_cap)}</td>"
            f"<td>{_e(s.relationship_type)}</td>"
            f"<td>{_e(s.binding_constraint or '-')}</td>"
            f"<td><code>{_e(s.best_feature or '-')}</code></td>"
            f"<td>{_e(corr)}</td>"
            f"<td>{_e(oos)}</td>"
            "</tr>"
        )
    return (
        "<table>"
        "<thead><tr><th>Signal</th><th>Cap</th><th>Type</th><th>Binding</th>"
        "<th>Best feature</th><th>Test corr</th><th>OOS</th></tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody></table>"
    )


def _contradiction_matrix(signals: list[FamilySignal]) -> str:
    """Pairwise sign agreement of test correlation.

    A non-null pairwise cell is "agree" when both signals' test
    correlations share a sign, "disagree" otherwise.
    """
    if not signals:
        return ""
    headers = "".join(
        f"<th>{_e(s.signal_id)}</th>" for s in signals
    )
    rows = []
    for row_signal in signals:
        cells = []
        for col_signal in signals:
            if row_signal is col_signal:
                cells.append('<td class="cell-diag">-</td>')
                continue
            a, b = row_signal.correlation_test, col_signal.correlation_test
            if a is None or b is None or a != a or b != b:
                cells.append('<td class="cell-na">n/a</td>')
                continue
            if (a >= 0 and b >= 0) or (a < 0 and b < 0):
                cells.append('<td class="cell-agree">+</td>')
            else:
                cells.append('<td class="cell-disagree">-</td>')
        rows.append(f"<tr><th>{_e(row_signal.signal_id)}</th>{''.join(cells)}</tr>")
    return (
        "<table class='contradiction-table'>"
        f"<thead><tr><th></th>{headers}</tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody></table>"
    )


def render_family_dashboard(
    signals: list[FamilySignal],
    *,
    family_name: str = "Signal Family",
) -> str:
    """Return a self-contained HTML family dashboard."""
    title = _e(family_name)
    overall_strip_tier = "low"
    if signals:
        ranks = {"low": 1, "medium": 2, "high": 3}
        worst = min(signals, key=lambda s: ranks.get(s.confidence_cap, 0))
        overall_strip_tier = worst.confidence_cap if worst.confidence_cap in ranks else "low"
    overall_strip = confidence_strip(overall_strip_tier)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>{_CSS}</style>
</head>
<body>
<header>
  <h1>{title}</h1>
  <p class="meta">Aggregate read across {len(signals)} signal(s).</p>
  <div style="margin-top:10px">
    <img src="data:image/png;base64,{overall_strip}" alt="overall confidence cap">
    <p class="meta">Overall cap is the minimum across the family.</p>
  </div>
</header>

<section>
  <h2>Confidence summary</h2>
  {_summary_cards(signals)}
  {_relationship_rollup(signals)}
</section>

<section>
  <h2>Signals</h2>
  {_signals_table(signals)}
</section>

<section>
  <h2>Contradiction map</h2>
  <p class="meta">Pairwise sign agreement of the headline test correlation. Cells: <code>+</code> agree, <code>-</code> disagree, <code>n/a</code> insufficient data.</p>
  {_contradiction_matrix(signals)}
</section>

<footer>
  <p>Generated by <code>deep-quantitative-research</code>.</p>
</footer>
</body>
</html>
"""


def render_family_from_run_dirs(
    run_dirs: list[Path | str],
    *,
    family_name: str = "Signal Family",
) -> str:
    """Convenience: load each run dir and render."""
    signals = [FamilySignal.from_run_dir(d) for d in run_dirs]
    return render_family_dashboard(signals, family_name=family_name)
