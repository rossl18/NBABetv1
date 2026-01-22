"""
Script to inspect the database schema and sample data
Run this first to understand the database structure
"""
from database import get_table_schema, query_historical_data
import pandas as pd

def inspect_database():
    """Inspect database structure and sample data"""
    print("="*60)
    print("DATABASE INSPECTION")
    print("="*60)
    
    # Get schema
    print("\n[1] Table Schema:")
    print("-" * 60)
    schema = get_table_schema()
    print(schema.to_string(index=False))
    
    # Get sample data
    print("\n[2] Sample Data (first 5 rows):")
    print("-" * 60)
    sample = query_historical_data(limit=5)
    if len(sample) > 0:
        print(f"Columns: {list(sample.columns)}")
        print(f"\nShape: {sample.shape}")
        print("\nData:")
        print(sample.head().to_string())
        
        # Show data types
        print("\n[3] Data Types:")
        print("-" * 60)
        print(sample.dtypes)
        
        # Show unique values for key columns
        print("\n[4] Unique Values:")
        print("-" * 60)
        if 'player_name' in sample.columns:
            print(f"Unique players: {sample['player_name'].nunique()}")
            print(f"Sample players: {sample['player_name'].unique()[:10]}")
        
        if 'prop_type' in sample.columns:
            print(f"\nUnique prop types: {sample['prop_type'].unique()}")
        elif any('prop' in col.lower() for col in sample.columns):
            prop_cols = [col for col in sample.columns if 'prop' in col.lower()]
            for col in prop_cols:
                print(f"\n{col} unique values: {sample[col].unique()[:10]}")
    else:
        print("No data found in table")
    
    print("\n" + "="*60)
    print("Inspection complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Review the schema above")
    print("2. Update feature_engineering.py column mappings if needed")
    print("3. Run main_workflow.py to generate betting dataset")

if __name__ == "__main__":
    inspect_database()
