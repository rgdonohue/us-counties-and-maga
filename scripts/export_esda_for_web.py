#!/usr/bin/env python3
"""
Export ESDA results for web visualization.

This script:
1. Loads the processed analysis dataset
2. Computes spatial weights and ESDA statistics (if not already present)
3. Exports to web/assets/counties_esda.geojson with all required fields
"""

from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np
from libpysal.weights import Queen
from esda import Moran_Local, Moran_Local_BV
from giddy.directional import Rose
import warnings
warnings.filterwarnings('ignore')

# Paths
project_root = Path(__file__).parent.parent
data_processed = project_root / "data" / "processed"
web_assets = project_root / "web" / "assets"
web_assets.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("ESDA Export for Web Visualization")
print("=" * 80)

# Load processed data
print("\n1. Loading processed data...")
gdf = gpd.read_file(data_processed / "counties_analysis.geojson")
print(f"   Loaded {len(gdf)} counties")

# Ensure NAME column exists (check alternatives)
if 'NAME' not in gdf.columns:
    if 'county_name' in gdf.columns:
        gdf['NAME'] = gdf['county_name']
    elif 'NAME' in gdf.columns.upper():
        name_col = [c for c in gdf.columns if c.upper() == 'NAME'][0]
        gdf['NAME'] = gdf[name_col]
    else:
        print("   Warning: No NAME column found, using FIPS as fallback")
        gdf['NAME'] = gdf['fips']

# Check if ESDA columns already exist
needs_lisa = 'trump_share_2016_lisa_cluster' not in gdf.columns
needs_bv = 'bv_cluster' not in gdf.columns
needs_hotspot = 'trump_share_2016_hotspot_conf' not in gdf.columns

if needs_lisa or needs_bv or needs_hotspot:
    print("\n2. Computing spatial weights...")
    w = Queen.from_dataframe(gdf, use_index=False)
    print(f"   Created weights matrix: {w.n} counties")
    
    if needs_lisa:
        print("\n3. Computing LISA clusters...")
        for var in ['trump_share_2016', 'freq_phys_distress_pct']:
            if var in gdf.columns:
                valid = gdf[var].notna()
                if valid.sum() > 100:
                    print(f"   Computing LISA for {var}...")
                    try:
                        lisa = Moran_Local(gdf[var].values, w, permutations=999)
                        gdf[f'{var}_lisa_cluster'] = 'Not Significant'
                        sig = lisa.p_sim < 0.05
                        gdf.loc[sig & (lisa.q == 1), f'{var}_lisa_cluster'] = 'HH'
                        gdf.loc[sig & (lisa.q == 2), f'{var}_lisa_cluster'] = 'LH'
                        gdf.loc[sig & (lisa.q == 3), f'{var}_lisa_cluster'] = 'LL'
                        gdf.loc[sig & (lisa.q == 4), f'{var}_lisa_cluster'] = 'HL'
                        print(f"      ✅ {sig.sum()} significant clusters")
                    except Exception as e:
                        print(f"      ⚠️  Error: {e}")
    
    if needs_bv:
        print("\n4. Computing bivariate LISA...")
        if all(col in gdf.columns for col in ['freq_phys_distress_pct', 'trump_share_2016']):
            valid = gdf[['freq_phys_distress_pct', 'trump_share_2016']].notna().all(axis=1)
            if valid.sum() > 100:
                print("   Computing bivariate LISA: distress × Trump...")
                try:
                    lisa_bv = Moran_Local_BV(
                        gdf['freq_phys_distress_pct'].values,
                        gdf['trump_share_2016'].values,
                        w, permutations=999
                    )
                    gdf['bv_cluster'] = 'Not Significant'
                    sig = lisa_bv.p_sim < 0.05
                    gdf.loc[sig & (lisa_bv.q == 1), 'bv_cluster'] = 'HH'
                    gdf.loc[sig & (lisa_bv.q == 2), 'bv_cluster'] = 'LH'
                    gdf.loc[sig & (lisa_bv.q == 3), 'bv_cluster'] = 'LL'
                    gdf.loc[sig & (lisa_bv.q == 4), 'bv_cluster'] = 'HL'
                    print(f"      ✅ {sig.sum()} significant bivariate clusters")
                except Exception as e:
                    print(f"      ⚠️  Error: {e}")
    
    if needs_hotspot:
        print("\n5. Computing hot spots (Getis-Ord Gi*)...")
        from esda import G_Local
        for var in ['trump_share_2016', 'freq_phys_distress_pct']:
            if var in gdf.columns:
                valid = gdf[var].notna()
                if valid.sum() > 100:
                    print(f"   Computing hot spots for {var}...")
                    try:
                        gi = G_Local(gdf[var].values, w, permutations=999)
                        gdf[f'{var}_hotspot_conf'] = 'Not Significant'
                        # Get Gi* values (use Gi attribute or z_sim for direction)
                        gi_values = gi.Gi if hasattr(gi, 'Gi') else gi.z_sim
                        # 99% confidence
                        sig_99 = gi.p_sim < 0.01
                        gdf.loc[sig_99 & (gi_values > 0), f'{var}_hotspot_conf'] = 'Hot Spot - 99% Conf'
                        gdf.loc[sig_99 & (gi_values < 0), f'{var}_hotspot_conf'] = 'Cold Spot - 99% Conf'
                        # 95% confidence
                        sig_95 = (gi.p_sim < 0.05) & (gi.p_sim >= 0.01)
                        gdf.loc[sig_95 & (gi_values > 0), f'{var}_hotspot_conf'] = 'Hot Spot - 95% Conf'
                        gdf.loc[sig_95 & (gi_values < 0), f'{var}_hotspot_conf'] = 'Cold Spot - 95% Conf'
                        # 90% confidence
                        sig_90 = (gi.p_sim < 0.10) & (gi.p_sim >= 0.05)
                        gdf.loc[sig_90 & (gi_values > 0), f'{var}_hotspot_conf'] = 'Hot Spot - 90% Conf'
                        gdf.loc[sig_90 & (gi_values < 0), f'{var}_hotspot_conf'] = 'Cold Spot - 90% Conf'
                        print(f"      ✅ Hot spot analysis complete")
                    except Exception as e:
                        print(f"      ⚠️  Error: {e}")
                        import traceback
                        traceback.print_exc()
