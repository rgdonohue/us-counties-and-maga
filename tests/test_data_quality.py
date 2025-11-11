"""Data quality tests for real data."""
from __future__ import annotations

import pytest
import pandas as pd
import geopandas as gpd

from pain_politics.config import paths


@pytest.mark.skipif(
    not (paths.data_processed / "counties_analysis.geojson").exists(),
    reason="Processed data not available"
)
class TestDataQuality:
    """Data quality checks on the processed analysis dataset."""
    
    @pytest.fixture(scope="class")
    def analysis_gdf(self):
        """Load the analysis dataset once for all tests."""
        return gpd.read_file(paths.data_processed / "counties_analysis.geojson")
    
    def test_no_duplicate_fips(self, analysis_gdf):
        """Check that each county appears only once."""
        assert not analysis_gdf["fips"].duplicated().any(), \
            f"Found {analysis_gdf['fips'].duplicated().sum()} duplicate FIPS codes"
    
    def test_trump_share_in_valid_range(self, analysis_gdf):
        """Check that Trump vote shares are valid percentages."""
        for year in [2016, 2020]:
            col = f"trump_share_{year}"
            if col in analysis_gdf.columns:
                valid = analysis_gdf[col].between(0, 100) | analysis_gdf[col].isna()
                assert valid.all(), \
                    f"Found {(~valid).sum()} invalid values in {col}"
    
    def test_overdose_rates_non_negative(self, analysis_gdf):
        """Check that overdose rates are non-negative."""
        for col in ["od_1316_rate", "od_1720_rate"]:
            if col in analysis_gdf.columns:
                valid = (analysis_gdf[col] >= 0) | analysis_gdf[col].isna()
                assert valid.all(), \
                    f"Found {(~valid).sum()} negative values in {col}"
    
    def test_distress_percentages_valid(self, analysis_gdf):
        """Check that distress percentages are in valid range."""
        pct_cols = [col for col in analysis_gdf.columns if "_pct" in col]
        for col in pct_cols:
            valid = analysis_gdf[col].between(0, 100) | analysis_gdf[col].isna()
            assert valid.all(), \
                f"Found {(~valid).sum()} invalid values in {col}"
    
    def test_geometry_validity(self, analysis_gdf):
        """Check that all geometries are valid."""
        assert analysis_gdf.geometry.notnull().all(), "Found null geometries"
        assert analysis_gdf.geometry.is_valid.all(), "Found invalid geometries"
    
    def test_fips_format(self, analysis_gdf):
        """Check that FIPS codes are properly formatted."""
        assert analysis_gdf["fips"].str.match(r"^\d{5}$").all(), \
            "FIPS codes must be 5-digit strings"
    
    def test_sufficient_data_coverage(self, analysis_gdf):
        """Check that we don't have excessive missing data."""
        key_cols = [
            "trump_share_2016",
            "freq_phys_distress_pct",
        ]
        
        for col in key_cols:
            if col in analysis_gdf.columns:
                missing_pct = (analysis_gdf[col].isna().sum() / len(analysis_gdf)) * 100
                assert missing_pct < 50, \
                    f"{col} has {missing_pct:.1f}% missing data (threshold: 50%)"
    
    def test_trump_shift_calculation(self, analysis_gdf):
        """Verify Trump shift is calculated correctly."""
        if all(col in analysis_gdf.columns for col in ["trump_share_2016", "trump_share_2020", "trump_shift_16_20"]):
            # Check a few rows manually
            sample = analysis_gdf[
                analysis_gdf["trump_share_2016"].notna() & 
                analysis_gdf["trump_share_2020"].notna()
            ].head(10)
            
            for _, row in sample.iterrows():
                expected_shift = row["trump_share_2020"] - row["trump_share_2016"]
                assert abs(row["trump_shift_16_20"] - expected_shift) < 0.01, \
                    f"Trump shift calculation error for FIPS {row['fips']}"
    
    def test_reasonable_county_count(self, analysis_gdf):
        """Check that we have a reasonable number of US counties."""
        # US has 3,143 counties + equivalents
        assert 3000 <= len(analysis_gdf) <= 3300, \
            f"Expected ~3,143 counties, got {len(analysis_gdf)}"
    
    def test_spatial_index_creation(self, analysis_gdf):
        """Check that spatial index can be created (geometry integrity)."""
        # This will fail if geometries are malformed
        try:
            _ = analysis_gdf.sindex
        except Exception as e:
            pytest.fail(f"Failed to create spatial index: {e}")

