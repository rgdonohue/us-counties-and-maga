# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a spatial analysis project examining the relationship between community distress metrics (overdose mortality, physical pain, life expectancy) and Trump vote share in 2016/2020 at the county level. The repository contains a production-ready Python package (`pain_politics`), a CLI, and an interactive web visualization.

## Development Commands

### Python Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Core Pipeline Commands
```bash
# View data catalog status (shows which raw datasets are present/missing)
python scripts/run_pipeline.py catalog

# Build analysis dataset using synthetic sample data
python scripts/run_pipeline.py build-data --sample

# Build with real data (once raw assets are downloaded)
python scripts/run_pipeline.py build-data

# Optional: specify custom output path
python scripts/run_pipeline.py build-data --output path/to/output.geojson
```

### Testing
```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_pipeline.py

# Run with verbose output
python -m pytest -v

# Run tests matching a pattern
python -m pytest -k "test_distress"
```

### Data QA Scripts
```bash
# Quick distribution check on County Health Rankings metrics
python scripts/qa_chr_metrics.py

# Download automated data sources
python scripts/download_data.py
```

### Web Visualization
```bash
cd web
npm install
npm run dev        # Development server at http://localhost:5173
npm run build      # Production bundle
npm run preview    # Preview production build

# Generate PMTiles (requires tippecanoe & pmtiles binaries installed)
npm run tiles
```

## Architecture Overview

### Package Structure (`src/pain_politics/`)

The package follows a data science project structure with clear separation of concerns:

- **`data/`**: Data catalog and loaders
  - `catalog.py`: Centralized inventory of required raw assets with acquisition metadata
  - `loaders.py`: Functions to load each raw dataset (elections, CDC WONDER, CHR, etc.)
  - `validators.py`: Data validation utilities

- **`features/`**: Feature engineering
  - `pain_metrics.py`: Computes derived distress metrics (Trump shift, overdose change, composite z-scores)
  - `spatial.py`: Spatial weights and lag calculations using PySAL

- **`models/`**: Statistical modeling
  - `spatial_regression.py`: `SpatialRegressionSuite` class wraps OLS, spatial lag, and spatial error models

- **`pipeline/`**: High-level orchestration
  - `build.py`: `build_analysis_dataset()` main entrypoint - merges all data sources, computes features, exports GeoJSON
  - `sample_data.py`: Generates synthetic county data for testing without real downloads

- **`config.py`**: `ProjectPaths` dataclass defines all directory paths (data/raw, data/processed, reports, etc.)

- **`cli.py`**: Command-line interface with `catalog` and `build-data` subcommands

### Data Pipeline Flow

1. **Data Catalog Check**: `DataCatalog` validates which raw assets exist
2. **Load & Merge**: Each loader returns a DataFrame with `fips` column; all are left-joined to county boundaries
3. **Feature Engineering**: `compute_distress_metrics()` adds derived columns (Trump shift, overdose change, composite metrics)
4. **Spatial Processing**: Converted to EPSG:4326, spatial weights computed as needed
5. **Export**: GeoJSON written to `data/processed/counties_analysis.geojson` and `web/assets/`

### Key Design Patterns

**Fallback to Sample Data**: If raw assets are missing, `build_analysis_dataset()` automatically falls back to synthetic data (100 counties with plausible distributions) so the entire pipeline can be exercised.

**Monkeypatch for Testing**: Tests use a `project_paths_tmp` fixture that monkeypatches the global `paths` object in `config`, `catalog`, and `loaders` modules to use isolated temp directories.

**County Health Rankings Integration**: The pipeline loads both 2016 and 2024 CHR releases and computes change columns for drug overdoses and poor health days (e.g., `chr_drug_overdose_change_16_24`).

**Spatial Weights**: `build_spatial_weights()` in `features/spatial.py` constructs PySAL weights (queen/rook/knn) with proper handling of islands and standardization.

**FIPS as Primary Key**: All datasets use 5-digit FIPS codes (`fips` column) for merging. County boundaries are filtered to exclude AK, HI, and territories (state FIPS 02, 15, 60, 66, 69, 72, 78).

## Data Sources & Manual Downloads

Several datasets require manual download. See `MANUAL_DOWNLOADS.md` for detailed instructions:

- **MIT Election Lab**: County presidential returns 2016/2020 (Dataverse)
- **CDC WONDER**: Overdose mortality 2013-2016, 2017-2020 (manual export as tab-delimited)
- **County Health Rankings**: 2016 and 2024 analytic CSVs (download from CHR&R website)

Automated downloads include Census TIGER/Line shapefiles, CDC PLACES, and USDA RUCC.

## Notebooks

Notebooks are narrative-driven and call into the `pain_politics` package rather than duplicating logic:

- `01_data_acquisition.ipynb`: Guided download/API scripts
- `02_data_processing.ipynb`: Calls `build_analysis_dataset()`, runs QA checks
- `03_esda_spatial_analysis.ipynb`: Moran's I, LISA, hot-spot analysis
- `04_spatial_models.ipynb`: Uses `SpatialRegressionSuite` to fit OLS, lag, error models
- `05_export_for_web.ipynb`: Simplifies geometry, exports GeoJSON/PMTiles for MapLibre

## Web Frontend

Built with Vite, MapLibre GL, D3, and Scrollama. Main entry point is `web/src/main.js`. The app expects `web/assets/counties_analysis.geojson` (or PMTiles equivalent) generated by the Python pipeline.

## Common Pitfalls

- **State FIPS Filtering**: County boundaries are filtered to exclude AK, HI, territories. If adding new data sources, ensure they also exclude these.
- **Column Name Consistency**: All loaders must return a `fips` column for merging. Check loader output carefully.
- **Missing Data Handling**: The pipeline uses left joins, so missing values are expected. `dropna` is deferred to modeling stage, not during merge.
- **Spatial Weights on Subsets**: When fitting spatial models, remember to build weights on the modeling subset (after dropping NAs), not the full GeoDataFrame.
- **CHR Column Names**: County Health Rankings columns follow the pattern `chr_{metric}_raw_value` in the raw CSV but are renamed during loading.

## Configuration

The global `paths` object in `pain_politics.config` provides all directory paths. Tests monkeypatch this to use temp directories. The `ProjectPaths.ensure()` method creates all required directories.

## Python Version

Requires Python 3.11+ (specified in `setup.py`).
