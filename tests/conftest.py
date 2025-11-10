from __future__ import annotations

from pathlib import Path

import pytest

from pain_politics.config import ProjectPaths


@pytest.fixture()
def project_paths_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ProjectPaths:
    """Provide an isolated project directory for tests."""
    root = tmp_path / "project"
    data_root = root / "data"
    project_paths = ProjectPaths(
        root=root,
        data_raw=data_root / "raw",
        data_interim=data_root / "interim",
        data_processed=data_root / "processed",
        data_external=data_root / "external",
        reports=root / "reports",
        web_assets=root / "web" / "assets",
        notebooks=root / "notebooks",
    )

    # Ensure directories exist
    project_paths.ensure()

    # Monkeypatch modules that cache the global `paths`.
    import pain_politics.config as config_module
    import pain_politics.data.catalog as catalog_module
    import pain_politics.data.loaders as loaders_module

    monkeypatch.setattr(config_module, "paths", project_paths, raising=False)
    monkeypatch.setattr(catalog_module, "paths", project_paths, raising=False)
    monkeypatch.setattr(loaders_module, "paths", project_paths, raising=False)

    return project_paths
