from __future__ import annotations

from pain_politics.data import DataCatalog, validate_required_files


def test_data_catalog_flags_missing_assets(project_paths_tmp):
    catalog = DataCatalog()
    valid, missing = validate_required_files(catalog)

    assert valid is False
    assert missing  # Should list at least one missing asset
