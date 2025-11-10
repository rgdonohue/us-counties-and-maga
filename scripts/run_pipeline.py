#!/usr/bin/env python3
"""
Lightweight wrapper for running the data build pipeline from the command line.

Usage examples:
    python scripts/run_pipeline.py build-data --sample
    python scripts/run_pipeline.py catalog
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the src directory is importable without installing the package.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from pain_politics.cli import main


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1:])
