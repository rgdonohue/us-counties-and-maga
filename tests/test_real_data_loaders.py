"""Tests for data loaders with real data files."""
from __future__ import annotations

import pytest
import pandas as pd
import geopandas as gpd

from pain_politics.data.loaders import (
    load_election_returns,
    load_county_boundaries,
    load_cdc_places,
    load_county_health_rankings,
)
from pain_politics.config import paths


@pytest.mark.skipif(
    not (paths.data_raw / "elections" / "county_presidential_2016.csv").exists(),
    reason="Real election data not available"
)
def test_load_election_returns_2016_real_data():
    """Test loading 2016 election returns with real data."""
    df = load_election_returns(year=2016)
    
    assert isinstance(df, pd.DataFrame)
    assert "fips" in df.columns
    assert "trump_share_2016" in df.columns
    assert "total_votes_2016" in df.columns
    
    # Check FIPS format (5-digit strings) - most should be valid
    valid_fips_count = df["fips"].str.len().eq(5).sum()
    assert valid_fips_count / len(df) > 0.99, "At least 99% of FIPS codes should be 5 digits"
    
    # Check percentages are in valid range (excluding nulls)
    valid_shares = df["trump_share_2016"].dropna()
    assert valid_shares.between(0, 100).all(), "Trump shares should be between 0-100%"
    
    # Check we have a reasonable number of counties
    assert len(df) > 3000  # US has ~3100+ counties


@pytest.mark.skipif(
    not (paths.data_raw / "shapefiles" / "tl_2023_us_county.shp").exists(),
    reason="Real shapefile data not available"
)
def test_load_county_boundaries_real_data():
    """Test loading county boundaries with real shapefile."""
    gdf = load_county_boundaries()
    
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert "fips" in gdf.columns
    assert "geometry" in gdf.columns
    assert gdf.geometry.notnull().all()
    
    # Check CRS is set
    assert gdf.crs is not None
    
    # Check we have counties
    assert len(gdf) > 3000


@pytest.mark.skipif(
    not (paths.data_raw / "cdc_places" / "places_county_2023.csv").exists(),
    reason="Real CDC PLACES data not available"
)
def test_load_cdc_places_real_data():
    """Test loading CDC PLACES data with real file."""
    df = load_cdc_places()
    
    assert isinstance(df, pd.DataFrame)
    assert "fips" in df.columns
    
    # Check expected health indicators
    expected_cols = [
        "arthritis_pct",
        "freq_phys_distress_pct",
        "freq_mental_distress_pct",
        "depression_pct",
    ]
    for col in expected_cols:
        if col in df.columns:
            # Check percentages are numeric and in valid range
            assert pd.api.types.is_numeric_dtype(df[col])
            assert df[col].between(0, 100).all() or df[col].isna().any()


@pytest.mark.skipif(
    not (paths.data_raw / "analytic_data2016.csv").exists(),
    reason="Real CHR data not available"
)
def test_load_chr_2016_real_data():
    """Test loading County Health Rankings 2016 with real data."""
    df = load_county_health_rankings(release_year=2016)
    
    assert isinstance(df, pd.DataFrame)
    assert "fips" in df.columns
    
    # Check FIPS format
    assert df["fips"].str.len().eq(5).all()
    
    # Check we have some expected metrics
    assert len(df.columns) > 5


@pytest.mark.skipif(
    not (paths.data_raw / "analytic_data2024.csv").exists(),
    reason="Real CHR 2024 data not available"
)
def test_load_chr_2024_real_data():
    """Test loading County Health Rankings 2024 with real data."""
    df = load_county_health_rankings(release_year=2024)
    
    assert isinstance(df, pd.DataFrame)
    assert "fips" in df.columns
    assert len(df) > 3000

