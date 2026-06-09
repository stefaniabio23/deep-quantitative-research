"""Walk-forward windows: yield (train, test) index slices over the test window."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class WalkForwardWindow:
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp

    def to_dict(self) -> dict[str, str]:
        return {
            "train_start": str(self.train_start.date()),
            "train_end": str(self.train_end.date()),
            "test_start": str(self.test_start.date()),
            "test_end": str(self.test_end.date()),
        }


def walk_forward_windows(
    index: pd.DatetimeIndex,
    *,
    train_start: str,
    train_end: str,
    test_start: str,
    test_end: str,
    step_periods: int = 1,
) -> list[WalkForwardWindow]:
    """Yield expanding-window splits across ``[test_start, test_end]``.

    Each window trains on everything from ``train_start`` through one
    period before the test bar, and tests on a single period bar. Single
    train/test split is a special case (``step_periods >= |test|``).
    """
    train_start_ts = pd.Timestamp(train_start)
    train_end_ts = pd.Timestamp(train_end)
    test_start_ts = pd.Timestamp(test_start)
    test_end_ts = pd.Timestamp(test_end)

    if train_end_ts >= test_start_ts:
        raise ValueError("train_end must be strictly before test_start")

    test_index = index[(index >= test_start_ts) & (index <= test_end_ts)]
    if len(test_index) == 0:
        return []

    windows: list[WalkForwardWindow] = []
    for i in range(0, len(test_index), step_periods):
        bar = test_index[i]
        # Expanding-window training: from train_start up to the bar before
        # this test point.
        prior = index[index < bar]
        if len(prior) == 0:
            continue
        windows.append(
            WalkForwardWindow(
                train_start=train_start_ts,
                train_end=prior[-1],
                test_start=bar,
                test_end=test_index[min(i + step_periods - 1, len(test_index) - 1)],
            )
        )
    return windows
