# Methodology Document

## Research Design

### Research Questions

1. **Primary**: How strongly are county-level pain/distress proxies associated with Trump vote share in 2016 and 2020, after adjusting for socioeconomic and demographic factors?

2. **Spatial**: Where are local clusters (LISA) of high pain–high Trump support versus mismatches?

3. **Modeling**: Do spatial models (lag/error) change inference compared to non-spatial OLS?

4. **Robustness**: Are relationships consistent across different pain proxies and time windows?

### Implementation Status (May 2024)

- Core ETL routines live in the `pain_politics` Python package; notebooks call those functions rather than owning logic.
- A CLI (`python scripts/run_pipeline.py`) provides two modes:
  - `build-data --sample` generates a deterministic synthetic dataset for prototyping.
  - `build-data` expects full raw assets and produces the master GeoJSON used by the web app.
- The automated test suite covers the synthetic pipeline, distress feature engineering, and catalog sanity checks. Extend tests as real data becomes available.

## Data Collection

### Unit of Analysis
- U.S. counties and county-equivalents (n ≈ 3,143)
- Current implementation filters out Alaska (STATEFP 02), Hawaii (STATEFP 15), and territories (STATEFP > 56)
- Note: Virginia independent cities and other county-equivalents are currently included (filtering refinement planned)

### Temporal Framework
- **Baseline Period**: 2010-2015 (for structural indicators)
- **Pre-2016 Election**: 2013-2016 (for pain metrics)
- **Pre-2020 Election**: 2017-2020 (for updated pain metrics)

### Data Catalog & Pipeline Integration
- `pain_politics.data.DataCatalog` enumerates every raw asset, its acquisition mode (automated/manual/API), and canonical file path.
- `python scripts/run_pipeline.py catalog` prints the status table; missing files trigger ⚠️ flags.
- `python scripts/run_pipeline.py build-data --sample` fabricates a reproducible five-county dataset for development; omit `--sample` once all raw assets are present to build the full GeoJSON consumed by notebooks and the web app.
- The pipeline writes both `data/processed/counties_analysis.geojson` and mirror exports in `web/assets/` to keep the interactive map in sync.
- County Health Rankings (CHR) analytic datasets (2016, 2024 vintages) live in `data/raw/`; documentation is archived under `docs/data_sources/county_health_rankings/`. During ingest we flatten verbose headers, retain reliability flags, and standardize key measures such as frequent physical distress, drug overdose deaths, suicides, and life expectancy.
- The pipeline derives simple 2016→2024 deltas for drug overdose mortality and poor physical/mental health days (`chr_*_change_16_24`) to highlight longer-run shifts alongside the latest levels.

### Variable Construction

#### Outcome Variables
- `trump_share_2016`: Two-party vote share for Trump in 2016
- `trump_share_2020`: Two-party vote share for Trump in 2020
- `trump_margin`: Republican minus Democratic vote share

#### Pain/Distress Proxies
1. **Mortality-based**:
   - Overdose mortality rate (age-adjusted per 100k)
   - Suicide rate (age-adjusted per 100k)
   - "Deaths of despair" composite

2. **Health status**:
   - Frequent physical distress (% adults with ≥14 poor physical health days/month)
   - Arthritis prevalence (% adults)
   - Depression prevalence (% adults)

3. **Healthcare utilization**:
   - Opioid dispensing rate (prescriptions per 100 persons)
   - Disability benefit recipiency rate

4. **Life expectancy**:
   - County life expectancy at birth (from County Health Rankings)
   - Note: Temporal change in life expectancy not yet implemented

#### Control Variables (Planned)
- **Demographic**: Age structure, race/ethnicity composition (ACS integration pending)
- **Socioeconomic**: Education (% BA+), median income, unemployment rate (ACS integration pending)
- **Geographic**: Rural-Urban Continuum Code (implemented), region fixed effects
- **Economic structure**: Manufacturing dependence, mining dependence (data sources TBD)