else:
    print("\n2-5. ESDA columns already exist, skipping computation...")

# Prepare export
print("\n6. Preparing web export...")
web_columns = [
    'fips', 'NAME', 'geometry',
    # Electoral
    'trump_share_2016', 'trump_share_2020', 'trump_shift_16_20',
    # Pain/distress metrics
    'od_1316_rate', 'od_1720_rate', 'od_rate_change',
    'freq_phys_distress_pct', 'freq_mental_distress_pct',
    'arthritis_pct', 'depression_pct', 'diabetes_pct',
    # LISA clusters
    'trump_share_2016_lisa_cluster',
    'freq_phys_distress_pct_lisa_cluster',
    # Bivariate LISA
    'bv_cluster',
    # Hot spots
    'trump_share_2016_hotspot_conf',
    'freq_phys_distress_pct_hotspot_conf',
    # Controls
    'rucc', 'rural', 'rucc_category'
]

# Filter to available columns
available_cols = [c for c in web_columns if c in gdf.columns]
missing_cols = [c for c in web_columns if c not in gdf.columns]

print(f"   Available columns: {len(available_cols)}/{len(web_columns)}")
if missing_cols:
    print(f"   Missing columns: {missing_cols}")

web_gdf = gdf[available_cols].copy()

# Ensure CRS is WGS84
if web_gdf.crs is None or web_gdf.crs.to_epsg() != 4326:
    if web_gdf.crs is not None:
        web_gdf = web_gdf.to_crs('EPSG:4326')
    else:
        web_gdf = web_gdf.set_crs('EPSG:4326')

# Simplify geometry
print("\n7. Simplifying geometry...")
try:
    web_gdf['geometry'] = web_gdf['geometry'].simplify(0.01, preserve_topology=True)
    print("   ✅ Geometry simplified")
except Exception as e:
    print(f"   ⚠️  Could not simplify: {e}")

# Round numeric columns
numeric_cols = web_gdf.select_dtypes(include=[np.number]).columns
web_gdf[numeric_cols] = web_gdf[numeric_cols].round(2)

# Export
output_path = web_assets / "counties_esda.geojson"
print(f"\n8. Exporting to {output_path}...")
web_gdf.to_file(output_path, driver='GeoJSON')
file_size_mb = output_path.stat().st_size / (1024 * 1024)
print(f"   ✅ Exported {len(web_gdf)} counties ({file_size_mb:.1f} MB)")

# Summary
print("\n" + "=" * 80)
print("Export Summary")
print("=" * 80)
print(f"Counties: {len(web_gdf)}")
print(f"Columns: {len(available_cols)}")
print(f"File size: {file_size_mb:.1f} MB")
print(f"Output: {output_path}")
print("=" * 80)

