"""
Data catalog describing the inputs required for the analysis pipeline.

The catalog makes it easy to surface which files can be downloaded
programmatically and which require manual intervention.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Mapping, Optional

from ..config import paths
from ..utils import get_logger


logger = get_logger(__name__)


@dataclass(frozen=True)
class DataAsset:
    """Metadata about a raw data asset."""

    name: str
    path: Path
    acquisition: str  # "automated" | "manual" | "api"
    notes: Optional[str] = None

    @property
    def exists(self) -> bool:
        return self.path.exists()


class DataCatalog:
    """Container for describing and checking project data assets."""

    def __init__(self, assets: Optional[Iterable[DataAsset]] = None) -> None:
        self._assets: List[DataAsset] = list(assets or self.default_assets())

    def __iter__(self):
        return iter(self._assets)

    def __len__(self) -> int:
        return len(self._assets)

    @staticmethod
    def default_assets() -> Iterable[DataAsset]:
        """Return the baseline list of required raw data assets."""
        return [
            DataAsset(
                name="county_boundaries",
                path=paths.data_raw / "shapefiles" / "tl_2023_us_county.shp",
                acquisition="automated",
                notes="Downloaded from Census TIGER/Line (2023 vintage).",
            ),
            DataAsset(
                name="election_returns_2016",
                path=paths.data_raw / "elections" / "county_presidential_2016.csv",
                acquisition="manual",
                notes="MIT Election Lab county returns.",
            ),
            DataAsset(
                name="election_returns_2020",
                path=paths.data_raw / "elections" / "county_presidential_2020.csv",
                acquisition="manual",
                notes="MIT Election Lab county returns.",
            ),
            DataAsset(
                name="cdc_wonder_overdose_2013_2016",
                path=paths.data_raw / "cdc_wonder" / "overdose_2013_2016.txt",
                acquisition="manual",
                notes="Export from CDC WONDER; tab-delimited.",
            ),
            DataAsset(
                name="cdc_wonder_overdose_2017_2020",
                path=paths.data_raw / "cdc_wonder" / "overdose_2017_2020.txt",
                acquisition="manual",
                notes="Export from CDC WONDER; tab-delimited.",
            ),
            DataAsset(
                name="cdc_places",
                path=paths.data_raw / "cdc_places" / "places_county_2023.csv",
                acquisition="automated",
                notes="CDC PLACES county estimates (2023 release).",
            ),
            DataAsset(
                name="usda_rucc",
                path=paths.data_raw / "usda" / "rucc_2023.xlsx",
                acquisition="automated",
                notes="USDA Rural-Urban Continuum Codes.",
            ),
            DataAsset(
                name="acs_variables",
                path=paths.data_raw / "census" / "acs_variables.json",
                acquisition="api",
                notes="Variable manifest for ACS API pulls.",
            ),
            DataAsset(
                name="county_health_rankings_2024",
                path=paths.data_raw / "analytic_data2024.csv",
                acquisition="manual",
                notes="County Health Rankings 2024 analytic data CSV.",
            ),
            DataAsset(
                name="county_health_rankings_2016",
                path=paths.data_raw / "analytic_data2016.csv",
                acquisition="manual",
                notes="County Health Rankings 2016 analytic data CSV.",
            ),
        ]

    def summary(self) -> List[Mapping[str, str]]:
        """Return status summary for each asset."""
        summary: List[Mapping[str, str]] = []
        for asset in self._assets:
            summary.append(
                {
                    "name": asset.name,
                    "path": str(asset.path),
                    "acquisition": asset.acquisition,
                    "exists": "yes" if asset.exists else "no",
                    "notes": asset.notes or "",
                }
            )
        return summary

    def missing(self) -> List[DataAsset]:
        """Return list of assets whose files are absent."""
        return [asset for asset in self._assets if not asset.exists]

    def ensure_directories(self) -> None:
        """Create parent directories for all assets."""
        for asset in self._assets:
            asset.path.parent.mkdir(parents=True, exist_ok=True)

    def log_summary(self) -> None:
        """Emit a human-readable status table to the logger."""
        logger.info("Data catalog status:")
        for asset in self._assets:
            status = "✅" if asset.exists else "⚠️ "
            logger.info(
                "%s %-32s | %s | %s",
                status,
                asset.name,
                asset.acquisition.ljust(9),
                asset.path,
            )
