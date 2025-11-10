# Quick Start: Download Missing Data

## Current Status: 5/10 Complete ✅

Good news: **County Health Rankings (2016 & 2024) already present!** ✅

---

## 🎯 What You Need to Download (3 sources, 5 files)

### 1️⃣ MIT Election Lab (ONE download, creates 2 files)

**Step 1:** Download the full dataset  
🔗 https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/VOQCHQ

- Click "Access Dataset" → Download
- File: `countypres_2000-2020.csv` (~50 MB)
- Save to: `data/raw/elections/`

**Step 2:** Run the splitter script  
```bash
cd /Users/richard/Documents/projects/us-counties-and-trump
source .venv/bin/activate
python scripts/split_election_data.py
```

This creates:
- ✅ `county_presidential_2016.csv`
- ✅ `county_presidential_2020.csv`

---

### 2️⃣ CDC WONDER Overdose Data (2 files - requires web form)

🔗 https://wonder.cdc.gov/mcd-icd10.html

**For EACH file (2013-2016 and 2017-2020):**

1. Click "I Agree"
2. **Group by:** County
3. **Years:** Select 2013-2016 (first file) OR 2017-2020 (second file)
4. **ICD-10 Codes:** Enter these codes in Section 6:
   ```
   X40, X41, X42, X43, X44, X60, X61, X62, X63, X64, X85, Y10, Y11, Y12, Y13, Y14
   ```
5. Click "Send"
6. Click "Export" → "Export Results"
7. Save as:
   - First query: `data/raw/cdc_wonder/overdose_2013_2016.txt`
   - Second query: `data/raw/cdc_wonder/overdose_2017_2020.txt`

💡 **Tip:** If the query times out, try selecting one state at a time

---

### 3️⃣ USDA Rural-Urban Codes (1 file)

🔗 https://www.ers.usda.gov/data-products/rural-urban-continuum-codes/

1. Visit the link above
2. Find "Download the Data" or "Documentation" section
3. Download the 2023 Excel file
4. Save as: `data/raw/usda/rucc_2023.xlsx`

💡 **Note:** If the URL has changed, search for "USDA Rural Urban Continuum Codes 2023"

---

## ✅ Verify & Build

### Check status:
```bash
cd /Users/richard/Documents/projects/us-counties-and-trump
source .venv/bin/activate
python scripts/run_pipeline.py catalog
```

All items should show ✅

### Build the final dataset:
```bash
python scripts/run_pipeline.py build-data
```

Creates: `data/processed/counties_analysis.geojson` (~3,100 US counties)

---

## 📂 Final Directory Structure

```
data/raw/
├── analytic_data2016.csv                    ✅ (already have)
├── analytic_data2024.csv                    ✅ (already have)
├── elections/
│   ├── county_presidential_2016.csv         ⚠️  NEED THIS
│   └── county_presidential_2020.csv         ⚠️  NEED THIS
├── cdc_wonder/
│   ├── overdose_2013_2016.txt               ⚠️  NEED THIS
│   └── overdose_2017_2020.txt               ⚠️  NEED THIS
├── usda/
│   └── rucc_2023.xlsx                       ⚠️  NEED THIS
├── shapefiles/                              ✅ (already have)
├── cdc_places/                              ✅ (already have)
└── census/                                  ✅ (already have)
```

---

## 🆘 Need More Details?

See `DOWNLOAD_INSTRUCTIONS.md` for:
- Detailed step-by-step instructions
- Troubleshooting tips
- Expected column names and formats
- Alternative download methods

---

## 📋 Quick Command Reference

```bash
# Check what's missing
python scripts/run_pipeline.py catalog

# Split MIT election data (after downloading)
python scripts/split_election_data.py

# Build full dataset (after all downloads)
python scripts/run_pipeline.py build-data

# Check the result
ls -lh data/processed/counties_analysis.geojson
```

---

**Estimated time:** 30-45 minutes (most time spent on CDC WONDER queries)

