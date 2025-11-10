from __future__ import annotations

import pandas as pd

from pain_politics.data.loaders import load_county_health_rankings


def test_load_county_health_rankings_2024():
    df = load_county_health_rankings(2024)

    expected_columns = {
        "fips",
        "chr_release_year",
        "chr_freq_phys_distress_pct",
        "chr_drug_overdose_deaths_per_100k",
        "chr_life_expectancy_years",
    }
    assert expected_columns <= set(df.columns)
    assert df["fips"].str.len().eq(5).all()
    assert df["chr_release_year"].nunique() == 1
    assert df["chr_release_year"].iloc[0] == 2024
    assert df.select_dtypes(include=["float64", "int64"]).shape[1] >= len(expected_columns) - 1



def test_load_county_health_rankings_2016():
    df = load_county_health_rankings(
        2016,
        select_metrics={
            "poor_physical_health_days_raw_value": "chr_poor_physical_health_days_2016",
            "poor_mental_health_days_raw_value": "chr_poor_mental_health_days_2016",
            "drug_overdose_deaths_raw_value": "chr_drug_overdose_deaths_per_100k_2016",
        },
    )

    expected_cols = {
        "fips",
        "chr_release_year",
        "chr_poor_physical_health_days_2016",
        "chr_drug_overdose_deaths_per_100k_2016",
    }
    assert expected_cols <= set(df.columns)
    assert df["fips"].str.endswith("000").sum() == 0
    assert df["chr_release_year"].nunique() == 1
    assert df["chr_release_year"].iloc[0] == 2016
