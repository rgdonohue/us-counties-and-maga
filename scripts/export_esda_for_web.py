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
                # Subset to valid rows and align weights matrix
                valid_mask = gdf[var].notna()
                valid_indices = gdf.index[valid_mask]
                
                if len(valid_indices) > 100:
                    print(f"   Computing LISA for {var} ({len(valid_indices)} valid counties)...")
                    try:
                        # Create subset GeoDataFrame and weights matrix for valid rows only
                        gdf_subset = gdf.loc[valid_indices].copy()
                        w_subset = Queen.from_dataframe(gdf_subset, use_index=False)
                        var_values = gdf_subset[var].values
                        
                        # Run LISA on subset
                        lisa = Moran_Local(var_values, w_subset, permutations=999)
                        
                        # Initialize cluster column for all counties
                        gdf[f'{var}_lisa_cluster'] = 'Not Significant'
                        
                        # Map results back to full dataframe using valid indices
                        sig = lisa.p_sim < 0.05
                        gdf.loc[valid_indices[sig & (lisa.q == 1)], f'{var}_lisa_cluster'] = 'HH'
                        gdf.loc[valid_indices[sig & (lisa.q == 2)], f'{var}_lisa_cluster'] = 'LH'
                        gdf.loc[valid_indices[sig & (lisa.q == 3)], f'{var}_lisa_cluster'] = 'LL'
                        gdf.loc[valid_indices[sig & (lisa.q == 4)], f'{var}_lisa_cluster'] = 'HL'
                        print(f"      ✅ {sig.sum()} significant clusters")
                    except Exception as e:
                        print(f"      ⚠️  Error: {e}")
                        import traceback
                        traceback.print_exc()
    
    if needs_bv:
        print("\n4. Computing bivariate LISA...")
        if all(col in gdf.columns for col in ['freq_phys_distress_pct', 'trump_share_2016']):
            # Subset to valid rows (both variables must be non-null)
            valid_mask = gdf[['freq_phys_distress_pct', 'trump_share_2016']].notna().all(axis=1)
            valid_indices = gdf.index[valid_mask]
            
            if len(valid_indices) > 100:
                print(f"   Computing bivariate LISA: distress × Trump ({len(valid_indices)} valid counties)...")
                try:
                    # Create subset GeoDataFrame and weights matrix for valid rows only
                    gdf_subset = gdf.loc[valid_indices].copy()
                    w_subset = Queen.from_dataframe(gdf_subset, use_index=False)
                    var1_values = gdf_subset['freq_phys_distress_pct'].values
                    var2_values = gdf_subset['trump_share_2016'].values
                    
                    # Run bivariate LISA on subset
                    lisa_bv = Moran_Local_BV(var1_values, var2_values, w_subset, permutations=999)
                    
                    # Initialize cluster column for all counties
                    gdf['bv_cluster'] = 'Not Significant'
                    
                    # Map results back to full dataframe using valid indices
                    sig = lisa_bv.p_sim < 0.05
                    gdf.loc[valid_indices[sig & (lisa_bv.q == 1)], 'bv_cluster'] = 'HH'
                    gdf.loc[valid_indices[sig & (lisa_bv.q == 2)], 'bv_cluster'] = 'LH'
                    gdf.loc[valid_indices[sig & (lisa_bv.q == 3)], 'bv_cluster'] = 'LL'
                    gdf.loc[valid_indices[sig & (lisa_bv.q == 4)], 'bv_cluster'] = 'HL'
                    print(f"      ✅ {sig.sum()} significant bivariate clusters")
                except Exception as e:
                    print(f"      ⚠️  Error: {e}")
                    import traceback
                    traceback.print_exc()
    
    if needs_hotspot:
        print("\n5. Computing hot spots (Getis-Ord Gi*)...")
        from esda import G_Local
        for var in ['trump_share_2016', 'freq_phys_distress_pct']:
            if var in gdf.columns:
                # Subset to valid rows and align weights matrix
                valid_mask = gdf[var].notna()
                valid_indices = gdf.index[valid_mask]
                
                if len(valid_indices) > 100:
                    print(f"   Computing hot spots for {var} ({len(valid_indices)} valid counties)...")
                    try:
                        # Create subset GeoDataFrame and weights matrix for valid rows only
                        gdf_subset = gdf.loc[valid_indices].copy()
                        w_subset = Queen.from_dataframe(gdf_subset, use_index=False)
                        var_values = gdf_subset[var].values
                        
                        # Run hot spot analysis on subset
                        gi = G_Local(var_values, w_subset, permutations=999)
                        
                        # Initialize hotspot column for all counties
                        gdf[f'{var}_hotspot_conf'] = 'Not Significant'
                        
                        # Get Gi* values (use Gi attribute or z_sim for direction)
                        gi_values = gi.Gi if hasattr(gi, 'Gi') else gi.z_sim
                        
                        # Map results back to full dataframe using valid indices
                        # 99% confidence
                        sig_99 = gi.p_sim < 0.01
                        gdf.loc[valid_indices[sig_99 & (gi_values > 0)], f'{var}_hotspot_conf'] = 'Hot Spot - 99% Conf'
                        gdf.loc[valid_indices[sig_99 & (gi_values < 0)], f'{var}_hotspot_conf'] = 'Cold Spot - 99% Conf'
                        # 95% confidence
                        sig_95 = (gi.p_sim < 0.05) & (gi.p_sim >= 0.01)
                        gdf.loc[valid_indices[sig_95 & (gi_values > 0)], f'{var}_hotspot_conf'] = 'Hot Spot - 95% Conf'
                        gdf.loc[valid_indices[sig_95 & (gi_values < 0)], f'{var}_hotspot_conf'] = 'Cold Spot - 95% Conf'
                        # 90% confidence
                        sig_90 = (gi.p_sim < 0.10) & (gi.p_sim >= 0.05)
                        gdf.loc[valid_indices[sig_90 & (gi_values > 0)], f'{var}_hotspot_conf'] = 'Hot Spot - 90% Conf'
                        gdf.loc[valid_indices[sig_90 & (gi_values < 0)], f'{var}_hotspot_conf'] = 'Cold Spot - 90% Conf'
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

# Round numeric columns (exclude categorical integers)
numeric_cols = web_gdf.select_dtypes(include=[np.number]).columns
# Exclude categorical integer fields from rounding (they should remain integers)
categorical_int_cols = ['rucc', 'rural']  # fips is string, not numeric
cols_to_round = [c for c in numeric_cols if c not in categorical_int_cols]
web_gdf[cols_to_round] = web_gdf[cols_to_round].round(2)

# Ensure categorical integers remain integers (not floats from previous operations)
for cat_col in categorical_int_cols:
    if cat_col in web_gdf.columns:
        if web_gdf[cat_col].dtype in [np.float64, np.float32]:
            # Convert to nullable integer (handles NaN)
            web_gdf[cat_col] = web_gdf[cat_col].astype('Int64')
        elif pd.api.types.is_integer_dtype(web_gdf[cat_col]):
            # Already integer, ensure it stays that way
            pass

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

