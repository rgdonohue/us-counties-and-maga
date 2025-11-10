# Developer Notes

## Workflow Spine

1. **Check data inventory**  
   ```bash
   python scripts/run_pipeline.py catalog
   ```
   The command prints a JSON status table; ⚠️ rows signal missing assets.

2. **Build the analysis dataset**  
   ```bash
   # Synthetic smoke test
   python scripts/run_pipeline.py build-data --sample
   # Full rebuild (requires all raw files)
   python scripts/run_pipeline.py build-data
   ```
   The builder writes `data/processed/counties_analysis.geojson` and mirrors the export under `web/assets/`.

3. **Run tests**  
   ```bash
   python -m pytest
   ```
   Add assertions for every new transform or model; the synthetic dataset makes it cheap to cover new code paths.

4. **Launch notebooks** (optional)  
   Point notebooks to the GeoJSON produced above. Avoid duplicating ETL logic inside notebooks—call into `pain_politics.pipeline` wherever possible.

## Paths & Configuration

- `pain_politics.config.ProjectPaths` centralizes directory resolution. Use it instead of hard-coded relative paths inside new modules.
- Override the project root by setting `PNP_PROJECT_ROOT=/path/to/root` in your environment (handy for debugging outside the repo).
- The pipeline ensures directories exist before writing, so scripts can assume `data/processed/` etc. are available.
- Source documentation (PDF codebooks + data dictionaries) for County Health Rankings lives in `docs/data_sources/county_health_rankings/`; keep new vintages there so analysts can trace provenance.

- Quick QA summaries: `python scripts/qa_chr_metrics.py` compares 2016 vs 2024 County Health Rankings metrics (drug overdoses, poor health days) and reports distribution deltas.

## Spatial Modeling Sandbox

- `pain_politics.models.SpatialRegressionSuite` wraps OLS, spatial lag, and spatial error estimators.  
  Example:
  ```python
  from pain_politics.models import SpatialRegressionSuite

  suite = SpatialRegressionSuite(
      gdf,
      dependent="trump_share_2016",
      predictors=["freq_phys_distress_pct", "od_1316_rate", "ba_plus_pct"],
  )
  suite.fit()
  coef_df = suite.to_dataframe()
  ```
- Extend the class with additional diagnostics (Moran's I on residuals, LM tests) as the analysis matures.

## Front-End Data Contract

- `web/src/main.js` expects the GeoJSON to expose:
  - `trump_share_2016`, `trump_share_2020`, `trump_shift_16_20`
  - `od_1316_rate`, `od_1720_rate`, `od_rate_change`
  - `freq_phys_distress_pct`, `arthritis_pct`, `distress_trump_zscore`
  - Spatial artifacts (`*_lisa_cluster`, `*_hotspot_conf`) once populated
- Keep column names stable; any rename must be reflected in both the web code and `docs/METHODOLOGY.md`.

## Housekeeping

- Run `black` + `pylint` periodically (pinned in `requirements.txt`).
- Commit large raw data files to external storage; keep `data/raw/` paths consistent with the catalog.
- Update `README.md` and `docs/METHODOLOGY.md` whenever the pipeline contract changes.
