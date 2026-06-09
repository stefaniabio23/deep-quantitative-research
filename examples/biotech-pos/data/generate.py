#!/usr/bin/env python3
"""Generate synthetic data for the biotech-pos worked demo.

Planted relationship: monthly Phase 3 oncology trial completion counts lead
quarterly biotech subindex returns by one quarter, with a coefficient that
survives realistic noise. Seed is fixed so the demo artefacts reproduce
exactly.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 2026
START = "2008-01-31"
END = "2025-09-30"

OUT_DIR = Path(__file__).parent


def make_predictor() -> pd.DataFrame:
    """Monthly Phase 3 oncology trial completion count.

    Poisson-distributed counts with a mild upward trend and a one-time
    regime shift in 2022, echoing post-pandemic approval throughput. Mean
    floats roughly from 6 to 12 over the period.
    """
    rng = np.random.default_rng(SEED)
    months = pd.date_range(START, END, freq="ME")
    trend = np.linspace(4.0, 12.0, len(months))
    regime_shift = np.where(months >= pd.Timestamp("2022-01-31"), 2.0, 0.0)
    lam = trend + regime_shift
    counts = rng.poisson(lam)
    return pd.DataFrame({"date": months, "value": counts})


def make_target(predictor: pd.DataFrame) -> pd.DataFrame:
    """Quarterly biotech subindex returns.

    Constructed so the predictor at lag 1 quarter has a real positive
    coefficient. The signal-to-noise ratio is realistic for an index-level
    quarterly return: the feature explains a meaningful but not dominant
    share of variance.
    """
    rng = np.random.default_rng(SEED + 1)

    pred_series = predictor.set_index("date")["value"].astype(float)
    quarterly_predictor = pred_series.resample("QE").sum()
    centered = (quarterly_predictor - quarterly_predictor.mean()) / quarterly_predictor.std()

    coefficient = 0.04
    noise_sigma = 0.06
    quarters = quarterly_predictor.index
    returns = coefficient * centered.shift(1) + rng.normal(0, noise_sigma, len(quarters))
    return pd.DataFrame({"date": quarters, "value": returns.values}).dropna()


def main() -> int:
    predictor = make_predictor()
    target = make_target(predictor)

    predictor_path = OUT_DIR / "predictor.csv"
    target_path = OUT_DIR / "target.csv"
    predictor.to_csv(predictor_path, index=False)
    target.to_csv(target_path, index=False)

    print(f"wrote {len(predictor)} predictor rows to {predictor_path}")
    print(f"wrote {len(target)} target rows to {target_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
