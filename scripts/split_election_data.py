#!/usr/bin/env python
"""
Helper script to split the MIT Election Lab dataset into separate 2016/2020 files.

After downloading the full countypres_2000-2020.csv file from:
https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/VOQCHQ

Place it in data/raw/elections/ and run this script to split it.
"""

import sys
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pain_politics.config import paths
from pain_politics.utils import get_logger

logger = get_logger(__name__)


def split_election_data(input_file: Path = None):
    """Split the full election dataset into 2016 and 2020 files."""
    
    # Look for the input file
    if input_file is None:
        possible_names = [
            'countypres_2000-2020.csv',
            'county_presidential_2000_2020.csv',
            'countypres_2016_2020.csv',
        ]
        
        elections_dir = paths.data_raw / 'elections'
        elections_dir.mkdir(parents=True, exist_ok=True)
        
        for name in possible_names:
            candidate = elections_dir / name
            if candidate.exists():
                input_file = candidate
                break
        
        if input_file is None:
            # List all CSV files in directory
            csv_files = list(elections_dir.glob('*.csv'))
            if csv_files:
                logger.info(f"Found CSV files in {elections_dir}:")
                for f in csv_files:
                    logger.info(f"  - {f.name}")
                logger.info("")
                logger.info("If one of these is the MIT Election Lab file, rename it or provide the path:")
                logger.info(f"  python scripts/split_election_data.py <filename>")
                return 1
            else:
                logger.error(f"❌ No election data file found in {elections_dir}")
                logger.info("")
                logger.info("Please download from:")
                logger.info("  https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/VOQCHQ")
                logger.info("")
                logger.info("Save it as: data/raw/elections/countypres_2000-2020.csv")
                logger.info("Then run this script again.")
                return 1
    
    logger.info(f"Reading election data from: {input_file}")
    
    try:
        df = pd.read_csv(input_file)
        logger.info(f"  Loaded {len(df):,} rows")
        logger.info(f"  Years available: {sorted(df['year'].unique())}")
        
        # Check for required columns
        required_cols = ['year', 'state', 'county_name', 'county_fips', 'candidate', 'party', 'candidatevotes', 'totalvotes']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.warning(f"⚠️  Missing expected columns: {missing_cols}")
            logger.info(f"  Available columns: {list(df.columns)}")
        
        # Split by year
        df_2016 = df[df['year'] == 2016].copy()
        df_2020 = df[df['year'] == 2020].copy()
        
        if len(df_2016) == 0:
            logger.error("❌ No data found for year 2016")
            return 1
        
        if len(df_2020) == 0:
            logger.error("❌ No data found for year 2020")
            return 1
        
        # Save files
        file_2016 = paths.data_raw / 'elections' / 'county_presidential_2016.csv'
        file_2020 = paths.data_raw / 'elections' / 'county_presidential_2020.csv'
        
        df_2016.to_csv(file_2016, index=False)
        df_2020.to_csv(file_2020, index=False)
        
        logger.info("")
        logger.info("✅ Successfully split election data:")
        logger.info(f"  2016: {len(df_2016):,} rows → {file_2016}")
        logger.info(f"  2020: {len(df_2020):,} rows → {file_2020}")
        logger.info("")
        
        # Optionally delete the original file
        if input_file.name.startswith('countypres_2000'):
            logger.info(f"You can now delete the original file: {input_file}")
            logger.info("  (The 2016 and 2020 files have been extracted)")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error processing file: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main entry point."""
    input_file = None
    
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
        if not input_file.exists():
            # Try relative to elections directory
            input_file = paths.data_raw / 'elections' / sys.argv[1]
            if not input_file.exists():
                logger.error(f"❌ File not found: {sys.argv[1]}")
                return 1
    
    return split_election_data(input_file)


if __name__ == "__main__":
    sys.exit(main())

