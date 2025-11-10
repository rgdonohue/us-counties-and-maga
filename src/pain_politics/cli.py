"""Command-line interface for common project tasks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import paths
from .data import DataCatalog
from .pipeline import build_analysis_dataset
from .utils import get_logger


logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pain-politics",
        description="Utilities for the Pain & Politics spatial analysis project.",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("catalog", help="List required raw datasets and their status.")

    build_parser = subparsers.add_parser("build-data", help="Build the analysis GeoJSON file.")
    build_parser.add_argument(
        "--sample",
        action="store_true",
        help="Use synthetic sample data instead of raw assets.",
    )
    build_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional override for the output GeoJSON path.",
    )

    return parser


def main(args: list[str] | None = None) -> None:
    parser = build_parser()
    parsed = parser.parse_args(args=args)

    if parsed.command == "catalog":
        catalog = DataCatalog()
        catalog.log_summary()
        print(json.dumps(catalog.summary(), indent=2))
    elif parsed.command == "build-data":
        result = build_analysis_dataset(output_path=parsed.output, use_sample_data=parsed.sample)
        if result.missing_assets:
            logger.warning("Pipeline used sample data due to missing assets:")
            for message in result.missing_assets:
                logger.warning("  %s", message)
        logger.info("Dataset exported to %s", result.output_path)
    else:
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover
    main()
