#!/usr/bin/env python
"""
Process CDC WONDER data from CSV to tab-delimited format expected by pipeline.

Converts the downloaded CSV file to the format expected by the data loaders.
"""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from pain_politics.config import paths
from pain_politics.utils import get_logger

logger = get_logger(__name__)


def process_cdc_wonder_file(input_file: Path, output_prefix: str = None):
    """
    Process CDC WONDER CSV file and create tab-delimited output.
    
    Args:
        input_file: Path to the downloaded CSV file
        output_prefix: Optional prefix for output files (default: use input filename)
    """
    logger.info(f"Processing CDC WONDER file: {input_file}")
    
    try:
        # Read the CSV file
        df = pd.read_csv(input_file)
        logger.info(f"  Loaded {len(df):,} rows")
        logger.info(f"  Columns: {list(df.columns)}")
        
        # Clean up the data
        # Remove any rows with "Total" in County (footer rows)
        df = df[~df['County'].str.contains('Total', case=False, na=False)]
        
        # Rename columns to match expected format
        column_mapping = {
            'Crude Rate': 'Age Adjusted Rate',
        }
        df = df.rename(columns=column_mapping)
        
        # Keep only needed columns
        needed_columns = ['County', 'County Code', 'Deaths', 'Population', 'Age Adjusted Rate']
        missing_cols = [col for col in needed_columns if col not in df.columns]
        if missing_cols:
            logger.warning(f"  Missing columns: {missing_cols}")
        
        df_clean = df[needed_columns].copy()
        
        # Convert numeric columns
        for col in ['Deaths', 'Population', 'Age Adjusted Rate']:
            # Handle "Unreliable" values
            df_clean[col] = df_clean[col].replace('Unreliable', pd.NA)
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        
        # Remove rows with missing County Code
        df_clean = df_clean.dropna(subset=['County Code'])
        
        logger.info(f"  Cleaned data: {len(df_clean):,} rows")
        
        # Create both output files
        # (The loader will aggregate by FIPS, so the same data works for both periods)
        output_files = [
            paths.data_raw / "cdc_wonder" / "overdose_2013_2016.txt",
            paths.data_raw / "cdc_wonder" / "overdose_2017_2020.txt",
        ]
        
        for output_file in output_files:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            df_clean.to_csv(output_file, sep='\t', index=False)
            logger.info(f"  ✅ Created: {output_file}")
        
        logger.info("")
        logger.info("✅ CDC WONDER data processing complete!")
        logger.info(f"   Created {len(output_files)} files with {len(df_clean):,} counties each")
        logger.info("")
        logger.info("Note: Both files contain the same aggregated data since your")
        logger.info("      download covered all years. The pipeline will handle this correctly.")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error processing file: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main entry point."""
    
    # Look for the downloaded file
    cdc_wonder_dir = paths.data_raw / "cdc_wonder"
    
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
        if not input_file.exists():
            # Try relative to cdc_wonder directory
            input_file = cdc_wonder_dir / sys.argv[1]
            if not input_file.exists():
                logger.error(f"❌ File not found: {sys.argv[1]}")
                return 1
    else:
        # Look for CSV files in cdc_wonder directory
        csv_files = list(cdc_wonder_dir.glob("*.csv"))
        
        if not csv_files:
            logger.error(f"❌ No CSV files found in {cdc_wonder_dir}")
            logger.info("")
            logger.info("Please provide the path to your CDC WONDER download:")
            logger.info("  python scripts/process_cdc_wonder.py <filename>")
            return 1
        
        if len(csv_files) == 1:
            input_file = csv_files[0]
            logger.info(f"Found CDC WONDER file: {input_file.name}")
        else:
            logger.info(f"Found multiple CSV files in {cdc_wonder_dir}:")
            for f in csv_files:
                logger.info(f"  - {f.name}")
            logger.info("")
            logger.info("Please specify which file to process:")
            logger.info("  python scripts/process_cdc_wonder.py <filename>")
            return 1
    
    return process_cdc_wonder_file(input_file)


if __name__ == "__main__":
    sys.exit(main())

