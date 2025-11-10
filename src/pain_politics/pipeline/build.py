"""Pipeline entrypoints for constructing the analysis-ready dataset."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import geopandas as gpd
import pandas as pd

from ..config import ProjectPaths, paths
from ..data import DataCatalog, validate_required_files
from ..data.loaders import (
    load_cdc_places,
    load_cdc_wonder,
    load_county_boundaries,
    load_county_health_rankings,
    load_election_returns,
    load_rucc,
)
from ..features import compute_distress_metrics
from ..utils import get_logger
from .sample_data import build_sample_geo_frame


logger = get_logger(__name__)


@dataclass
class BuildResult:
    dataset: gpd.GeoDataFrame
    output_path: Path
    missing_assets: List[str]
    used_sample_data: bool


def build_analysis_dataset(
    project_paths: ProjectPaths = paths,
    output_path: Optional[Path] = None,
    use_sample_data: bool = False,
) -> BuildResult:
    """
    Build and persist the analysis-ready county GeoDataFrame.

    Parameters
    ----------
    project_paths:
        Optional override for the default project directory structure.
    output_path:
        Optional target path for the GeoJSON export. Defaults to
        ``project_paths.data_processed / "counties_analysis.geojson"``.
    use_sample_data:
        When true (or when critical raw assets are missing), a synthetic sample
        dataset is generated so downstream steps still have something to run
        against.
    """

    catalog = DataCatalog()
    catalog.ensure_directories()

    missing_messages: List[str] = []
    if not use_sample_data:
        valid, missing_messages = validate_required_files(catalog)
        if not valid:
            logger.warning("Missing required raw assets; falling back to sample data.")
            for message in missing_messages:
                logger.warning("  %s", message)
            use_sample_data = True

    if use_sample_data:
        gdf = build_sample_geo_frame()
    else:
        gdf = _build_from_raw_assets(project_paths)

    gdf = compute_distress_metrics(gdf)
    gdf = gdf.to_crs("EPSG:4326")

    project_paths.ensure()
    target = output_path or (project_paths.data_processed / "counties_analysis.geojson")
    gdf.to_file(target, driver="GeoJSON")
    logger.info("Exported %s counties to %s", len(gdf), target)

    return BuildResult(
        dataset=gdf,
        output_path=target,
        missing_assets=missing_messages,
        used_sample_data=use_sample_data,
    )


def _build_from_raw_assets(project_paths: ProjectPaths) -> gpd.GeoDataFrame:
    """Load, merge, and tidy the canonical raw datasets."""
    counties = load_county_boundaries()
    counties = counties[~counties["STATEFP"].isin(["02", "15", "60", "66", "69", "72", "78"])]
    counties = counties.rename(columns={"NAME": "county_name", "STATEFP": "state_fips"})

    election_2016 = load_election_returns(2016)
    election_2020 = load_election_returns(2020)

    # CDC WONDER overdose exports
    overdose_1316 = load_cdc_wonder(
        project_paths.data_raw / "cdc_wonder" / "overdose_2013_2016.txt", "od_1316"
    )
    overdose_1720 = load_cdc_wonder(
        project_paths.data_raw / "cdc_wonder" / "overdose_2017_2020.txt", "od_1720"
    )

    places = load_cdc_places()
    rucc = load_rucc()
    chr_2024 = load_county_health_rankings(2024)
    chr_2016 = load_county_health_rankings(
        2016,
        select_metrics={
            "poor_physical_health_days_raw_value": "chr_poor_physical_health_days_2016",
            "poor_mental_health_days_raw_value": "chr_poor_mental_health_days_2016",
            "drug_overdose_deaths_raw_value": "chr_drug_overdose_deaths_per_100k_2016",
        },
    ).rename(
        columns={
            "chr_release_year": "chr_release_year_2016",
            "chr_county_ranked": "chr_county_ranked_2016",
        }
    )

    dfs: List[pd.DataFrame] = [
        election_2016,
        election_2020,
        overdose_1316,
        overdose_1720,
        places,
        rucc,
        chr_2024,
        chr_2016,
    ]

    merged = counties[["fips", "county_name", "state_fips", "geometry"]].copy()

    for df in dfs:
        merged = merged.merge(df, on="fips", how="left")

    merged["ba_plus_pct"] = merged.get("ba_plus_pct", pd.Series(dtype=float))
    merged["median_income"] = merged.get("median_income", pd.Series(dtype=float))

    if {
        "chr_drug_overdose_deaths_per_100k",
        "chr_drug_overdose_deaths_per_100k_2016",
    }.issubset(merged.columns):
        merged["chr_drug_overdose_change_16_24"] = (
            merged["chr_drug_overdose_deaths_per_100k"]
            - merged["chr_drug_overdose_deaths_per_100k_2016"]
        )

    if {
        "chr_poor_physical_health_days",
        "chr_poor_physical_health_days_2016",
    }.issubset(merged.columns):
        merged["chr_poor_physical_health_days_change_16_24"] = (
            merged["chr_poor_physical_health_days"]
            - merged["chr_poor_physical_health_days_2016"]
        )

    if {
        "chr_poor_mental_health_days",
        "chr_poor_mental_health_days_2016",
    }.issubset(merged.columns):
        merged["chr_poor_mental_health_days_change_16_24"] = (
            merged["chr_poor_mental_health_days"]
            - merged["chr_poor_mental_health_days_2016"]
        )

    return gpd.GeoDataFrame(merged, geometry="geometry", crs=counties.crs)
