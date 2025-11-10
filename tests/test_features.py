from __future__ import annotations

import pandas as pd

from pain_politics.features import compute_distress_metrics


def test_compute_distress_metrics_adds_expected_columns():
    data = pd.DataFrame(
        {
            "trump_share_2016": [60.0, 55.0, 70.0],
            "trump_share_2020": [65.0, 52.0, 72.0],
            "od_1316_rate": [20.0, 15.0, 30.0],
            "od_1720_rate": [25.0, 18.0, 35.0],
            "freq_phys_distress_pct": [12.0, 14.0, 11.0],
        }
    )

    enriched = compute_distress_metrics(data)

    assert "trump_shift_16_20" in enriched.columns
    assert "od_rate_change" in enriched.columns
    assert "distress_trump_zscore" in enriched.columns
    assert enriched["trump_shift_16_20"].iloc[0] == 5.0