## Analytical Framework

### 1. Exploratory Data Analysis

#### Non-spatial exploration
- Univariate distributions by rurality
- Bivariate correlations (Pearson, Spearman)
- Partial correlations controlling for key confounders
- Missing data patterns and imputation strategy

#### Spatial exploration
- **Global spatial autocorrelation**:
  ```python
  Moran's I = (n/W) * (Σᵢ Σⱼ wᵢⱼ(xᵢ - x̄)(xⱼ - x̄)) / Σᵢ(xᵢ - x̄)²
  ```
  Where:
  - n = number of counties
  - W = sum of weights
  - wᵢⱼ = spatial weight between counties i and j
  - xᵢ = value for county i
  - x̄ = mean value

- **Local spatial autocorrelation (LISA)**:
  ```python
  Iᵢ = (xᵢ - x̄) * Σⱼ wᵢⱼ(xⱼ - x̄)
  ```
  Identifies four cluster types:
  - HH: High values surrounded by high values
  - LL: Low values surrounded by low values
  - HL: High values surrounded by low values (outliers)
  - LH: Low values surrounded by high values (outliers)

### 2. Spatial Weights Specification

#### Queen Contiguity (Primary)
- Counties sharing any boundary point
- Most inclusive definition
- Handles irregular boundaries well

#### Alternative Specifications (Robustness)
- Rook contiguity (shared edges only)
- k-Nearest Neighbors (k=8)
- Distance-based (threshold = 150km)

#### Weight Standardization
- Row-standardization (W-standardized)
- Each row sums to 1
- Interpretation: spatial lag as weighted average of neighbors

### 3. Statistical Modeling

#### Model Hierarchy

**M0: Baseline OLS**
```
Y = α + βX + γZ + ε
```
Where:
- Y = Trump vote share
- X = Pain proxy
- Z = Control variables
- ε = Error term

**M1: Spatial Lag Model (SLM)**
```
Y = ρWY + βX + γZ + ε
```
Where:
- ρ = Spatial autoregressive parameter
- WY = Spatially lagged dependent variable

**M2: Spatial Error Model (SEM)**
```
Y = βX + γZ + u
u = λWu + ε
```
Where:
- λ = Spatial error parameter
- Wu = Spatially lagged error term

#### Model Selection
1. Run OLS baseline
2. Calculate Lagrange Multiplier tests:
   - LM-Lag for spatial lag
   - LM-Error for spatial error
   - Robust versions of both
3. Select model based on test significance

#### Estimation
- Maximum Likelihood (ML) for spatial models
- Robust standard errors
- Spatial HAC standard errors for inference

### 4. Robustness Checks

#### Variable Sensitivity
- Rotate through different pain proxies
- Use principal components of multiple proxies
- Test with and without outliers

#### Spatial Sensitivity
- Alternative weight matrices
- Different neighbor definitions
- Spatial regimes (allow coefficients to vary by region)

#### Temporal Stability
- Compare 2016 vs 2020 results
- Test for structural breaks
- Analyze changes over time

### 5. Bivariate Spatial Analysis

#### Global Bivariate Moran's I
Tests whether high values of variable X cluster with high values of variable Y:
```python
I_xy = (n/W) * (Σᵢ Σⱼ wᵢⱼ(xᵢ - x̄)(yⱼ - ȳ)) / (σₓσᵧ)
```

#### Local Bivariate LISA
Identifies local patterns of association between two variables:
- HH: High X, High Y (e.g., high pain, high Trump)
- LL: Low X, Low Y
- HL: High X, Low Y
- LH: Low X, High Y

### 6. Hot Spot Analysis

#### Getis-Ord Gi*
Identifies statistically significant spatial clusters of high or low values:
```python
Gi* = (Σⱼ wᵢⱼxⱼ - X̄Σⱼ wᵢⱼ) / (S√[(nΣⱼ wᵢⱼ² - (Σⱼ wᵢⱼ)²)/(n-1)])
```

