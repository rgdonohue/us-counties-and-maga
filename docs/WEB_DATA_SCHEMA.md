# Web Visualization Data Schema

This document defines the expected schema for `web/assets/counties_esda.geojson` consumed by the MapLibre scrollytelling interface.

## GeoJSON Structure

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": { ... },
      "properties": { ... }
    }
  ]
}
```

## Required Properties

### Identifiers
- **`fips`** (string, required): 5-digit FIPS code (e.g., "01001")
- **`NAME`** (string, required): County name (e.g., "Autauga County")

### Electoral Variables
- **`trump_share_2016`** (number, nullable): Trump vote share in 2016 (%)
  - Range: 0-100
  - Nullable: Yes (suppressed counties)
- **`trump_share_2020`** (number, nullable): Trump vote share in 2020 (%)
  - Range: 0-100
  - Nullable: Yes
- **`trump_shift_16_20`** (number, nullable): Change in Trump support 2016→2020 (%)
  - Range: typically -20 to +20
  - Nullable: Yes

### Pain/Distress Metrics
- **`freq_phys_distress_pct`** (number, nullable): Frequent physical distress (%)
  - Range: 0-100
  - Nullable: Yes (CDC suppresses small counties)
- **`freq_mental_distress_pct`** (number, nullable): Frequent mental distress (%)
  - Range: 0-100
  - Nullable: Yes
- **`arthritis_pct`** (number, nullable): Arthritis prevalence (%)
  - Range: 0-100
  - Nullable: Yes
- **`depression_pct`** (number, nullable): Depression prevalence (%)
  - Range: 0-100
  - Nullable: Yes
- **`diabetes_pct`** (number, nullable): Diabetes prevalence (%)
  - Range: 0-100
  - Nullable: Yes
- **`od_1316_rate`** (number, nullable): Overdose mortality rate 2013-2016 (per 100k)
  - Range: typically 0-100
  - Nullable: Yes (CDC suppresses small counts)
- **`od_1720_rate`** (number, nullable): Overdose mortality rate 2017-2020 (per 100k)
  - Range: typically 0-100
  - Nullable: Yes
- **`od_rate_change`** (number, nullable): Change in overdose rate (%)
  - Nullable: Yes

### ESDA Results
- **`bv_cluster`** (string, nullable): Bivariate LISA cluster type
  - Values: `"HH"`, `"HL"`, `"LH"`, `"LL"`, `"Not Significant"`
  - Nullable: Yes (missing counties default to "Not Significant")
- **`trump_share_2016_lisa_cluster`** (string, nullable): LISA cluster for Trump 2016
  - Values: `"HH"`, `"HL"`, `"LH"`, `"LL"`, `"Not Significant"`
  - Nullable: Yes
- **`freq_phys_distress_pct_lisa_cluster`** (string, nullable): LISA cluster for physical distress
  - Values: `"HH"`, `"HL"`, `"LH"`, `"LL"`, `"Not Significant"`
  - Nullable: Yes
- **`trump_share_2016_hotspot_conf`** (string, nullable): Hot spot confidence level
  - Values: `"Hot Spot - 99% Conf"`, `"Hot Spot - 95% Conf"`, `"Hot Spot - 90% Conf"`, `"Cold Spot - 90% Conf"`, `"Cold Spot - 95% Conf"`, `"Cold Spot - 99% Conf"`, `"Not Significant"`
  - Nullable: Yes
- **`freq_phys_distress_pct_hotspot_conf`** (string, nullable): Hot spot confidence for distress
  - Values: Same as above
  - Nullable: Yes

### Control Variables
- **`rucc`** (integer, nullable): Rural-Urban Continuum Code
  - Values: 1-9 (1=Metro >1M, 2=Metro 250k-1M, 3=Metro <250k, 4=Micropolitan adjacent, 5=Micropolitan non-adjacent, 6=Small town adjacent, 7=Small town non-adjacent, 8=Rural adjacent, 9=Rural non-adjacent)
  - Nullable: Yes
- **`rural`** (integer, nullable): Binary rural indicator
  - Values: 0 (urban/metro), 1 (rural)
  - Nullable: Yes
- **`rucc_category`** (string, nullable): Categorical RUCC grouping
  - Values: `"Metro"`, `"Micropolitan"`, `"Rural"`
  - Nullable: Yes

## Data Quality Notes

1. **Missing Data**: Many counties have null values for:
   - CDC PLACES metrics (suppressed for small counties)
   - Overdose rates (suppressed for small counts)
   - ESDA results (if county was excluded from analysis)

2. **Null Handling**: The frontend should:
   - Display "Data suppressed" for null values in info cards
   - Use neutral colors (gray) for null counties on maps
   - Skip null counties in quantile calculations

3. **Categorical Values**: ESDA cluster fields use exact string matching. Ensure:
   - Case-sensitive matching (`"HH"` not `"hh"`)
   - Default fallback for unexpected values

## Validation Checklist

Before deploying, verify:
- [ ] All required identifier fields present (`fips`, `NAME`)
- [ ] At least one electoral variable present (`trump_share_2016`)
- [ ] At least one distress metric present (`freq_phys_distress_pct` or `od_1316_rate`)
- [ ] ESDA fields present if using bivariate/hotspot visualizations (`bv_cluster`, `*_hotspot_conf`)
- [ ] Geometry is valid GeoJSON (EPSG:4326)
- [ ] File size reasonable (< 50 MB for web performance)

## Example Feature

```json
{
  "type": "Feature",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[...]]
  },
  "properties": {
    "fips": "01001",
    "NAME": "Autauga County",
    "trump_share_2016": 65.2,
    "trump_share_2020": 68.1,
    "trump_shift_16_20": 2.9,
    "freq_phys_distress_pct": 14.3,
    "od_1316_rate": 18.5,
    "bv_cluster": "HH",
    "trump_share_2016_lisa_cluster": "HH",
    "trump_share_2016_hotspot_conf": "Hot Spot - 95% Conf",
    "rucc": 3,
    "rural": 0
  }
}
```

