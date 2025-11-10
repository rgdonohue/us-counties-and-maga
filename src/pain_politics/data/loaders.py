"""Functions for loading raw data assets into pandas/geopandas structures."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Optional

import geopandas as gpd
import pandas as pd
import re

from ..config import paths
from ..utils import get_logger


logger = get_logger(__name__)


def load_county_boundaries(shapefile: Optional[Path] = None) -> gpd.GeoDataFrame:
    """Load county boundaries, defaulting to the TIGER shapefile."""
    file_path = shapefile or (paths.data_raw / "shapefiles" / "tl_2023_us_county.shp")
    gdf = gpd.read_file(file_path)
    # Rename columns to uppercase, but preserve geometry
    gdf = gdf.rename(columns={col: col.upper() for col in gdf.columns if col != 'geometry'})
    gdf["fips"] = gdf["GEOID"]
    return gdf


def load_election_returns(
    year: int,
    file_path: Optional[Path] = None,
    candidates: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    """Load county-level presidential returns for the specified year."""
    candidates = tuple(candidates or ("TRUMP", "CLINTON" if year == 2016 else "BIDEN"))
    path = file_path or (paths.data_raw / "elections" / f"county_presidential_{year}.csv")
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df.columns = df.columns.str.lower()

    # Ensure the necessary columns are present
    required = {"candidate", "candidatevotes", "totalvotes"}
    # Handle both formats: separate state_fips/county_fips OR combined county_fips
    if "state_fips" in df.columns and "county_fips" in df.columns:
        required.update({"state_fips", "county_fips"})
    elif "county_fips" in df.columns:
        required.add("county_fips")
    else:
        raise ValueError(f"Election file {path} missing FIPS columns")
    
    missing_cols = required.difference(df.columns)
    if missing_cols:
        raise ValueError(f"Election file {path} missing columns: {missing_cols}")

    # Build FIPS code
    if "state_fips" in df.columns:
        df["fips"] = (
            df["state_fips"].astype(str).str.zfill(2) + df["county_fips"].astype(str).str.zfill(3)
        )
    else:
        # county_fips already contains the full FIPS code
        df["fips"] = df["county_fips"].astype(str).str.replace(".0", "", regex=False).str.zfill(5)

    # Convert vote columns to numeric
    df["candidatevotes"] = pd.to_numeric(df["candidatevotes"], errors="coerce").fillna(0)
    df["totalvotes"] = pd.to_numeric(df["totalvotes"], errors="coerce").fillna(0)

    trump = (
        df[df["candidate"].str.contains("TRUMP", case=False, na=False)]
        .groupby("fips")["candidatevotes"]
        .sum()
    )
    opponent = (
        df[df["candidate"].str.contains(candidates[1], case=False, na=False)]
        .groupby("fips")["candidatevotes"]
        .sum()
    )

    totals = df.groupby("fips")["totalvotes"].sum()
    two_party_total = trump.add(opponent, fill_value=0)

    result = pd.DataFrame(
        {
            "fips": trump.index,
            f"trump_votes_{year}": trump,
            f"opponent_votes_{year}": opponent.reindex(trump.index).fillna(0),
            f"two_party_votes_{year}": two_party_total.reindex(trump.index).fillna(0),
            f"total_votes_{year}": totals.reindex(trump.index).fillna(0),
        }
    )
    # Avoid division by zero
    result[f"trump_share_{year}"] = (
        result[f"trump_votes_{year}"] / result[f"two_party_votes_{year}"]
    ).replace([float("inf"), -float("inf")], pd.NA) * 100
    result[f"trump_margin_{year}"] = (
        (result[f"trump_votes_{year}"] - result[f"opponent_votes_{year}"])
        / result[f"two_party_votes_{year}"]
    ).replace([float("inf"), -float("inf")], pd.NA) * 100

    return result.reset_index(drop=True)


def load_cdc_wonder(file_path: Optional[Path], metric_name: str) -> pd.DataFrame:
    """Load and tidy CDC WONDER mortality exports."""
    path = file_path or (paths.data_raw / "cdc_wonder" / f"{metric_name}.txt")
    df = pd.read_csv(path, sep="\t")

    if "County Code" not in df.columns:
        raise ValueError(f"CDC WONDER file {path} missing 'County Code'")

    df["fips"] = df["County Code"].astype(str).str.zfill(5)
    numeric_cols = ["Deaths", "Population", "Age Adjusted Rate"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    collapsed = (
        df.groupby("fips")
        .agg(
            deaths=("Deaths", "sum"),
            population=("Population", "sum"),
            age_adjusted_rate=("Age Adjusted Rate", "mean"),
        )
        .reset_index()
    )

    collapsed[f"{metric_name}_rate"] = (collapsed["deaths"] / collapsed["population"]) * 100_000
    collapsed = collapsed.rename(
        columns={
            "deaths": f"{metric_name}_deaths",
            "population": f"{metric_name}_population",
            "age_adjusted_rate": f"{metric_name}_aar",
        }
    )
    return collapsed


def load_cdc_places(file_path: Optional[Path] = None) -> pd.DataFrame:
    """Load the CDC PLACES county-level CSV and pivot indicators to wide format."""
    path = file_path or (paths.data_raw / "cdc_places" / "places_county_2023.csv")
    df = pd.read_csv(path, dtype=str, keep_default_na=False)

    if {"DataValueTypeID", "LocationID", "MeasureId", "Data_Value"}.difference(df.columns):
        raise ValueError("CDC PLACES file missing required columns")

    county_df = df[df["DataValueTypeID"] == "AgeAdjPrv"].copy()
    indicators = {
        "ARTHRITIS": "arthritis_pct",
        "PHLTH": "freq_phys_distress_pct",
        "MHLTH": "freq_mental_distress_pct",
        "DEPRESSION": "depression_pct",
        "BPHIGH": "high_bp_pct",
        "DIABETES": "diabetes_pct",
    }

    pivot = (
        county_df[county_df["MeasureId"].isin(indicators)]
        .pivot(index="LocationID", columns="MeasureId", values="Data_Value")
        .rename(columns=indicators)
    )
    pivot.index.name = "fips"
    pivot.index = pivot.index.astype(str).str.zfill(5)
    
    # Convert percentage columns to numeric
    for col in pivot.columns:
        pivot[col] = pd.to_numeric(pivot[col], errors="coerce")
    
    return pivot.reset_index()


def load_rucc(file_path: Optional[Path] = None) -> pd.DataFrame:
    """Load USDA Rural-Urban Continuum Codes."""
    path = file_path or (paths.data_raw / "usda" / "rucc_2023.xlsx")
    df = pd.read_excel(path)
    if {"FIPS", "RUCC_2023"}.difference(df.columns):
        raise ValueError("RUCC file missing required columns")

    df["fips"] = df["FIPS"].astype(str).str.zfill(5)
    df["rural"] = (df["RUCC_2023"] >= 4).astype(int)
    df["rucc_category"] = pd.cut(
        df["RUCC_2023"],
        bins=[0, 3, 6, 9],
        labels=["Metro", "Micropolitan", "Rural"],
        right=True,
    )

    return df[["fips", "RUCC_2023", "rural", "rucc_category"]].rename(
        columns={"RUCC_2023": "rucc"}
    )


def _snake_case(name: str) -> str:
    """Normalize messy headers (spaces, punctuation) into snake_case."""
    name = name.strip()
    name = re.sub(r"[()/%-]", " ", name)
    name = re.sub(r"[^0-9a-zA-Z]+", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_").lower()


def _deduplicate_columns(columns: Iterable[str]) -> list[str]:
    """Ensure column names are unique by appending numeric suffixes."""
    seen: Dict[str, int] = {}
    result: list[str] = []
    for col in columns:
        if col not in seen:
            seen[col] = 0
            result.append(col)
        else:
            seen[col] += 1
            result.append(f"{col}_{seen[col]}")
    return result


def load_county_health_rankings(
    release_year: int,
    file_path: Optional[Path] = None,
    select_metrics: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    """
    Load and clean the County Health Rankings analytic dataset for a given release year.

    Parameters
    ----------
    release_year:
        The annual ranking release year (e.g., 2024).
    file_path:
        Optional override path to the CSV. Defaults to ``data/raw/analytic_data{year}.csv``.
    select_metrics:
        Optional mapping from raw snake_case column name to final project column name.
        When omitted, a default set of distress-relevant measures is returned.

    Returns
    -------
    pandas.DataFrame
        Columns include ``fips``, ``chr_release_year``, ``chr_county_clustered`` (when available),
        and the selected metrics renamed per ``select_metrics``.
    """

    default_path = paths.data_raw / f"analytic_data{release_year}.csv"
    path = file_path or default_path

    if not path.exists():
        raise FileNotFoundError(f"County Health Rankings file not found at {path}")

    df = pd.read_csv(path, dtype=str, keep_default_na=False)

    normalized_cols = [_snake_case(col) for col in df.columns]
    normalized_cols = _deduplicate_columns(normalized_cols)
    df.columns = normalized_cols

    rename_base = {
        "state_fips_code": "state_fips",
        "county_fips_code": "county_fips",
        "5_digit_fips_code": "fips",
        "state_abbreviation": "state_abbr",
        "name": "county_name_chr",
        "release_year": "chr_release_year",
        "county_clustered_yes_1_no_0": "chr_county_clustered",
        "county_ranked_yes_1_no_0": "chr_county_ranked",
    }
    df = df.rename(columns=rename_base)

    if "fips" not in df.columns:
        raise ValueError("CHR dataset is missing a FIPS column after normalization.")

    df["fips"] = df["fips"].astype(str).str.strip()
    header_mask = df["fips"].str.lower() == "fipscode"
    if header_mask.any():
        df = df[~header_mask]

    df["fips"] = df["fips"].str.zfill(5)
    df = df[df["fips"] != "00000"]
    df = df[df["fips"].str[-3:] != "000"]
    if "state_fips" in df.columns:
        df["state_fips"] = df["state_fips"].astype(str).str.zfill(2)
    if "county_fips" in df.columns:
        df["county_fips"] = df["county_fips"].astype(str).str.zfill(3)

    metrics_map = select_metrics or {
        "frequent_physical_distress_raw_value": "chr_freq_phys_distress_pct",
        "frequent_physical_distress_ci_low": "chr_freq_phys_distress_ci_low",
        "frequent_physical_distress_ci_high": "chr_freq_phys_distress_ci_high",
        "frequent_mental_distress_raw_value": "chr_freq_mental_distress_pct",
        "poor_physical_health_days_raw_value": "chr_poor_physical_health_days",
        "poor_physical_health_days_ci_low": "chr_poor_physical_health_days_ci_low",
        "poor_physical_health_days_ci_high": "chr_poor_physical_health_days_ci_high",
        "poor_mental_health_days_raw_value": "chr_poor_mental_health_days",
        "poor_mental_health_days_ci_low": "chr_poor_mental_health_days_ci_low",
        "poor_mental_health_days_ci_high": "chr_poor_mental_health_days_ci_high",
        "drug_overdose_deaths_raw_value": "chr_drug_overdose_deaths_per_100k",
        "suicides_raw_value": "chr_suicides_per_100k",
        "life_expectancy_raw_value": "chr_life_expectancy_years",
    }

    available_metrics = {col: new for col, new in metrics_map.items() if col in df.columns}
    missing = [col for col in metrics_map if col not in df.columns]
    if missing:
        logger.debug(
            "CHR release %s missing expected columns: %s",
            release_year,
            ", ".join(missing),
        )

    base_cols = ["fips", "chr_release_year"]
    if "chr_county_clustered" in df.columns:
        base_cols.append("chr_county_clustered")
    if "chr_county_ranked" in df.columns:
        base_cols.append("chr_county_ranked")

    keep_cols = base_cols + list(available_metrics.keys())
    missing_base = [col for col in base_cols if col not in df.columns]
    if missing_base:
        raise ValueError(f"CHR dataset missing required columns: {missing_base}")

    df = df[keep_cols].rename(columns=available_metrics)

    numeric_cols = [col for col in df.columns if col not in {"fips"}]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")

    df["chr_release_year"] = df["chr_release_year"].fillna(release_year).astype(int)

    return df
