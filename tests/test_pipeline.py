from __future__ import annotations

import geopandas as gpd

from pain_politics.pipeline import build_analysis_dataset


def test_build_dataset_with_sample_data(project_paths_tmp):
    result = build_analysis_dataset(project_paths=project_paths_tmp, use_sample_data=True)

    assert result.used_sample_data is True
    assert result.output_path.exists()

    gdf = result.dataset
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert {"trump_shift_16_20", "od_rate_change", "distress_trump_zscore"} <= set(gdf.columns)
    assert gdf.geometry.notnull().all()
