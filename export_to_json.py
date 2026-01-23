"""
Export processed props to JSON for dashboard
Also tracks outcomes and exports performance metrics
"""
import pandas as pd
import json
import os
import sys
from datetime import date
from main_workflow import generate_betting_dataset
from save_to_database import save_props_to_database
from track_outcomes import process_past_props, export_performance_json

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass  # If it fails, continue without fixing (some environments handle it differently)

def export_for_dashboard():
    """Generate data and export to JSON for dashboard"""
    try:
        print("=" * 60)
        print("Dashboard Data Export")
        print("=" * 60)
        
        # Check for database connection string
        # Note: database.py has a fallback connection string, so we'll always try to connect
        db_conn = os.getenv('DB_CONNECTION_STRING')
        if not db_conn:
            print("⚠ Note: DB_CONNECTION_STRING environment variable not set")
            print("  Using fallback connection string from database.py")
        else:
            print("✓ Database connection string found in environment")
        
        # Always attempt database operations (database.py has fallback connection string)
        db_conn = True  # Set to True to enable database operations
        
        print("\n[Step 1/3] Generating betting dataset...")
        try:
            df = generate_betting_dataset(
                filter_overs_only=True,
                min_games=10,
                max_props=None,
                debug=False
            )
            print(f"✓ Generated dataset with {len(df)} props")
        except Exception as e:
            print(f"❌ Error generating betting dataset: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        
        if len(df) > 0:
            # Save to database
            print("\n[Step 2/3] Saving to database...")
            if db_conn:
                try:
                    save_props_to_database(df)
                    print("✓ Saved to database")
                except Exception as e:
                    print(f"⚠ Warning: Could not save to database: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("⚠ Skipping database save (no connection string)")
            
            # Track outcomes for past props (games that have already occurred)
            print("\n[Step 3/3] Tracking outcomes and generating performance metrics...")
            if db_conn:
                try:
                    # Process props from yesterday's games (to verify yesterday's predictions)
                    # This will find props with game_date = yesterday and track their outcomes
                    from datetime import timedelta
                    yesterday = date.today() - timedelta(days=1)
                    print(f"Tracking outcomes for props with game_date = {yesterday} (yesterday's games)...")
                    process_past_props(start_date=yesterday)
                    # Export performance JSON
                    export_performance_json()
                    print("✓ Performance metrics updated")
                except Exception as e:
                    print(f"⚠ Warning: Could not track outcomes: {e}")
                    print("  (This is normal if no games have occurred yet)")
                    import traceback
                    traceback.print_exc()
                    # Still create empty performance.json file
                    export_performance_json()
            else:
                print("⚠ Skipping outcome tracking (no connection string)")
                # Still create empty performance.json file
                export_performance_json()
            
            # Export to JSON for static site
            # Convert DataFrame to list of dicts
            bets_data = df.to_dict('records')
            
            # Save to dashboard data folder
            os.makedirs('dashboard/public/data', exist_ok=True)
            output_path = 'dashboard/public/data/latest-bets.json'
            try:
                with open(output_path, 'w') as f:
                    json.dump(bets_data, f, indent=2, default=str)
                print(f"\n✓ Exported {len(bets_data)} bets to {output_path}")
            except Exception as e:
                print(f"❌ Error writing JSON file: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)
            
            print("\n✅ Dashboard export complete!")
            
            return df
        else:
            print("⚠ No data to export (empty dataset)")
            # Still create an empty JSON file so the dashboard doesn't break
            os.makedirs('dashboard/public/data', exist_ok=True)
            output_path = 'dashboard/public/data/latest-bets.json'
            with open(output_path, 'w') as f:
                json.dump([], f, indent=2)
            print(f"✓ Created empty JSON file at {output_path}")
            
            # Always create performance.json file, even if empty
            try:
                export_performance_json()
            except Exception as e:
                print(f"⚠ Warning: Could not export performance JSON: {e}")
                # Create empty performance.json manually
                perf_path = 'dashboard/public/data/performance.json'
                empty_perf = {
                    "totalBets": 0,
                    "wins": 0,
                    "losses": 0,
                    "winRate": 0,
                    "totalProfit": 0,
                    "roi": 0,
                    "byProp": [],
                    "overTime": []
                }
                with open(perf_path, 'w') as f:
                    json.dump(empty_perf, f, indent=2)
                print(f"✓ Created empty performance.json file")
            
            return None
            
    except Exception as e:
        print(f"❌ Fatal error in export_for_dashboard: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        export_for_dashboard()
    except KeyboardInterrupt:
        print("\n⚠ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Unhandled exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
