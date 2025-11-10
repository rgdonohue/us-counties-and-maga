# Data Download Instructions

## Quick Status Check
Run this to see what's missing:
```bash
source .venv/bin/activate
python scripts/run_pipeline.py catalog
```

---

## Missing Files (3 sources, 5 files total)

### 1. 🗳️ MIT Election Lab - County Presidential Returns (2 files)

**Dataset:** County Presidential Election Returns 2000-2020  
**URL:** https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/VOQCHQ

**Direct download links:**
- Full dataset: https://dataverse.harvard.edu/api/access/datafile/4819117

**Steps:**
1. Click the link above or visit the dataset page
2. Download the CSV file (named `countypres_2000-2020.csv` or similar)
3. The file contains data for all years 2000-2020
4. You can either:
   - **Option A:** Save the full file and filter it later, OR
   - **Option B:** Open in Excel/pandas and create two files:
     - Filter for `year == 2016` → save as `data/raw/elections/county_presidential_2016.csv`
     - Filter for `year == 2020` → save as `data/raw/elections/county_presidential_2020.csv`

**Required columns:**
- `year`, `state`, `state_po`, `county_name`, `county_fips`
- `candidate`, `party`, `candidatevotes`, `totalvotes`

**File size:** ~50 MB (full dataset)

**Save locations:**
```
data/raw/elections/county_presidential_2016.csv
data/raw/elections/county_presidential_2020.csv
```

---

### 2. 💊 CDC WONDER - Drug Overdose Mortality Data (2 files)

**System:** CDC WONDER Multiple Cause of Death Database  
**URL:** https://wonder.cdc.gov/mcd-icd10.html

**ICD-10 Codes for Drug Overdose:**
- X40-X44: Accidental poisoning
- X60-X64: Intentional self-poisoning
- X85: Assault by drugs
- Y10-Y14: Poisoning of undetermined intent

#### File 1: Overdose Deaths 2013-2016

**Steps:**
1. Go to https://wonder.cdc.gov/mcd-icd10.html
2. Click "I Agree" to the data use terms
3. **Section 1 - Organize table layout:**
   - Group Results By: Select "County" (and optionally "Year")
4. **Section 2 - Select location:**
   - Select: All states or specific states
5. **Section 3 - Select demographics:**
   - Leave defaults or select "All" for each category
6. **Section 4 - Select year and month:**
   - Check: 2013, 2014, 2015, 2016
7. **Section 5 - Place of death:**
   - Leave defaults
8. **Section 6 - Select cause of death:**
   - Under "ICD-10 Codes", enter: `X40, X41, X42, X43, X44, X60, X61, X62, X63, X64, X85, Y10, Y11, Y12, Y13, Y14`
9. Click "Send" button at bottom
10. On results page, click "Export" → "Export Results"
11. Save as: `data/raw/cdc_wonder/overdose_2013_2016.txt`

**Expected format:** Tab-delimited text file

**Expected columns:**
- `County`, `County Code`, `Deaths`, `Population`, `Crude Rate`
- Note: Some counties may be suppressed (shown as "Suppressed") if deaths < 10

#### File 2: Overdose Deaths 2017-2020

**Repeat the exact same process as above, but:**
- In Section 4, select years: 2017, 2018, 2019, 2020
- Save as: `data/raw/cdc_wonder/overdose_2017_2020.txt`

**Save locations:**
```
data/raw/cdc_wonder/overdose_2013_2016.txt
data/raw/cdc_wonder/overdose_2017_2020.txt
```

**Tips:**
- The query interface can time out with large requests
- If it fails, try:
  - Querying one state at a time and combining results
  - Splitting into smaller year ranges
  - Using the "More Options" to set population thresholds
- Data suppression (< 10 deaths) is normal and the pipeline handles it

**File size:** ~5-10 MB each

---

### 3. 🏘️ USDA - Rural-Urban Continuum Codes 2023 (1 file)

**Source:** USDA Economic Research Service (ERS)  
**URL:** https://www.ers.usda.gov/data-products/rural-urban-continuum-codes/

**Steps:**
1. Visit https://www.ers.usda.gov/data-products/rural-urban-continuum-codes/
2. Scroll down to find the "Download the Data" section
3. Look for "2023 Rural-Urban Continuum Codes" 
4. Download the Excel file (.xlsx)
5. Save as: `data/raw/usda/rucc_2023.xlsx`

**Alternative approach if direct download isn't visible:**
1. Click on the "Documentation" link on that page
2. Look for downloadable files or tables
3. The file should contain FIPS codes and RUCC classifications (1-9 scale)

**Expected columns:**
- `FIPS` or `FIPS Code` (5-digit county code)
- `State`
- `County_Name` or `County Name`
- `RUCC_2023` or `RUCC 2023` (values 1-9)
- `Population_2020` or similar

**RUCC Scale (1-9):**
- 1 = Metro areas with 1M+ population
- 2 = Metro areas 250K-1M
- 3 = Metro areas <250K
- 4-6 = Urban areas with varying metro adjacency
- 7-9 = Rural areas with varying metro adjacency

**Save location:**
```
data/raw/usda/rucc_2023.xlsx
```

**File size:** < 1 MB

**Note:** If you can't find 2023, the 2013 version may still be on the site and would work as a fallback, though 2023 is preferred.

---

## After Downloading All Files

### 1. Verify the files are in place:
```bash
cd /Users/richard/Documents/projects/us-counties-and-trump
source .venv/bin/activate
python scripts/run_pipeline.py catalog
```

You should see all items with ✅ (green check marks).

### 2. Build the full dataset:
```bash
python scripts/run_pipeline.py build-data
```

This will create:
- `data/processed/counties_analysis.geojson` (~3,100 US counties with all metrics)

### 3. Expected output:
The final GeoJSON will include:
- **Geometry:** County boundaries (polygons)
- **Election results:** 2016, 2020, (and 2024 if available)
- **Health metrics:** From County Health Rankings (2016 & 2024)
- **Overdose rates:** Drug mortality rates from CDC WONDER
- **Rural-urban classification:** USDA RUCC codes
- **CDC PLACES:** Health indicators (obesity, smoking, etc.)
- **Demographics:** Population, income, education (from ACS)

---

## Troubleshooting

### MIT Election Lab
- If the direct download fails, you may need to create a free Dataverse account
- The file is large (~50MB) and may take a few minutes to download
- You can download once and split into 2016/2020 files locally

### CDC WONDER
- **Query timeouts:** Try smaller geographic regions or year ranges
- **Data suppression:** Counties with <10 deaths show "Suppressed" - this is normal
- **Missing counties:** Some rural counties may have no data - pipeline handles this
- **Export format:** Make sure to select "Export Results" not "Print"

### USDA RUCC
- **404 errors:** The USDA occasionally changes URLs
- **Alternative:** Google search for "USDA Rural Urban Continuum Codes 2023" and find the most recent ERS page
- **Fallback:** If 2023 isn't available, 2013 data can be used temporarily

---

## Need Help?

If you encounter issues:
1. Check that directories exist: `data/raw/elections/`, `data/raw/cdc_wonder/`, `data/raw/usda/`
2. Verify file permissions (files should be readable)
3. Check file formats (CSV/TXT should be plain text, not HTML error pages)
4. Run `python scripts/run_pipeline.py catalog` to see specific missing files

---

## Quick Command Reference

```bash
# Activate environment
source .venv/bin/activate

# Check data status
python scripts/run_pipeline.py catalog

# Build full dataset
python scripts/run_pipeline.py build-data

# Check build status
ls -lh data/processed/counties_analysis.geojson
```

---

**Last updated:** November 9, 2025

