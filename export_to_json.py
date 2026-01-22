"""
Export processed props to JSON for dashboard
Also tracks outcomes and exports performance metrics
"""
import pandas as pd
import json
from datetime import date
from main_workflow import generate_betting_dataset
from save_to_database import save_props_to_database
from track_outcomes import process_past_props, export_performance_json

def export_for_dashboard():
    """Generate data and export to JSON for dashboard"""
    print("=" * 60)
    print("Dashboard Data Export")
    print("=" * 60)
    
    print("\n[Step 1/3] Generating betting dataset...")
    df = generate_betting_dataset(
        filter_overs_only=True,
        min_games=10,
        max_props=None,
        debug=False
    )
    
    if len(df) > 0:
        # Save to database
        print("\n[Step 2/3] Saving to database...")
        try:
            save_props_to_database(df)
            print("✓ Saved to database")
        except Exception as e:
            print(f"⚠ Warning: Could not save to database: {e}")
        
        # Track outcomes for past props (games that have already occurred)
        print("\n[Step 3/3] Tracking outcomes and generating performance metrics...")
        try:
            # Process props from today that have already occurred
            process_past_props(start_date=date.today())
            # Export performance JSON
            export_performance_json()
            print("✓ Performance metrics updated")
        except Exception as e:
            print(f"⚠ Warning: Could not track outcomes: {e}")
            print("  (This is normal if no games have occurred yet)")
        
        # Export to JSON for static site
        # Convert DataFrame to list of dicts
        bets_data = df.to_dict('records')
        
        # Save to dashboard data folder
        import os
        os.makedirs('dashboard/public/data', exist_ok=True)
        output_path = 'dashboard/public/data/latest-bets.json'
        with open(output_path, 'w') as f:
            json.dump(bets_data, f, indent=2, default=str)
        
        print(f"\n✓ Exported {len(bets_data)} bets to {output_path}")
        print("\n✅ Dashboard export complete!")
        
        return df
    else:
        print("No data to export")
        return None

if __name__ == "__main__":
    export_for_dashboard()
