"""Spatial helper functions built on top of PySAL."""

from __future__ import annotations

from typing import Literal, Optional

import geopandas as gpd
import numpy as np
from libpysal.weights import KNN, Queen, Rook, W


WeightType = Literal["queen", "rook", "knn"]


def build_spatial_weights(
    gdf: gpd.GeoDataFrame, weight_type: WeightType = "queen", k_neighbors: int = 8
) -> W:
    """Create and row-standardize a spatial weights matrix."""
    if not isinstance(gdf, gpd.GeoDataFrame):
        raise TypeError("Input must be a GeoDataFrame with geometry.")

    if weight_type == "queen":
        w = Queen.from_dataframe(gdf, use_index=True)
    elif weight_type == "rook":
        w = Rook.from_dataframe(gdf, use_index=True)
    elif weight_type == "knn":
        w = KNN.from_dataframe(gdf, k=k_neighbors)
    else:
        raise ValueError(f"Unsupported weight_type: {weight_type}")

    w.transform = "r"
    return w


def add_spatial_lag(
    gdf: gpd.GeoDataFrame, column: str, w: Optional[W] = None, weight_type: WeightType = "queen"
) -> gpd.GeoDataFrame:
    """Append a spatial lag column for the specified feature."""
    if column not in gdf.columns:
        raise ValueError(f"Column '{column}' not found in GeoDataFrame.")

    local_w = w or build_spatial_weights(gdf, weight_type=weight_type)
    lag_values = local_w.sparse.dot(gdf[column].fillna(0).values)
    gdf = gdf.copy()
    gdf[f"{column}_lag"] = np.asarray(lag_values).flatten()
    return gdf

