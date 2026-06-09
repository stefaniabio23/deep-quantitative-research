"""Single-signal HTML dashboard emitter.

Produces a self-contained ``dashboard.html`` (no external assets, no JS) that
shows the same information as ``signal-card.md`` plus inline charts. CSS is
inlined; images are embedded as base64 PNGs. The output is intentionally
small enough to email or commit.
"""

from __future__ import annotations

import html
from typing import Any

import pandas as pd

from ..backtest.kpi_backtest import KpiBacktestResult
from ..research.signal_spec import SignalSpec
from ..validation.gate import ValidationReport
from .charts import confidence_strip, lead_lag_chart, signal_vs_target_chart


_CSS = """
:root {
  --ink: #1a1a1a;
  --muted: #6b6b6b;
  --rule: #d6d6d6;
  --accent: #1f77b4;
  --warn: #b58900;
  --fail: #c0392b;
  --pass: #2e8540;
}
* { box-sizing: border-box; }
body {
  font-family: Georgia, "Times New Roman", serif;
  color: var(--ink);
  margin: 0;
  padding: 32px;
  max-width: 980px;
  margin-left: auto;
  margin-right: auto;
  line-height: 1.5;
}
header { border-bottom: 1px solid var(--rule); padding-bottom: 16px; margin-bottom: 24px; }
h1 { margin: 0; font-size: 1.7em; font-weight: normal; }
h2 {
  font-size: 1.15em;
  font-weight: normal;
  margin: 28px 0 12px 0;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--rule);
}
.meta { color: var(--muted); font-size: 0.9em; margin-top: 8px; }
.confidence-row { display: flex; align-items: center; gap: 16px; margin-top: 12px; }
.confidence-row strong { font-size: 1.1em; }
.binding { color: var(--muted); font-style: italic; }
.chart { margin: 16px 0; }
.chart img { max-width: 100%; height: auto; display: block; }
table { border-collapse: collapse; width: 100%; font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; font-size: 0.92em; }
th, td { padding: 6px 10px; text-align: left; border-bottom: 1px solid #efefef; }
th { font-weight: 600; color: var(--muted); border-bottom: 1px solid var(--rule); }
td.num { text-align: right; font-variant-numeric: tabular-nums; }
.verdict-pass { color: var(--pass); }
.verdict-warn { color: var(--warn); }
.verdict-fail { color: var(--fail); }
ul.tight { margin: 0; padding-left: 20px; }
ul.tight li { margin: 4px 0; }
footer { color: var(--muted); font-size: 0.85em; margin-top: 32px; border-top: 1px solid var(--rule); padding-top: 12px; }
code { font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 0.92em; background: #f3f3f3; padding: 1px 4px; border-radius: 3px; }
"""


def _e(value: Any) -> str:
    if value is None:
        return ""
    return html.escape(str(value))


def _fmt(value: float | None) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float) and value != value:
        return "n/a"
    return f"{value:.2f}"


def _verdict_class(verdict: str) -> str:
    return f"verdict-{verdict}"


def _checks_table(report: ValidationReport) -> str:
    rows = []
    for check in report.checks:
        rows.append(
            f'<tr><td>{_e(check.name)}</td>'
            f'<td class="{_verdict_class(check.verdict)}">{_e(check.verdict)}</td>'
            f'<td class="num">{_e(check.value)}</td>'
            f'<td>{_e(check.explanation)}</td></tr>'
        )
    return (
        "<table>"
        "<thead><tr><th>Check</th><th>Verdict</th><th class='num'>Value</th><th>Explanation</th></tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody></table>"
    )


def _metrics_table(backtest: KpiBacktestResult) -> str:
    train, test = backtest.metrics_train, backtest.metrics_test
    rows = [
        ("Correlation", _fmt(train.correlation), _fmt(test.correlation)),
        ("Rank correlation", "n/a", _fmt(test.rank_correlation)),
        ("Directional accuracy", _fmt(train.directional_accuracy), _fmt(test.directional_accuracy)),
        ("MAE", "n/a", _fmt(test.mae)),
        ("MAPE (%)", "n/a", _fmt(test.mape)),
        ("RMSE", "n/a", _fmt(test.rmse)),
        ("Hit rate", "n/a", _fmt(test.hit_rate)),
        ("Sample size", str(train.sample_size), str(test.sample_size)),
    ]
    body = "".join(
        f'<tr><td>{_e(name)}</td><td class="num">{_e(t)}</td><td class="num">{_e(v)}</td></tr>'
        for name, t, v in rows
    )
    return (
        "<table>"
        "<thead><tr><th>Metric</th><th class='num'>Train</th><th class='num'>Test</th></tr></thead>"
        "<tbody>" + body + "</tbody></table>"
    )


