"""Synthetic sample dataset used when real assets are unavailable."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Polygon


@dataclass(frozen=True)
class SampleCounty:
    fips: str
    county_name: str
    state_fips: str
    trump_share_2016: float
    trump_share_2020: float
    od_1316_rate: float
    od_1720_rate: float
    freq_phys_distress_pct: float
    arthritis_pct: float
    rural: int
    rucc: int


def build_sample_geo_frame() -> gpd.GeoDataFrame:
    """Return a small synthetic dataset that mimics the real schema."""
    counties: List[SampleCounty] = [
        SampleCounty(
            fips="01001",
            county_name="Autauga",
            state_fips="01",
            trump_share_2016=73.9,
            trump_share_2020=74.4,
            od_1316_rate=16.5,
            od_1720_rate=20.4,
            freq_phys_distress_pct=13.2,
            arthritis_pct=28.3,
            rural=0,
            rucc=2,
        ),
        SampleCounty(
            fips="01003",
            county_name="Baldwin",
            state_fips="01",
            trump_share_2016=78.8,
            trump_share_2020=79.2,
            od_1316_rate=19.1,
            od_1720_rate=24.6,
            freq_phys_distress_pct=12.1,
            arthritis_pct=27.2,
            rural=0,
            rucc=3,
        ),
        SampleCounty(
            fips="01005",
            county_name="Barbour",
            state_fips="01",
            trump_share_2016=68.5,
            trump_share_2020=70.1,
            od_1316_rate=25.3,
            od_1720_rate=32.8,
            freq_phys_distress_pct=17.6,
            arthritis_pct=31.2,
            rural=1,
            rucc=6,
        ),
        SampleCounty(
            fips="01007",
            county_name="Bibb",
            state_fips="01",
            trump_share_2016=76.5,
            trump_share_2020=77.6,
            od_1316_rate=14.7,
            od_1720_rate=18.1,
            freq_phys_distress_pct=15.2,
            arthritis_pct=30.5,
            rural=1,
            rucc=7,
        ),
        SampleCounty(
            fips="01009",
            county_name="Blount",
            state_fips="01",
            trump_share_2016=84.9,
            trump_share_2020=85.5,
            od_1316_rate=21.4,
            od_1720_rate=27.0,
            freq_phys_distress_pct=14.6,
            arthritis_pct=33.0,
            rural=1,
            rucc=6,
        ),
    ]

    df = pd.DataFrame([c.__dict__ for c in counties])
    df["rucc_category"] = pd.cut(
        df["rucc"], bins=[0, 3, 6, 9], labels=["Metro", "Micropolitan", "Rural"]
    )

    rng = np.random.default_rng(seed=42)
    df["ba_plus_pct"] = rng.normal(loc=20.0, scale=2.5, size=len(df)).round(1)
    df["median_income"] = rng.normal(loc=52000, scale=3500, size=len(df)).round().astype(int)

    geometries = []
    for idx, _ in enumerate(counties):
        x_offset = idx * 1.5
        polygon = Polygon(
            [
                (x_offset, 32.0),
                (x_offset + 1, 32.0),
                (x_offset + 1, 33.0),
                (x_offset, 33.0),
            ]
        )
        geometries.append(polygon)

    gdf = gpd.GeoDataFrame(df, geometry=geometries, crs="EPSG:4326")
    return gdf
