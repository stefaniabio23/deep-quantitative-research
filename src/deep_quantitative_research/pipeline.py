"""End-to-end run-signal pipeline.

Wires the Phase 4 modules together: load SignalSpec + CSVs, roll up cadences,
apply target transform, build feature grid, run KPI backtest, run validation
gate, write artefacts, render signal card.

CLI entry point: ``deep-quant run-signal``. Python entry point:
``run_signal_from_paths``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from .backtest.kpi_backtest import run_kpi_backtest
from .dashboard import render_dashboard
from .features import assess as assess_feature_search
from .features.grid import build_grid
from .reporting.signal_card import render_signal_card
from .research.signal_spec import SignalSpec, load_signal_spec
from .timeseries.cadence import rollup
from .timeseries.transformations import apply_transform
from .validation import (
    check_autocorrelation,
    check_lag_sensitivity,
    check_missingness,
    check_outlier_sensitivity,
    check_outliers,
    check_regime_split,
    check_sample_size,
    check_stationarity_adf,
    check_stationarity_kpss,
    classify_relationship,
)
from .validation.gate import assemble as assemble_report


@dataclass
class RunSummary:
    run_dir: Path
    signal_id: str
    best_feature: str
    confidence_cap: str
    binding_constraint: str | None
    survives_oos: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_dir": str(self.run_dir),
            "signal_id": self.signal_id,
            "best_feature": self.best_feature,
            "confidence_cap": self.confidence_cap,
            "binding_constraint": self.binding_constraint,
            "survives_oos": self.survives_oos,
        }


def _load_csv_series(path: Path, *, date_col: str = "date", value_col: str = "value") -> pd.Series:
    df = pd.read_csv(path)
    if date_col not in df.columns:
        raise KeyError(
            f"{path} is missing the date column {date_col!r}. Available: {list(df.columns)}"
        )
    if value_col not in df.columns:
        raise KeyError(
            f"{path} is missing the value column {value_col!r}. Available: {list(df.columns)}"
        )
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values(date_col).set_index(date_col)
    return df[value_col].astype(float)


def _period_bounds(period: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    start, end = period.split("/")
    return pd.Timestamp(start.strip()), pd.Timestamp(end.strip())


def _rollup_with_audit(
    series: pd.Series,
    *,
    source_cadence: str,
    target_cadence: str,
    variable_type: str,
    aggregation: str | None,
    dataset_id: str,
) -> tuple[pd.Series, dict[str, Any]]:
    rolled, audit = rollup(
        series,
        source_cadence=source_cadence,
        target_cadence=target_cadence,
        variable_type=variable_type,
        aggregation=aggregation,
    )
    audit["dataset_id"] = dataset_id
    return rolled, audit


def run_signal(
    spec: SignalSpec,
    target: pd.Series,
    predictors: dict[str, pd.Series],
    *,
    run_dir: Path,
    registry_commit: str | None = None,
) -> RunSummary:
    """Drive the pipeline against in-memory Series. Tests use this directly."""
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    # --- cadence rollup ---------------------------------------------------
    cadence_audits: list[dict[str, Any]] = []

    target_rolled, target_audit = _rollup_with_audit(
        target,
        source_cadence=spec.target.cadence,
        target_cadence=spec.target.cadence,
        variable_type="flow",
        aggregation=None,
        dataset_id=spec.target.dataset_id,
    )
    cadence_audits.append(target_audit)

    if spec.target.transform:
        target_rolled = apply_transform(target_rolled, spec.target.transform).rename(spec.target.field)

    predictor_rolled: dict[str, pd.Series] = {}
    for predictor in spec.predictors:
        raw_series = predictors[predictor.dataset_id]
        rolled, audit = _rollup_with_audit(
            raw_series,
            source_cadence=predictor.cadence,
            target_cadence=spec.target.cadence,
            variable_type=predictor.variable_type or "flow",
            aggregation=predictor.default_aggregation,
            dataset_id=predictor.dataset_id,
        )
        predictor_rolled[predictor.dataset_id] = rolled
        cadence_audits.append(audit)

    # --- feature grid -----------------------------------------------------
    grid_result = build_grid(spec, predictor_rolled)

    # --- KPI backtest -----------------------------------------------------
    backtest = run_kpi_backtest(spec, grid_result.features, target_rolled)

    # --- feature search assessment ---------------------------------------
    feature_search = assess_feature_search(
        features_tested=grid_result.features_emitted,
        lags_tested=len(grid_result.lags),
        best_feature=backtest.best_feature,
        pre_specified_feature=spec.feature_grid.pre_specified_feature,
        out_of_sample_survives=backtest.survives_oos,
        truncated_at_max_features=grid_result.truncated_at_max_features,
    )

    # --- validation -------------------------------------------------------
    test_start, test_end = _period_bounds(spec.validation.test_period)
    test_target = target_rolled[(target_rolled.index >= test_start) & (target_rolled.index <= test_end)]
    best_feature_series = grid_result.features[backtest.best_feature]
    test_predictor = best_feature_series[
        (best_feature_series.index >= test_start) & (best_feature_series.index <= test_end)
    ]

    checks = [
        check_sample_size(len(test_target.dropna())),
        check_missingness(test_target),
        check_outliers(test_target),
        check_stationarity_adf(test_target),
        check_stationarity_kpss(test_target),
        check_autocorrelation(test_target),
        check_lag_sensitivity(backtest.lead_lag, best_lag=0),
        check_outlier_sensitivity(
            test_predictor,
            test_target,
            headline_corr=backtest.metrics_test.correlation,
        ),
    ]

    if spec.validation.regime_split:
        checks.append(
            check_regime_split(
                test_predictor,
                test_target,
                headline_corr=backtest.metrics_test.correlation,
            )
        )

    relationship_type, relationship_justification = classify_relationship(
        backtest.lead_lag,
        predictor=test_predictor,
        target=test_target,
        survives_oos=backtest.survives_oos,
        feature_name=backtest.best_feature,
    )

    recommended = []
    if feature_search.confidence_cap != "high":
        recommended.append(
            f"Pre-specify the feature in SignalSpec.feature_grid.pre_specified_feature; "
            f"current best ({backtest.best_feature}) was discovered."
        )
    if not backtest.survives_oos:
        recommended.append(
            "Investigate why OOS correlation drops. Probe a regime split and check release_lag handling."
        )
    for c in checks:
        if c.verdict in {"warn", "fail"} and c.name in {"stationarity_adf", "spurious_trend"}:
            recommended.append(
                f"Address {c.name}: differencing or detrending may stabilise the result."
            )

    validation = assemble_report(
        signal_id=spec.signal_id,
        checks=checks,
        feature_search_cap=feature_search.confidence_cap,
        survives_oos=backtest.survives_oos,
        walk_forward=spec.validation.walk_forward,
        relationship_type=relationship_type,
        registry_commit=registry_commit,
        recommended=recommended,
    )
    # Attach the justification as a note in the recommended list when useful.
    if relationship_type in {"spurious", "lagging"}:
        validation.recommended_next_iterations.insert(
            0, f"Relationship classified {relationship_type}: {relationship_justification}"
        )

    # --- artefacts --------------------------------------------------------
    (run_dir / "run.yaml").write_text(
        yaml.safe_dump(
            {
                "run_id": run_dir.name,
                "signal_id": spec.signal_id,
                "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "registry_commit": registry_commit,
                "spec_path": None,
            },
            sort_keys=False,
        )
    )
    (run_dir / "cadence-rollup-audit.yaml").write_text(
        yaml.safe_dump({"audits": cadence_audits}, sort_keys=False)
    )
    (run_dir / "feature-grid.yaml").write_text(
        yaml.safe_dump(grid_result.to_dict(), sort_keys=False)
    )
    (run_dir / "feature-search-log.yaml").write_text(
        yaml.safe_dump(feature_search.to_dict(), sort_keys=False)
    )
    (run_dir / "backtest-result.yaml").write_text(
        yaml.safe_dump(backtest.to_dict(), sort_keys=False)
    )
    (run_dir / "validation-report.yaml").write_text(
        yaml.safe_dump(validation.to_dict(), sort_keys=False)
    )

    card = render_signal_card(spec, backtest, validation, cadence_audits=cadence_audits)
    (run_dir / "signal-card.md").write_text(card)

    if spec.outputs.get("dashboard"):
        dashboard_html = render_dashboard(
            spec,
            backtest,
            validation,
            target_series=target_rolled,
            predictor_series=best_feature_series,
            cadence_audits=cadence_audits,
        )
        (run_dir / "dashboard.html").write_text(dashboard_html)

    return RunSummary(
        run_dir=run_dir,
        signal_id=spec.signal_id,
        best_feature=backtest.best_feature,
        confidence_cap=validation.confidence_cap,
        binding_constraint=validation.binding_constraint,
        survives_oos=backtest.survives_oos,
    )


def run_signal_from_paths(
    *,
    spec_path: Path | str,
    target_csv: Path | str,
    predictor_csvs: dict[str, Path | str],
    run_dir: Path | str,
    registry_commit: str | None = None,
    date_col: str = "date",
    value_col: str = "value",
) -> RunSummary:
    """CSV-on-disk entry point used by the CLI."""
    spec = load_signal_spec(spec_path)
    target = _load_csv_series(Path(target_csv), date_col=date_col, value_col=value_col)
    predictors = {
        dataset_id: _load_csv_series(Path(path), date_col=date_col, value_col=value_col)
        for dataset_id, path in predictor_csvs.items()
    }
    return run_signal(
        spec,
        target,
        predictors,
        run_dir=Path(run_dir),
        registry_commit=registry_commit,
    )
