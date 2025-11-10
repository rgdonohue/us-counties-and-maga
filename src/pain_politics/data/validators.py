"""Validation helpers for required data inputs."""

from __future__ import annotations

from typing import Iterable, List, Tuple

from .catalog import DataAsset


def validate_required_files(assets: Iterable[DataAsset]) -> Tuple[bool, List[str]]:
    """Return (is_valid, missing_messages) for the provided assets."""

    missing = [asset for asset in assets if not asset.exists]
    if not missing:
        return True, []

    messages = [
        f"{asset.name} → expected at {asset.path} ({asset.acquisition})" for asset in missing
    ]
    return False, messages