Where:
- Positive Gi* = Hot spot (cluster of high values)
- Negative Gi* = Cold spot (cluster of low values)
- Significance based on z-scores

## Preliminary Findings (November 2024)

> **Status**: These are exploratory findings from initial spatial analysis. Full model specifications, sensitivity analyses, and peer review are ongoing.

### Global Spatial Autocorrelation

Moran's I statistics reveal **strong positive spatial autocorrelation** across all key variables:

| Variable | Moran's I | p-value | Interpretation |
|----------|-----------|---------|----------------|
| Trump Support 2016 | 0.64 | < 0.001 | Very strong clustering |
| Physical Distress (%) | 0.65 | < 0.001 | Very strong clustering |
| Depression (%) | 0.51 | < 0.001 | Strong clustering |
| Arthritis (%) | 0.57 | < 0.001 | Strong clustering |
| Trump Support 2020 | 0.63 | < 0.001 | Very strong clustering |
| Trump Shift 2016→2020 | 0.43 | < 0.001 | Moderate clustering |

**Key takeaway**: Geographic clustering is highly significant for both health distress metrics and voting patterns. "Place matters"—neighboring counties exhibit similar characteristics far more than would be expected by chance alone.

### Local Spatial Patterns (LISA)

Local Indicators of Spatial Association identify distinct **regional clusters**:

#### High-High (HH) Clusters: High Distress + High Trump Support
- **Appalachian region**: Kentucky, West Virginia, eastern Tennessee
- **Rural South**: Parts of Arkansas, Mississippi, Alabama
- **Ozarks**: Southern Missouri, northern Arkansas
- **Industrial Midwest**: Pockets of Ohio, Indiana, Michigan

These regions show statistically significant co-location of:
- Elevated physical distress (≥14 poor health days/month)
- Higher Trump vote shares (2016 & 2020)
- Elevated depression and chronic conditions

#### Low-Low (LL) Clusters: Low Distress + Low Trump Support
- **Urban corridors**: Northeast megalopolis, West Coast metros
- **College towns**: Counties with major universities
- **High-income suburbs**: Around major metropolitan areas

#### Spatial Outliers (HL and LH)
- **HL (High distress, Low Trump)**: Some Native American counties, border regions
- **LH (Low distress, High Trump)**: Wealthy rural counties, agricultural Great Plains

### Bivariate Spatial Correlation

Bivariate Moran's I tests confirm **positive spatial association** between distress and Trump support:

- Physical distress × Trump 2016: I = 0.38, p < 0.001
- Depression × Trump 2016: I = 0.31, p < 0.001

The bivariate LISA maps reveal that HH clusters (high distress **and** high Trump support) are geographically concentrated in Appalachia and parts of the rural South, suggesting regional variation in the relationship.

### Heterogeneity Analysis

Preliminary stratified analyses suggest the distress→Trump relationship varies by context:

1. **By Rurality**: The association appears **stronger in rural and micropolitan counties** than in metropolitan areas, though formal tests are pending.

2. **By Population**: Electoral weight matters—relationships observed in small counties may not reflect voter behavior in large population centers.

### Important Caveats

1. **Ecological Fallacy**: These county-level patterns **do not** tell us about individual voters. A county can have high distress and high Trump support without the distressed individuals voting for Trump.

2. **Confounding**: We have not yet controlled for education, income, race, age structure, or other key demographic factors. The observed correlations may be spurious.

3. **Temporal Ambiguity**: Pain metrics from 2023 (CDC PLACES) are being correlated with 2016 elections. Temporal ordering is unclear.

4. **Missing Data**: CDC suppresses data for small counties, potentially biasing our sample toward larger, less rural counties.

5. **Multiple Comparisons**: With 3,100+ counties, some significant clusters are expected by chance. Current LISA analyses use p < 0.05 without multiple testing correction; FDR adjustment is planned for publication.

