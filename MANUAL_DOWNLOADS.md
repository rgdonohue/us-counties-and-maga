# Manual Data Downloads - Quick Reference

## Status: 5/10 datasets complete ✅

### 📥 REQUIRED MANUAL DOWNLOADS (5 remaining)

#### 1. Election Data (2 files)
**MIT Election Lab:** https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/VOQCHQ

Download and save as:
- `data/raw/elections/county_presidential_2016.csv`
- `data/raw/elections/county_presidential_2020.csv`

---

#### 2. Overdose Data (2 files)
**CDC WONDER:** https://wonder.cdc.gov/mcd-icd10.html

Query for ICD-10 codes: `X40-X44, X60-X64, X85, Y10-Y14`

Save as:
- `data/raw/cdc_wonder/overdose_2013_2016.txt`
- `data/raw/cdc_wonder/overdose_2017_2020.txt`

---

#### 3. Rural-Urban Codes (1 file)
**USDA ERS:** https://www.ers.usda.gov/data-products/rural-urban-continuum-codes/

Save as:
- `data/raw/usda/rucc_2023.xlsx`

---

## 📋 After Downloading

Check status:
```bash
source .venv/bin/activate
python scripts/download_data.py --check  # or run the status check from catalog
```

Run full pipeline:
```bash
python scripts/run_pipeline.py build-data
```

Expected output: `data/processed/counties_analysis.geojson` with ~3,100 counties

---

**See `docs/DATA_DOWNLOAD_GUIDE.md` for detailed instructions.**

