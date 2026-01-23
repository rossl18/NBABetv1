"""
Script to check when predictions were made and optionally regenerate them with the new model.
This helps ensure performance metrics reflect the new model's performance.
"""
import pandas as pd
import psycopg2
from datetime import date, timedelta
import os
import sys

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

DB_CONNECTION_STRING = os.getenv(
    'DB_CONNECTION_STRING',
    "postgresql://neondb_owner:npg_4mPxqU1CzSoI@ep-summer-band-ahle3ux5-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
)

def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = psycopg2.connect(DB_CONNECTION_STRING)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise

def check_prediction_dates(days_back: int = 7):
    """
    Check when predictions were made for recent games.
    This helps determine if they used the old or new model.
    """
    conn = get_db_connection()
    try:
        start_date = date.today() - timedelta(days=days_back)
        
        query = """
        SELECT 
            DATE(generated_at) as prediction_date,
            game_date,
            COUNT(*) as num_predictions,
            MIN(generated_at) as first_prediction,
            MAX(generated_at) as last_prediction
        FROM processed_props
        WHERE game_date >= %s
        AND game_date <= %s
        GROUP BY DATE(generated_at), game_date
        ORDER BY game_date DESC, prediction_date DESC
        """
        
        end_date = date.today() - timedelta(days=1)  # Up to yesterday
        df = pd.read_sql_query(query, conn, params=[start_date, end_date])
        
        print("=" * 70)
        print("PREDICTION DATE ANALYSIS")
        print("=" * 70)
        print(f"\nChecking predictions for games from {start_date} to {end_date}")
        print(f"\n{'Game Date':<12} {'Prediction Date':<18} {'Count':<8} {'First Generated':<20} {'Last Generated':<20}")
        print("-" * 70)
        
        if len(df) == 0:
            print("No predictions found for this date range.")
        else:
            for _, row in df.iterrows():
                print(f"{row['game_date']:<12} {row['prediction_date']:<18} {row['num_predictions']:<8} "
                      f"{row['first_prediction']:<20} {row['last_prediction']:<20}")
            
            print("\n" + "=" * 70)
            print("ANALYSIS:")
            print("=" * 70)
            
            # Check if predictions were made today (after model improvements)
            today = date.today()
            today_predictions = df[df['prediction_date'] == today]
            
            if len(today_predictions) > 0:
                print(f"✅ Found {len(today_predictions)} game dates with predictions made TODAY")
                print("   These predictions use the NEW model (with improvements)")
            else:
                print("⚠ No predictions found that were made TODAY")
                print("   Recent predictions likely use the OLD model")
            
            # Check most recent prediction date
            most_recent = df['prediction_date'].max()
            print(f"\nMost recent prediction date: {most_recent}")
            
            if most_recent < today:
                print("⚠ Most recent predictions are from before today")
                print("   To get new model performance, you should regenerate predictions")
            else:
                print("✅ Recent predictions were made today (using new model)")
        
        return df
        
    except Exception as e:
        print(f"Error checking prediction dates: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()

def regenerate_recent_predictions(days_back: int = 7, confirm: bool = False):
    """
    Regenerate predictions for recent games using the new model.
    
    WARNING: This will create NEW rows in processed_props (not update old ones).
    The old predictions will remain, and new ones will be added.
    
    Args:
        days_back: How many days back to regenerate (default: 7)
        confirm: If False, just shows what would be done. If True, actually does it.
    """
    print("=" * 70)
    print("REGENERATE RECENT PREDICTIONS WITH NEW MODEL")
    print("=" * 70)
    
    if not confirm:
        print("\n⚠ DRY RUN MODE - No changes will be made")
        print("   Set confirm=True to actually regenerate predictions")
    
    print(f"\nThis will:")
    print(f"  1. Generate new predictions for games from the last {days_back} days")
    print(f"  2. Use the NEW model (enhanced features, time weighting, optimized hyperparameters)")
    print(f"  3. Create NEW rows in processed_props (old predictions remain)")
    print(f"  4. Then you can track outcomes to get new model performance")
    
    if not confirm:
        print("\n⚠ To actually run this, call:")
        print(f"   regenerate_recent_predictions(days_back={days_back}, confirm=True)")
        return
    
    print("\n" + "=" * 70)
    print("Starting regeneration...")
    print("=" * 70)
    
    try:
        from main_workflow import generate_betting_dataset
        from save_to_database import save_props_to_database
        
        # Generate new predictions (these will use the new model)
        print("\n[Step 1/2] Generating new predictions with improved model...")
        df = generate_betting_dataset(
            filter_overs_only=True,
            min_games=10,
            max_props=None,
            debug=False
        )
        
        if len(df) == 0:
            print("⚠ No props generated (may be no games in this period)")
            return
        
        print(f"✓ Generated {len(df)} new predictions")
        
        # Filter to only recent games
        start_date = date.today() - timedelta(days=days_back)
        if 'game_date' in df.columns:
            df_recent = df[df['game_date'] >= start_date].copy()
            print(f"✓ Filtered to {len(df_recent)} predictions for games from {start_date} onwards")
        else:
            df_recent = df
            print("⚠ No game_date column found, saving all predictions")
        
        # Save to database
        print("\n[Step 2/2] Saving to database...")
        save_props_to_database(df_recent)
        print("✓ Saved to database")
        
        print("\n" + "=" * 70)
        print("✅ REGENERATION COMPLETE")
        print("=" * 70)
        print(f"\nGenerated {len(df_recent)} new predictions with the improved model.")
        print("\nNext steps:")
        print("  1. Run track_outcomes.py to match these new predictions with game results")
        print("  2. Performance metrics will now reflect the new model's performance")
        
    except Exception as e:
        print(f"\n❌ Error during regeneration: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Check and optionally regenerate recent predictions')
    parser.add_argument('--check', action='store_true', help='Check when predictions were made')
    parser.add_argument('--regenerate', action='store_true', help='Regenerate predictions with new model')
    parser.add_argument('--days', type=int, default=7, help='Number of days back to check/regenerate (default: 7)')
    parser.add_argument('--confirm', action='store_true', help='Actually regenerate (required for --regenerate)')
    
    args = parser.parse_args()
    
    if args.check:
        check_prediction_dates(days_back=args.days)
    elif args.regenerate:
        if not args.confirm:
            print("⚠ WARNING: --regenerate requires --confirm flag")
            print("   This is a safety measure to prevent accidental regeneration")
            print("\nTo actually regenerate, run:")
            print(f"   python check_and_regenerate_predictions.py --regenerate --days {args.days} --confirm")
        else:
            regenerate_recent_predictions(days_back=args.days, confirm=True)
    else:
        # Default: just check
        print("Checking prediction dates... (use --regenerate --confirm to regenerate)")
        print()
        check_prediction_dates(days_back=args.days)
        print("\n" + "=" * 70)
        print("To regenerate predictions with the new model:")
        print(f"  python check_and_regenerate_predictions.py --regenerate --days {args.days} --confirm")
        print("=" * 70)
