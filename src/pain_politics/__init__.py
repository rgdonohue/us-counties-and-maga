"""
Core package for the Pain & Politics county-level spatial analysis project.

The package exposes high-level entrypoints for data acquisition, processing,
and export so that notebooks and scripts can share a consistent API.
"""

from importlib.metadata import PackageNotFoundError, version


def get_version() -> str:
    """Return the installed package version or a dev placeholder."""
    try:
        return version("pain_politics")
    except PackageNotFoundError:
        return "0.0.dev0"


__all__ = ["get_version"]
