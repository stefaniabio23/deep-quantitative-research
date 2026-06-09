"""Backtest engine: KPI-prediction path (Phase 4). Tradable path in 4b."""

from .kpi_backtest import KpiBacktestResult, run_kpi_backtest
from .metrics import KpiMetrics, kpi_metrics, lead_lag_profile, oos_degradation
from .walk_forward import WalkForwardWindow, walk_forward_windows

__all__ = [
    "KpiBacktestResult",
    "run_kpi_backtest",
    "KpiMetrics",
    "kpi_metrics",
    "lead_lag_profile",
    "oos_degradation",
    "WalkForwardWindow",
    "walk_forward_windows",
]
