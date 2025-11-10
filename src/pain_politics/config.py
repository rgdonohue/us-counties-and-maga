"""
Project configuration helpers used across the pipeline.

These utilities avoid hard-coding relative paths inside notebooks by deriving
locations from the repository root. Keeping this centralized makes it safer to
refactor directory names later.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    """Resolve canonical project directories relative to the repo root."""

    root: Path
    data_raw: Path
    data_interim: Path
    data_processed: Path
    data_external: Path
    reports: Path
    web_assets: Path
    notebooks: Path

    @classmethod
    def from_env(cls) -> "ProjectPaths":
        """Instantiate paths using the PNP_PROJECT_ROOT env var or cwd."""
        root = Path(os.getenv("PNP_PROJECT_ROOT", Path.cwd())).resolve()
        data_root = root / "data"
        return cls(
            root=root,
            data_raw=data_root / "raw",
            data_interim=data_root / "interim",
            data_processed=data_root / "processed",
            data_external=data_root / "external",
            reports=root / "reports",
            web_assets=root / "web" / "assets",
            notebooks=root / "notebooks",
        )

    def ensure(self) -> None:
        """Create directories if they do not exist."""
        for path in (
            self.data_raw,
            self.data_interim,
            self.data_processed,
            self.reports,
            self.web_assets,
        ):
            path.mkdir(parents=True, exist_ok=True)


paths = ProjectPaths.from_env()
