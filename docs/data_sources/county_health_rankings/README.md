# County Health Rankings Source Notes

- **Location**: raw CSVs (`analytic_data2016.csv`, `analytic_data2024.csv`) live in `data/raw/`; codebooks and data dictionaries are stored alongside this file.
- **Structure**: Every measure appears as a family of columns (raw value, numerator, denominator, confidence interval bounds, flags). Column names from the CSV are flattened to snake_case during ingestion so downstream merges can rely on consistent naming.
- **Key distress metrics** leveraged in this project:
  - `chr_freq_phys_distress_pct` → percentage of adults reporting ≥14 poor physical-health days per month (age-adjusted).
  - `chr_freq_mental_distress_pct` → percentage of adults with ≥14 poor mental-health days per month (age-adjusted).
  - `chr_drug_overdose_deaths_per_100k` → age-adjusted drug poisoning mortality rate.
  - `chr_suicides_per_100k` → age-adjusted suicide mortality rate.
  - `chr_life_expectancy_years` → average life expectancy at birth (overall and race-specific variants when available).
- **Flags**: Many measures include reliability flags (`*_flag`) and race-specific estimates (`*_race_*`). Suppressed or unreliable values should be handled before analysis; the loader converts unsupported values to `NaN` but retains the flag columns for QC.
- **Vintage**: The 2024 release provides the latest multiyear averages (e.g., BRFSS 2021/2022, CDC WONDER 2018–2022). Earlier releases (e.g., 2016) can be loaded for change-over-time analysis; mind the underlying data year differences noted in the analytic documentation.
