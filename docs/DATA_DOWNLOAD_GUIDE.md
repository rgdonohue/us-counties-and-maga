# Data Download Guide

This guide walks you through downloading all required data sources for the county analysis pipeline.

## ✅ Automated Downloads (COMPLETED)

The following data sources have been automatically downloaded:

- **✅ Census TIGER/Line County Boundaries (2023)**  
  Location: `data/raw/shapefiles/tl_2023_us_county.shp`
  
- **✅ CDC PLACES County Data (2023)**  
  Location: `data/raw/cdc_places/places_county_2023.csv`
  
- **✅ ACS Variables Manifest**  
  Location: `data/raw/census/acs_variables.json`

- **✅ County Health Rankings (2016 & 2024)**  
  Already present:
  - `data/raw/analytic_data2016.csv`
  - `data/raw/analytic_data2024.csv`

---

## 📥 Manual Downloads Required

### 1. MIT Election Lab - Presidential Election Returns

#### 2016 Presidential Election
- **URL:** https://dataverse.harvard.edu/file.xhtml?fileId=4819117
- **Alternative:** https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/VOQCHQ
- **File:** County Presidential Election Returns 2000-2020
- **Action:**
  1. Download the CSV file
  2. Filter for year 2016 (if full dataset)
  3. Save as: `data/raw/elections/county_presidential_2016.csv`

#### 2020 Presidential Election
- **URL:** https://dataverse.harvard.edu/file.xhtml?fileId=4819088
- **Alternative:** Same dataset as above
- **Action:**
  1. Download the CSV file
  2. Filter for year 2020 (if full dataset)
  3. Save as: `data/raw/elections/county_presidential_2020.csv`

**Expected columns:**
- `year`, `state`, `state_po`, `county_name`, `county_fips`
- `candidate`, `party`, `candidatevotes`, `totalvotes`

---

### 2. CDC WONDER - Drug Overdose Mortality Data

**Base URL:** https://wonder.cdc.gov/mcd-icd10.html

#### Overdose Deaths 2013-2016
**Query Parameters:**
- **Years:** 2013, 2014, 2015, 2016
- **Group By:** County (or County + Year)
- **ICD-10 Codes:** X40-X44 (accidental), X60-X64 (intentional self-harm), X85 (assault), Y10-Y14 (undetermined)
- **Drug/Alcohol Induced Causes:** All drug poisonings
- **Export Format:** Tab-delimited text

**Steps:**
1. Go to https://wonder.cdc.gov/mcd-icd10.html
2. Click "I Agree" to terms
3. **Section 1 (Organize table layout):**
   - Group Results By: County, Year (optional: add State for clarity)
4. **Section 2 (Select location):**
   - Select: All U.S. Counties (or specific states)
5. **Section 3 (Select demographics):**
   - Leave defaults or select specific age groups if needed
6. **Section 4 (Select year and month):**
   - Years: Check 2013, 2014, 2015, 2016
7. **Section 5 (Select weekday, autopsy, place of death):**
   - Leave defaults
8. **Section 6 (Select cause of death):**
   - ICD-10 Codes: Enter `X40,X41,X42,X43,X44,X60,X61,X62,X63,X64,X85,Y10,Y11,Y12,Y13,Y14`
9. Click "Send"
10. On results page, click "Export" → "Export Results"
11. Save as: `data/raw/cdc_wonder/overdose_2013_2016.txt`

#### Overdose Deaths 2017-2020
**Repeat the same process but for years 2017-2020**
- Save as: `data/raw/cdc_wonder/overdose_2017_2020.txt`

**Expected columns:**
- `County`, `County Code`, `Year`, `Deaths`, `Population`, `Crude Rate`

**Note:** CDC WONDER may suppress data for counties with <10 deaths. This is normal.

---

### 3. USDA Economic Research Service - Rural-Urban Continuum Codes

**URL:** https://www.ers.usda.gov/data-products/rural-urban-continuum-codes/

**Steps:**
1. Visit the URL above
2. Scroll to "Documentation" section
3. Find and download "Rural-Urban Continuum Codes (2023)"
4. Should be an Excel file (.xlsx)
5. Save as: `data/raw/usda/rucc_2023.xlsx`

**Alternative download:** https://www.ers.usda.gov/data-products/rural-urban-continuum-codes/documentation/

**Expected columns:**
- `FIPS`, `State`, `County_Name`
- `RUCC_2023` (1-9 scale: 1=metro areas with 1M+ pop, 9=rural <2,500 pop)
- `Population_2020`

---

## 🔍 Verification

After downloading all files, verify your data structure:

```bash
data/raw/
├── analytic_data2016.csv          ✅ (already present)
├── analytic_data2024.csv          ✅ (already present)
├── shapefiles/
│   ├── tl_2023_us_county.shp     ✅ (automated)
│   ├── tl_2023_us_county.shx     ✅ (automated)
│   ├── tl_2023_us_county.dbf     ✅ (automated)
│   └── tl_2023_us_county.prj     ✅ (automated)
├── elections/
│   ├── county_presidential_2016.csv  ⚠️  (manual - download needed)
│   └── county_presidential_2020.csv  ⚠️  (manual - download needed)
├── cdc_wonder/
│   ├── overdose_2013_2016.txt        ⚠️  (manual - download needed)
│   └── overdose_2017_2020.txt        ⚠️  (manual - download needed)
├── cdc_places/
│   └── places_county_2023.csv     ✅ (automated)
├── usda/
│   └── rucc_2023.xlsx             ⚠️  (manual - download needed)
└── census/
    └── acs_variables.json         ✅ (automated)
```

Check status programmatically:
```bash
source .venv/bin/activate
python -c "
from pain_politics.data.catalog import DataCatalog
catalog = DataCatalog()
catalog.log_summary()
"
```

---

## 🚀 Running the Pipeline

Once all data is downloaded:

```bash
source .venv/bin/activate
python scripts/run_pipeline.py build-data
```

This will generate:
- `data/processed/counties_analysis.geojson` (~3,100 US counties with all metrics)

The GeoJSON will include:
- Election results (2016, 2020, 2024)
- Health metrics from County Health Rankings
- Overdose mortality rates
- Rural-urban classification
- CDC PLACES health indicators
- Demographic data from ACS

---

## 💡 Tips

1. **MIT Election Lab:** The dataset covers 2000-2020, so download once and filter for both 2016 and 2020.

2. **CDC WONDER:** The query interface can be finicky. If it times out, try:
   - Selecting fewer years at once
   - Querying by state groups rather than all counties at once
   - Using the "More Options" to set reasonable population thresholds

3. **File sizes:**
   - Election data: ~50 MB
   - CDC WONDER: ~5-10 MB each
   - USDA RUCC: <1 MB

4. **Data suppression:** Some counties may have missing values due to privacy protection. The pipeline handles this gracefully.

---

## 📚 Data Sources & Citations

- **Census TIGER/Line:** U.S. Census Bureau (2023)
- **MIT Election Lab:** MIT Election Data and Science Lab (2020)
- **CDC WONDER:** Centers for Disease Control and Prevention, Multiple Cause of Death Files
- **County Health Rankings:** University of Wisconsin Population Health Institute
- **CDC PLACES:** Centers for Disease Control and Prevention, PLACES Project
- **USDA RUCC:** U.S. Department of Agriculture, Economic Research Service

