"""Dashboard HTML emitters.

Phase 7 ships per-signal rendering (``render_dashboard``).
Phase 8 ships multi-signal aggregation: ``render_family_dashboard`` and
``render_family_from_run_dirs``.
"""

from .aggregator import (
    FamilySignal,
    render_family_dashboard,
    render_family_from_run_dirs,
)
from .charts import (
    confidence_strip,
    fig_to_base64,
    lead_lag_chart,
    signal_vs_target_chart,
    tufte_style,
)
from .html import render_dashboard

__all__ = [
    "render_dashboard",
    "render_family_dashboard",
    "render_family_from_run_dirs",
    "FamilySignal",
    "signal_vs_target_chart",
    "lead_lag_chart",
    "confidence_strip",
    "tufte_style",
    "fig_to_base64",
]
