"""Feature engineering for pain/distress and electoral metrics."""

from __future__ import annotations

import pandas as pd


def compute_distress_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add derived distress and electoral interaction metrics.

    Expected input columns:
        - trump_share_2016, trump_share_2020
        - od_1316_rate, od_1720_rate (optional)
        - freq_phys_distress_pct (optional)
    """

    df = df.copy()

    if {"trump_share_2016", "trump_share_2020"}.issubset(df.columns):
        df["trump_shift_16_20"] = df["trump_share_2020"] - df["trump_share_2016"]

    if {"od_1316_rate", "od_1720_rate"}.issubset(df.columns):
        df["od_rate_change"] = df["od_1720_rate"] - df["od_1316_rate"]

    if {"freq_phys_distress_pct", "trump_share_2016"}.issubset(df.columns):
        df["distress_trump_zscore"] = zscore_pair(
            df["freq_phys_distress_pct"], df["trump_share_2016"]
        )

    return df


def zscore_pair(series_a: pd.Series, series_b: pd.Series) -> pd.Series:
    """
    Return a composite z-score highlighting counties that score high on both inputs.

    The function standardizes each series and averages them, preserving NaNs.
    """
    standardized = [
        (series_a - series_a.mean()) / series_a.std(ddof=0),
        (series_b - series_b.mean()) / series_b.std(ddof=0),
    ]
    return sum(standardized) / len(standardized)

