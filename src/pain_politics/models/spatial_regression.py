"""Reusable spatial regression workflow for county-level analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import geopandas as gpd
import numpy as np
import pandas as pd
import statsmodels.api as sm

from ..features import build_spatial_weights
from ..utils import get_logger


logger = get_logger(__name__)


@dataclass(frozen=True)
class ModelSummary:
    name: str
    coefficients: pd.DataFrame
    diagnostics: Dict[str, float]


class SpatialRegressionSuite:
    """
    Fit a baseline OLS model alongside spatial lag and error variants.

    The class collects coefficient estimates in tidy DataFrames so they can be
    serialized to JSON for the interactive story.
    """

    def __init__(
        self,
        gdf: gpd.GeoDataFrame,
        dependent: str,
        predictors: List[str],
        weight_type: str = "queen",
        dropna: bool = True,
    ) -> None:
        self.gdf = gdf
        self.dependent = dependent
        self.predictors = predictors
        self.weight_type = weight_type
        self.dropna = dropna
        self.results: Dict[str, ModelSummary] = {}

    def fit(self) -> Dict[str, ModelSummary]:
        """Run OLS and spatial models, storing results."""
        df = self.gdf[self.predictors + [self.dependent]].copy()
        if self.dropna:
            df = df.dropna()

        if df.empty:
            raise ValueError("No observations available after dropping missing values.")

        X = sm.add_constant(df[self.predictors])
        y = df[self.dependent]
        ols_model = sm.OLS(y, X).fit()
        self.results["ols"] = ModelSummary(
            name="OLS",
            coefficients=_coef_table(ols_model.params, ols_model.bse),
            diagnostics={
                "r_squared": float(ols_model.rsquared),
                "aic": float(ols_model.aic),
            },
        )

        try:
            from spreg import ML_Error, ML_Lag
        except ImportError:  # pragma: no cover - handled in tests
            logger.warning("spreg not available; skipping spatial models.")
            return self.results

        modeling_gdf = self.gdf.loc[df.index]
        w = build_spatial_weights(modeling_gdf, weight_type=self.weight_type)

        y_array = y.values.reshape(-1, 1)
        X_array = df[self.predictors].values

        lag_model = ML_Lag(
            y_array,
            X_array,
            w=w,
            name_y=self.dependent,
            name_x=self.predictors,
            name_w=self.weight_type,
            name_ds="counties",
        )

        self.results["spatial_lag"] = ModelSummary(
            name="Spatial Lag",
            coefficients=_coef_table(lag_model.betas.flatten(), lag_model.std_err),
            diagnostics={
                "rho": float(lag_model.rho),
                "log_likelihood": float(lag_model.logll),
                "aic": float(lag_model.aic),
            },
        )

        error_model = ML_Error(
            y_array,
            X_array,
            w=w,
            name_y=self.dependent,
            name_x=self.predictors,
            name_w=self.weight_type,
            name_ds="counties",
        )

        self.results["spatial_error"] = ModelSummary(
            name="Spatial Error",
            coefficients=_coef_table(error_model.betas.flatten(), error_model.std_err),
            diagnostics={
                "lambda": float(error_model.lam),
                "log_likelihood": float(error_model.logll),
                "aic": float(error_model.aic),
            },
        )

        return self.results

    def to_dataframe(self) -> pd.DataFrame:
        """Concatenate coefficient tables for downstream visualization."""
        if not self.results:
            raise RuntimeError("Models not fit. Call fit() first.")

        frames = []
        for name, summary in self.results.items():
            df = summary.coefficients.copy()
            df["model"] = name
            frames.append(df)
        return pd.concat(frames, ignore_index=True)


def _coef_table(estimates: np.ndarray, std_errors: np.ndarray) -> pd.DataFrame:
    """Return tidy coefficient table with z statistics."""
    estimates = np.asarray(estimates).reshape(-1)
    std_errors = np.asarray(std_errors).reshape(-1)
    z_scores = np.divide(estimates, std_errors, out=np.zeros_like(estimates), where=std_errors != 0)
    return pd.DataFrame(
        {
            "coefficient": estimates,
            "std_error": std_errors,
            "z_score": z_scores,
        }
    )

