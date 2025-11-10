#!/usr/bin/env python
"""
Download automated data sources for the county analysis pipeline.

This script fetches:
1. Census TIGER/Line county boundaries (2023)
2. CDC PLACES county health data (2023)
3. USDA Rural-Urban Continuum Codes (2023)
"""

import sys
from pathlib import Path
import urllib.request
import zipfile
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pain_politics.config import paths
from pain_politics.utils import get_logger

logger = get_logger(__name__)


def download_file(url: str, dest: Path, desc: str) -> None:
    """Download a file with progress indication."""
    logger.info(f"Downloading {desc}...")
    logger.info(f"  URL: {url}")
    logger.info(f"  Destination: {dest}")
    
    dest.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        urllib.request.urlretrieve(url, dest)
        logger.info(f"✅ Downloaded {desc} ({dest.stat().st_size / 1024 / 1024:.1f} MB)")
    except Exception as e:
        logger.error(f"❌ Failed to download {desc}: {e}")
        raise


def download_tiger_counties() -> None:
    """Download Census TIGER/Line county boundaries."""
    url = "https://www2.census.gov/geo/tiger/TIGER2023/COUNTY/tl_2023_us_county.zip"
    zip_path = paths.data_raw / "shapefiles" / "tl_2023_us_county.zip"
    extract_dir = paths.data_raw / "shapefiles"
    
    download_file(url, zip_path, "TIGER/Line Counties 2023")
    
    logger.info("Extracting shapefile...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    # Clean up zip file
    zip_path.unlink()
    logger.info("✅ Extracted county boundaries")


def download_cdc_places() -> None:
    """Download CDC PLACES county data."""
    # CDC PLACES 2023 county-level data
    url = "https://chronicdata.cdc.gov/api/views/swc5-untb/rows.csv?accessType=DOWNLOAD"
    dest = paths.data_raw / "cdc_places" / "places_county_2023.csv"
    
    download_file(url, dest, "CDC PLACES County Data 2023")


def download_usda_rucc() -> None:
    """Download USDA Rural-Urban Continuum Codes."""
    # Updated link for 2023 RUCC data
    url = "https://www.ers.usda.gov/webdocs/DataFiles/53251/ruralurbancodes2023.xlsx"
    dest = paths.data_raw / "usda" / "rucc_2023.xlsx"
    
    download_file(url, dest, "USDA Rural-Urban Continuum Codes 2023")


def create_acs_variables_manifest() -> None:
    """Create a basic ACS variables manifest for API queries."""
    import json
    
    # Common ACS variables for socioeconomic analysis
    acs_vars = {
        "variables": [
            {"code": "B01003_001E", "label": "Total Population", "concept": "Total Population"},
            {"code": "B19013_001E", "label": "Median Household Income", "concept": "Median Household Income in the Past 12 Months"},
            {"code": "B17001_002E", "label": "Income Below Poverty Level", "concept": "Poverty Status in the Past 12 Months"},
            {"code": "B23025_005E", "label": "Unemployed", "concept": "Employment Status"},
            {"code": "B15003_017E", "label": "High School Graduate", "concept": "Educational Attainment"},
            {"code": "B15003_022E", "label": "Bachelor's Degree", "concept": "Educational Attainment"},
            {"code": "B27001_001E", "label": "Total Health Insurance Coverage Universe", "concept": "Health Insurance Coverage Status"},
        ],
        "year": 2022,
        "dataset": "acs5",
        "geography": "county:*"
    }
    
    dest = paths.data_raw / "census" / "acs_variables.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    
    with open(dest, 'w') as f:
        json.dump(acs_vars, f, indent=2)
    
    logger.info("✅ Created ACS variables manifest")


def main():
    """Download all automated data sources."""
    logger.info("=" * 70)
    logger.info("Downloading automated data sources")
    logger.info("=" * 70)
    
    try:
        # Create directories
        logger.info("Creating data directories...")
        (paths.data_raw / "shapefiles").mkdir(parents=True, exist_ok=True)
        (paths.data_raw / "cdc_places").mkdir(parents=True, exist_ok=True)
        (paths.data_raw / "usda").mkdir(parents=True, exist_ok=True)
        (paths.data_raw / "census").mkdir(parents=True, exist_ok=True)
        
        # Download automated sources
        download_tiger_counties()
        download_cdc_places()
        download_usda_rucc()
        create_acs_variables_manifest()
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("✅ All automated data sources downloaded successfully!")
        logger.info("=" * 70)
        logger.info("")
        logger.info("NEXT STEPS - Manual data downloads:")
        logger.info("")
        logger.info("1. MIT Election Lab - Presidential Election Returns:")
        logger.info("   2016: https://dataverse.harvard.edu/file.xhtml?fileId=4819117")
        logger.info("   2020: https://dataverse.harvard.edu/file.xhtml?fileId=4819088")
        logger.info("   → Save as: data/raw/elections/county_presidential_2016.csv")
        logger.info("   → Save as: data/raw/elections/county_presidential_2020.csv")
        logger.info("")
        logger.info("2. CDC WONDER - Drug Overdose Deaths:")
        logger.info("   Visit: https://wonder.cdc.gov/mcd-icd10.html")
        logger.info("   - Query 2013-2016 overdose deaths by county (ICD-10 codes X40-X44, X60-X64, X85, Y10-Y14)")
        logger.info("   - Query 2017-2020 overdose deaths by county")
        logger.info("   - Export as tab-delimited text files")
        logger.info("   → Save as: data/raw/cdc_wonder/overdose_2013_2016.txt")
        logger.info("   → Save as: data/raw/cdc_wonder/overdose_2017_2020.txt")
        logger.info("")
        logger.info("After downloading manual files, run:")
        logger.info("  python scripts/run_pipeline.py build-data")
        logger.info("")
        
    except Exception as e:
        logger.error(f"❌ Error downloading data: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

