"""Integration tests for pipeline with real data."""
from __future__ import annotations

import pytest
import pandas as pd
import geopandas as gpd

from pain_politics.pipeline import build_analysis_dataset
from pain_politics.config import paths


@pytest.mark.skipif(
    not (paths.data_raw / "elections" / "county_presidential_2016.csv").exists()
    or not (paths.data_raw / "shapefiles" / "tl_2023_us_county.shp").exists(),
    reason="Real data files not available"
)
def test_build_dataset_with_real_data():
    """Test building the full analysis dataset with real data."""
    result = build_analysis_dataset(use_sample_data=False)
    
    assert result.used_sample_data is False
    assert result.output_path.exists()
    
    gdf = result.dataset
    assert isinstance(gdf, gpd.GeoDataFrame)
    
    # Check required columns exist
    required_cols = {
        "fips",
        "trump_share_2016",
        "trump_shift_16_20",
        "geometry"
    }
    assert required_cols <= set(gdf.columns)
    
    # Check geometry is valid
    assert gdf.geometry.notnull().all()
    
    # Check we have a reasonable number of counties
    assert len(gdf) > 3000
    
    # Check FIPS codes are 5 digits
    assert gdf["fips"].str.len().eq(5).all()
    
    # Check derived metrics exist
    if "distress_trump_zscore" in gdf.columns:
        assert pd.api.types.is_numeric_dtype(gdf["distress_trump_zscore"])


@pytest.mark.skipif(
    not (paths.data_processed / "counties_analysis.geojson").exists(),
    reason="Processed GeoJSON not available"
)
def test_read_processed_geojson():
    """Test reading the processed GeoJSON output."""
    gdf = gpd.read_file(paths.data_processed / "counties_analysis.geojson")
    
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert len(gdf) > 3000
    assert "fips" in gdf.columns
    assert gdf.geometry.notnull().all()
    
    # Check CRS is WGS84 (EPSG:4326) for web compatibility
    assert gdf.crs is not None
    if gdf.crs.to_epsg() is not None:
        assert gdf.crs.to_epsg() == 4326

