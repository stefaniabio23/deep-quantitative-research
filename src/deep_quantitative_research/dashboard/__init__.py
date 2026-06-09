"""Single-signal dashboard HTML emitter with Tufte-aware matplotlib charts.

Phase 7 ships per-signal rendering. Phase 8+ adds multi-signal aggregation
(current read, contradiction map across a signal family).
"""

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
    "signal_vs_target_chart",
    "lead_lag_chart",
    "confidence_strip",
    "tufte_style",
    "fig_to_base64",
]