def render_dashboard(
    spec: SignalSpec,
    backtest: KpiBacktestResult,
    validation: ValidationReport,
    *,
    target_series: pd.Series,
    predictor_series: pd.Series,
    cadence_audits: list[dict] | None = None,
) -> str:
    """Return a self-contained HTML document for the run."""
    train_end_str = spec.validation.train_period.split("/")[1] if "/" in spec.validation.train_period else None
    train_end_ts = pd.Timestamp(train_end_str) if train_end_str else None

    chart_signal = signal_vs_target_chart(
        predictor_series,
        target_series,
        train_end=train_end_ts,
        title="Predictor vs target, standardised",
    )
    chart_lead_lag = lead_lag_chart(backtest.lead_lag, title="Lead-lag profile (test window)")
    chart_confidence = confidence_strip(validation.confidence_cap)

    audit_rows = []
    for audit in cadence_audits or []:
        audit_rows.append(
            f'<li><code>{_e(audit.get("dataset_id"))}</code> '
            f'{_e(audit.get("source_cadence"))} → {_e(audit.get("target_cadence"))} '
            f'by {_e(audit.get("aggregation"))} '
            f'(periods={_e(audit.get("periods_created"))}, '
            f'partial_dropped={_e(audit.get("partial_periods_dropped"))}).</li>'
        )
    audit_html = "<ul class='tight'>" + "".join(audit_rows) + "</ul>" if audit_rows else "<p class='meta'>(no rollup audits)</p>"

    caveats_html = []
    for check in validation.checks:
        if check.verdict in {"warn", "fail"}:
            caveats_html.append(
                f"<li><code>{_e(check.name)}</code>: {_e(check.explanation)}</li>"
            )
    caveats_block = (
        "<ul class='tight'>" + "".join(caveats_html) + "</ul>"
        if caveats_html
        else "<p class='meta'>(no caveats flagged)</p>"
    )

    next_iter_html = (
        "<ul class='tight'>"
        + "".join(f"<li>{_e(item)}</li>" for item in validation.recommended_next_iterations)
        + "</ul>"
        if validation.recommended_next_iterations
        else "<p class='meta'>(no next iteration recorded)</p>"
    )

    title_safe = _e(spec.signal_name)
    hyp_safe = _e(spec.hypothesis.statement)

    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title_safe}</title>
<style>{_CSS}</style>
</head>
<body>
<header>
  <h1>{title_safe}</h1>
  <p class="meta">Signal: <code>{_e(spec.signal_id)}</code> · Relationship: <code>{_e(validation.relationship_type)}</code></p>
  <div class="confidence-row">
    <div class="chart" style="margin:0">
      <img src="data:image/png;base64,{chart_confidence}" alt="confidence tier">
    </div>
    <div>
      <strong>Confidence cap: {_e(validation.confidence_cap.title())}</strong><br>
      <span class="binding">Binding constraint: {_e(validation.binding_constraint or "none")}</span>
    </div>
  </div>
</header>

<section>
  <h2>Hypothesis</h2>
  <p>{hyp_safe}</p>
</section>

<section>
  <h2>Predictor vs target</h2>
  <div class="chart"><img src="data:image/png;base64,{chart_signal}" alt="signal vs target"></div>
</section>

<section>
  <h2>Lead-lag profile</h2>
  <div class="chart"><img src="data:image/png;base64,{chart_lead_lag}" alt="lead-lag profile"></div>
  <p class="meta">Best feature: <code>{_e(backtest.best_feature)}</code>. OOS degradation: {_fmt(backtest.oos_degradation_pct)}%.</p>
</section>

<section>
  <h2>Backtest metrics</h2>
  {_metrics_table(backtest)}
</section>

<section>
  <h2>Validation checks</h2>
  {_checks_table(validation)}
</section>

<section>
  <h2>Cadence rollup</h2>
  {audit_html}
</section>

<section>
  <h2>Caveats</h2>
  {caveats_block}
</section>

<section>
  <h2>Next iteration</h2>
  {next_iter_html}
</section>

<footer>
  <p>Registry commit: <code>{_e(validation.registry_commit or "(none)")}</code> · Checked at: {_e(validation.checked_at)}.</p>
  <p>Generated by <code>deep-quantitative-research</code>.</p>
</footer>
</body>
</html>
"""
    return document
