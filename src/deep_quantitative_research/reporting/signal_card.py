"""Render the canonical signal card from a SignalSpec, backtest result, and
validation report.
"""

from __future__ import annotations

from typing import Any

from ..backtest.kpi_backtest import KpiBacktestResult
from ..research.signal_spec import SignalSpec
from ..validation.gate import ValidationReport
from .markdown import bullets, section


def _fmt_metric(value: float | None) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float) and value != value:  # NaN
        return "n/a"
    return f"{value:.2f}"


def render_signal_card(
    spec: SignalSpec,
    backtest: KpiBacktestResult,
    validation: ValidationReport,
    *,
    cadence_audits: list[dict[str, Any]] | None = None,
) -> str:
    cadence_audits = cadence_audits or []

    hypothesis = section("Hypothesis", spec.hypothesis.statement)

    economic = section(
        "Economic Mapping",
        f"Predictor concepts to {spec.target.field} via the mechanism declared in the hypothesis. "
        f"Expected direction: {spec.hypothesis.expected_direction}.",
    )

    inputs = section(
        "Data Inputs",
        bullets(
            [f"Target: `{spec.target.dataset_id}` (`{spec.target.field}`, {spec.target.cadence}).",
             *[
                 f"Predictor: `{p.dataset_id}` (`{p.field}`, {p.cadence}, {p.variable_type or 'flow'}, "
                 f"agg={p.default_aggregation or 'default'})."
                 for p in spec.predictors
             ]]
        ),
    )

    timeseries_body_parts = []
    for audit in cadence_audits:
        timeseries_body_parts.append(
            f"- `{audit.get('dataset_id', 'unknown')}` rolled "
            f"{audit.get('source_cadence')} → {audit.get('target_cadence')} "
            f"by {audit.get('aggregation')} "
            f"(periods={audit.get('periods_created')}, "
            f"partial_dropped={audit.get('partial_periods_dropped')})."
        )
    timeseries_body_parts.append(
        f"\nBest feature: `{backtest.best_feature}`. "
        f"Train window {backtest.train_period}; test window {backtest.test_period}."
    )
    timeseries = section("Time-Series", "\n".join(timeseries_body_parts))

    model_logic = section(
        "Model Logic",
        "Single-feature linear specification. The test is whether the chosen feature "
        "leads the target with the expected sign, not how much can be curve-fit.",
    )

    metrics = backtest.metrics_test
    backtest_md = section(
        "Backtest Summary",
        "\n".join(
            [
                "| Metric | Train | Test |",
                "| --- | ---: | ---: |",
                f"| Correlation | {_fmt_metric(backtest.metrics_train.correlation)} | {_fmt_metric(metrics.correlation)} |",
                f"| Directional accuracy | {_fmt_metric(backtest.metrics_train.directional_accuracy)} | {_fmt_metric(metrics.directional_accuracy)} |",
                f"| MAE | n/a | {_fmt_metric(metrics.mae)} |",
                f"| MAPE (%) | n/a | {_fmt_metric(metrics.mape)} |",
                f"| RMSE | n/a | {_fmt_metric(metrics.rmse)} |",
                f"| Hit rate | n/a | {_fmt_metric(metrics.hit_rate)} |",
                "",
                f"OOS degradation: {_fmt_metric(backtest.oos_degradation_pct)}%.",
                f"Sample size (test): {metrics.sample_size}.",
            ]
        ),
    )

    current_read = section(
        "Current Read",
        backtest.notes,
    )

    related = section(
        "Related Signals",
        "(none registered yet; populate as the signal library grows)",
    )

    confidence = section(
        "Confidence",
        f"**{validation.confidence_cap.title()}.** "
        f"Binding constraint: `{validation.binding_constraint or 'none'}`. "
        "Tier semantics: see `skills/deep-quantitative-research/references/confidence-tiers.md`.",
    )

    caveat_lines = []
    for check in validation.checks:
        if check.verdict in {"warn", "fail"}:
            caveat_lines.append(f"`{check.name}`: {check.explanation}")
    caveats = section("Caveats", bullets(caveat_lines) or "No flagged caveats.")

    failure_modes = section(
        "Failure Modes",
        bullets(
            [
                "OOS correlation falling more than 30% below train would invalidate the signal.",
                "Cadence rollup misclassification (sum vs mean) would silently corrupt the target.",
            ]
        ),
    )

    next_iter = section(
        "Next Iteration",
        bullets(validation.recommended_next_iterations or ["Re-run with extended OOS window."]),
    )

    links = section(
        "Links",
        bullets(
            [
                f"SignalSpec: `experiments/specs/{spec.signal_id}.yaml`",
                "Run artefacts: `experiments/runs/<run-id>/`",
            ]
        ),
    )

    return "\n".join(
        [
            f"# {spec.signal_name}",
            "",
            hypothesis,
            economic,
            inputs,
            timeseries,
            model_logic,
            backtest_md,
            current_read,
            related,
            confidence,
            caveats,
            failure_modes,
            next_iter,
            links,
        ]
    )
