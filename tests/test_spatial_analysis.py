"""Tests for spatial analysis functionality."""
from __future__ import annotations

import pytest
import numpy as np
import geopandas as gpd
from libpysal.weights import Queen
from esda import Moran

from pain_politics.config import paths


@pytest.mark.skipif(
    not (paths.data_processed / "counties_analysis.geojson").exists(),
    reason="Processed data not available"
)
class TestSpatialAnalysis:
    """Validate spatial analysis computations."""
    
    @pytest.fixture(scope="class")
    def analysis_gdf(self):
        """Load the analysis dataset once for all tests."""
        return gpd.read_file(paths.data_processed / "counties_analysis.geojson")
    
    @pytest.fixture(scope="class")
    def spatial_weights(self, analysis_gdf):
        """Create Queen contiguity weights."""
        return Queen.from_dataframe(analysis_gdf)
    
    def test_spatial_weights_creation(self, spatial_weights):
        """Check that spatial weights can be created."""
        assert spatial_weights is not None
        assert spatial_weights.n > 3000
        
        # Check that most counties have neighbors
        islands = [i for i, neighbors in spatial_weights.neighbors.items() if len(neighbors) == 0]
        island_pct = (len(islands) / spatial_weights.n) * 100
        assert island_pct < 5, f"{island_pct:.1f}% of counties are spatial islands (threshold: 5%)"
    
    def test_morans_i_trump_support(self, analysis_gdf, spatial_weights):
        """Test Moran's I calculation for Trump support."""
        if "trump_share_2016" not in analysis_gdf.columns:
            pytest.skip("trump_share_2016 not available")
        
        # Use fillna for spatial analysis (removes dimension mismatch issues)
        valid_data = analysis_gdf["trump_share_2016"].fillna(analysis_gdf["trump_share_2016"].mean())
        
        if valid_data.notna().sum() < 100:
            pytest.skip("Insufficient non-null data")
        
        mi = Moran(valid_data.values, spatial_weights)
        
        # Check that Moran's I is positive (spatial clustering)
        assert mi.I > 0, "Expected positive spatial autocorrelation for Trump support"
        
        # Check that it's statistically significant
        assert mi.p_sim < 0.05, "Moran's I should be statistically significant"
        
        # Check that I is in valid range [-1, 1]
        assert -1 <= mi.I <= 1, f"Moran's I out of range: {mi.I}"
    
    def test_morans_i_distress(self, analysis_gdf, spatial_weights):
        """Test Moran's I calculation for physical distress."""
        if "freq_phys_distress_pct" not in analysis_gdf.columns:
            pytest.skip("freq_phys_distress_pct not available")
        
        valid_data = analysis_gdf["freq_phys_distress_pct"].dropna()
        
        if len(valid_data) < 100:
            pytest.skip("Insufficient non-null data")
        
        mi = Moran(valid_data.values, spatial_weights)
        
        assert mi.I > 0, "Expected positive spatial autocorrelation for distress"
        assert mi.p_sim < 0.05, "Moran's I should be statistically significant"
        assert -1 <= mi.I <= 1, f"Moran's I out of range: {mi.I}"
    
    def test_spatial_lag_calculation(self, analysis_gdf, spatial_weights):
        """Test that spatial lags can be calculated."""
        if "trump_share_2016" not in analysis_gdf.columns:
            pytest.skip("trump_share_2016 not available")
        
        from libpysal.weights import lag_spatial
        
        valid_data = analysis_gdf["trump_share_2016"].fillna(0)
        lag = lag_spatial(spatial_weights, valid_data.values)
        
        assert len(lag) == len(valid_data)
        assert not np.isnan(lag).all()
        assert np.isfinite(lag).all()
    
    def test_crs_is_projected_or_geographic(self, analysis_gdf):
        """Check that the GeoDataFrame has a valid CRS."""
        assert analysis_gdf.crs is not None, "CRS is not set"
        
        # Should be either WGS84 (4326) for web or a valid projected CRS
        epsg = analysis_gdf.crs.to_epsg()
        assert epsg is not None, "CRS must have an EPSG code"

