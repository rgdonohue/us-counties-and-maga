#!/usr/bin/env python3
"""
Quick QA script to compare County Health Rankings metrics across releases.

Usage:
    python scripts/qa_chr_metrics.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

import pandas as pd  # noqa: E402

from pain_politics.data.loaders import load_county_health_rankings  # noqa: E402


def summarize(series: pd.Series) -> dict[str, float]:
    """Return a compact summary dictionary for QA output."""
    numeric = pd.to_numeric(series, errors="coerce")
    return {
        "count": int(numeric.count()),
        "mean": float(numeric.mean()) if numeric.count() else float("nan"),
        "p10": float(numeric.quantile(0.10)) if numeric.count() else float("nan"),
        "p90": float(numeric.quantile(0.90)) if numeric.count() else float("nan"),
        "min": float(numeric.min()) if numeric.count() else float("nan"),
        "max": float(numeric.max()) if numeric.count() else float("nan"),
    }


def main() -> None:
    chr_2024 = load_county_health_rankings(2024)
    chr_2016 = load_county_health_rankings(
        2016,
        select_metrics={
            "poor_physical_health_days_raw_value": "chr_poor_physical_health_days_2016",
            "poor_mental_health_days_raw_value": "chr_poor_mental_health_days_2016",
            "drug_overdose_deaths_raw_value": "chr_drug_overdose_deaths_per_100k_2016",
        },
    ).rename(
        columns={
            "chr_release_year": "chr_release_year_2016",
            "chr_county_ranked": "chr_county_ranked_2016",
        }
    )

    merged = chr_2024.merge(chr_2016, on="fips", how="left", suffixes=("", "_2016"))

    metrics = [
        ("chr_drug_overdose_deaths_per_100k", "chr_drug_overdose_deaths_per_100k_2016"),
        ("chr_poor_physical_health_days", "chr_poor_physical_health_days_2016"),
        ("chr_poor_mental_health_days", "chr_poor_mental_health_days_2016"),
    ]

    print("County Health Rankings QA Summary")
    print("=" * 40)
    for latest, earlier in metrics:
        if latest not in merged.columns or earlier not in merged.columns:
            continue
        delta = merged[latest] - merged[earlier]
        summary_latest = summarize(merged[latest])
        summary_earlier = summarize(merged[earlier])
        summary_delta = summarize(delta)

        print(f"\nMetric: {latest}")
        print(f"  2024 → {summary_latest}")
        print(f"  2016 → {summary_earlier}")
        print(f"  Δ(2024-2016) → {summary_delta}")


if __name__ == "__main__":
    main()
