#!/usr/bin/env python3
"""Generate synthetic data for the null-control demo.

The predictor is white noise. The target is constructed from a DIFFERENT
random stream so by construction there is no lead-lag relationship. A
correctly tuned pipeline should:

1. Find that no feature has a meaningful correlation with the target.
2. Cap confidence at ``low`` (binding constraints will include
   multiple_testing fail / warn and small effective sample size).
3. Emit a signal card that names the binding constraint and offers a
   defensible null verdict.

If the pipeline ever reports ``medium`` or ``high`` confidence on this
dataset, that's a regression: the pipeline is overstating evidence on
pure noise.

Seeds are fixed so the demo artefacts reproduce exactly.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 4242
START = "2008-01-31"
END = "2025-09-30"

OUT_DIR = Path(__file__).parent


def make_predictor() -> pd.DataFrame:
    """White-noise monthly count series, roughly matched to biotech-pos in scale."""
    rng = np.random.default_rng(SEED)
    months = pd.date_range(START, END, freq="ME")
    # Poisson(lambda=8) — same scale as biotech-pos, but no trend or regime shift.
    counts = rng.poisson(8.0, size=len(months))
    return pd.DataFrame({"date": months, "value": counts})


def make_target() -> pd.DataFrame:
    """Quarterly biotech subindex returns, from an INDEPENDENT random stream.

    By construction there is no relationship to the predictor. Any
    surviving correlation is luck and the validation gate should say so.
    """
    rng = np.random.default_rng(SEED + 99)
    quarters = pd.date_range(START, END, freq="QE")
    # Quarterly returns: realistic stdev around 6%.
    returns = rng.normal(0, 0.06, size=len(quarters))
    return pd.DataFrame({"date": quarters, "value": returns})


def main() -> int:
    predictor = make_predictor()
    target = make_target()

    predictor_path = OUT_DIR / "predictor.csv"
    target_path = OUT_DIR / "target.csv"
    predictor.to_csv(predictor_path, index=False)
    target.to_csv(target_path, index=False)

    print(f"wrote {len(predictor)} predictor rows (white noise) to {predictor_path}")
    print(f"wrote {len(target)} target rows (independent) to {target_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
