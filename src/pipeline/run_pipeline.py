import os
import sys

# Ensure project root is on PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.pipeline.sample_and_merge import run_sampling_and_merging
from src.pipeline.features import run_features_generation
from src.pipeline.build_db import build_duckdb_database

def main():
    print("=================== STARTING FLIGHTSCOPE PIPELINE ===================")
    
    # Step 1: Sample & Merge
    try:
        sampled_pq = run_sampling_and_merging()
    except Exception as e:
        print(f"Error during sampling and merging: {e}")
        sys.exit(1)
        
    # Step 2: Feature Engineering
    try:
        processed_pq = run_features_generation(sampled_pq)
    except Exception as e:
        print(f"Error during feature engineering: {e}")
        sys.exit(1)
        
    # Step 3: Database Load
    try:
        build_duckdb_database(processed_pq)
    except Exception as e:
        print(f"Error during database building: {e}")
        sys.exit(1)
        
    print("=================== PIPELINE COMPLETED SUCCESSFULLY ===================")

if __name__ == "__main__":
    main()
