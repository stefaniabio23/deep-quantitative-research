"""Multiple testing correction. Benjamini-Hochberg by default."""

from __future__ import annotations

import numpy as np


def benjamini_hochberg(p_values: list[float], *, fdr: float = 0.05) -> list[bool]:
    """Return a list of booleans: True for hypotheses that survive BH at ``fdr``.

    Standard Benjamini-Hochberg procedure: sort p-values ascending, find the
    largest k where p_k <= k/m * fdr, reject hypotheses with rank <= k.
    """
    m = len(p_values)
    if m == 0:
        return []
    arr = np.asarray(p_values, dtype=float)
    order = np.argsort(arr)
    sorted_p = arr[order]
    thresholds = (np.arange(1, m + 1) / m) * fdr
    passed_sorted = sorted_p <= thresholds
    # Pass-through rule: once we find any True, every smaller p is also a pass.
    if passed_sorted.any():
        cutoff = np.max(np.where(passed_sorted)[0])
        keep_sorted = np.zeros(m, dtype=bool)
        keep_sorted[: cutoff + 1] = True
    else:
        keep_sorted = np.zeros(m, dtype=bool)
    # Restore original order.
    result = np.zeros(m, dtype=bool)
    result[order] = keep_sorted
    return [bool(x) for x in result]