### Next Steps

Before publication, the following analyses are required:

- [ ] Full regression models with demographic/socioeconomic controls
- [ ] Spatial lag and spatial error models
- [ ] Sensitivity analyses with alternative weight matrices
- [ ] Temporal analyses comparing 2016 vs 2020 patterns
- [ ] Robustness checks with different pain proxies
- [ ] Formal tests of regional heterogeneity
- [ ] Peer review and external validation

## Visualization Strategy

### Map Types

1. **Choropleth Maps**
   - Quantile classification (5 classes)
   - Sequential color schemes for univariate
   - Diverging schemes for changes/residuals

2. **LISA Cluster Maps**
   - Categorical colors for cluster types
   - Significance filtering (p < 0.05)

3. **Bivariate Choropleth**
   - 3x3 grid color scheme
   - Shows two variables simultaneously

### Interactive Elements
- Hover tooltips with county details
- Click for detailed statistics
- Synchronized maps for comparison
- Time slider for temporal changes

### Statistical Graphics
- Moran scatterplots
- Coefficient plots with confidence intervals
- Partial regression plots
- Residual maps

## Limitations & Caveats

### Methodological Limitations

1. **Ecological Inference**
   - Cannot infer individual behavior from county aggregates
   - Simpson's paradox possible

2. **Modifiable Areal Unit Problem (MAUP)**
   - Results may change with different geographic units
   - County boundaries are arbitrary

3. **Spatial Dependence**
   - Violates independence assumption
   - Requires spatial models

### Data Limitations

1. **Measurement Error**
   - CDC PLACES uses model-based estimates
   - Small counties have higher uncertainty

2. **Temporal Misalignment**
   - Pain metrics and elections at different times
   - Lag between exposure and outcome

3. **Missing Data**
   - CDC suppresses data for small counts
   - Rural counties more affected

4. **Prototype Sample Dataset**
   - The bundled synthetic counties are meant for smoke testing only.
   - Do not report findings based on the sample; always rebuild with real raw inputs before publishing.

### Interpretive Cautions

1. **Correlation ≠ Causation**
   - Many confounders unmeasured
   - Reverse causation possible

2. **Multiple Testing**
   - Many counties tested simultaneously
   - FDR correction planned but not yet implemented

3. **Effect Heterogeneity**
   - Relationships may vary by region
   - Average effects mask variation

## Ethical Considerations

### Do's
- Present uncertainty and confidence intervals
- Acknowledge all limitations prominently
- Focus on structural/place-based factors
- Use neutral, scientific language

### Don'ts
- Make individual-level inferences
- Pathologize communities or voters
- Claim causal relationships
- Ignore contradictory evidence

## Reproducibility

### Code Practices
- Version control with Git
- Documented functions
- Unit tests for key operations
- Seed setting for randomization

### Data Management
- Raw data preserved unchanged
- Processing steps documented
- Intermediate outputs saved
- Final data versioned

### Environment
- Conda environment file provided
- Package versions pinned
- Platform specifications noted
- Hardware requirements documented

## References

### Methodological References
1. Anselin, L. (1995). "Local indicators of spatial association—LISA"
2. Getis, A. & Ord, J.K. (1992). "The analysis of spatial association"
3. LeSage, J. & Pace, R.K. (2009). "Introduction to Spatial Econometrics"

### Substantive References
1. Case, A. & Deaton, A. (2015). "Rising morbidity and mortality in midlife"
2. Monnat, S.M. (2016). "Deaths of despair and support for Trump"
3. Goodwin, J.S. et al. (2021). "County-level correlates of US election outcomes"

### Software References
- PySAL: Rey, S.J. & Anselin, L. (2007)
- GeoPandas: Jordahl, K. et al. (2020)
- MapLibre GL JS: MapLibre Contributors (2023)
