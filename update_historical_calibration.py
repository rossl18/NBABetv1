"""
Script to update historical probabilities with new calibration system
and regenerate performance metrics
"""
import pandas as pd
import psycopg2
import numpy as np
from typing import Optional
import os
import sys

def _configure_utf8_console() -> None:
    """
    Best-effort UTF-8 output on Windows without breaking stdout/stderr.

    Avoid wrapping TextIOWrapper around sys.stdout/sys.stderr buffers because it can
    lead to 'I/O operation on closed file' on interpreter shutdown in some shells.
    """
    if sys.platform != 'win32':
        return
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        # If reconfigure isn't supported (or fails), continue with defaults.
        return

_configure_utf8_console()

# Database connection string
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

def apply_new_calibration(old_prob: float, implied_prob: Optional[float] = None) -> float:
    """
    Apply the new aggressive calibration to an old probability value.
    This approximates what the new calibration would produce.
    
    Note: This is not perfect since we're re-calibrating an already-calibrated value,
    but it's the best we can do without re-running all models.
    """
    if pd.isna(old_prob) or old_prob is None:
        return old_prob
    
    prob = max(0.0, min(1.0, float(old_prob)))
    
    # Apply new calibration mapping
    if prob > 0.90:
        # Map [0.90, 1.0] to [0.65, 0.75]
        excess = (prob - 0.90) / 0.10
        calibrated = 0.65 + excess * 0.10
    elif prob > 0.75:
        # Map [0.75, 0.90] to [0.60, 0.65]
        excess = (prob - 0.75) / 0.15
        calibrated = 0.60 + excess * 0.05
    elif prob < 0.10:
        # Map [0.0, 0.10] to [0.10, 0.20]
        excess = prob / 0.10
        calibrated = 0.10 + excess * 0.10
    else:
        # Map [0.10, 0.75] to [0.20, 0.60]
        normalized = (prob - 0.10) / 0.65
        calibrated = 0.20 + normalized * 0.40
    
    # If we have implied probability, blend if way off
    if implied_prob is not None and not pd.isna(implied_prob):
        implied_prob = max(0.05, min(0.95, float(implied_prob)))
        prob_diff = abs(calibrated - implied_prob)
        if prob_diff > 0.25:
            blend_weight = min(0.5, prob_diff * 1.5)
            calibrated = (1 - blend_weight) * calibrated + blend_weight * implied_prob
    
    # Final clamp
    return max(0.10, min(0.75, calibrated))

def update_historical_probabilities():
    """
    Update all historical probabilities in processed_props and bet_tracking
    with the new calibration system
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        print("=" * 60)
        print("Updating Historical Probabilities with New Calibration")
        print("=" * 60)
        
        # Step 1: Update processed_props
        print("\n[Step 1/3] Updating processed_props table...")
        query = """
        SELECT id, model_probability, implied_probability, odds
        FROM processed_props
        WHERE model_probability IS NOT NULL
        """
        cursor.execute(query)
        props = cursor.fetchall()
        
        updated_count = 0
        for prop_id, old_prob, implied_prob, odds in props:
            new_prob = apply_new_calibration(old_prob, implied_prob)
            
            # Recalculate EV with new probability
            if odds and not pd.isna(odds):
                # Convert American odds to decimal
                if odds > 0:
                    decimal_odds = 1 + (odds / 100)
                else:
                    decimal_odds = 1 + (100 / abs(odds))
                
                # Calculate new EV using market-adjusted calculation
                # Import the function to use the same logic as main workflow
                from expected_value import calculate_expected_value_from_american
                new_ev = calculate_expected_value_from_american(new_prob, odds, implied_prob)
                
                # Calculate new edge
                if implied_prob and not pd.isna(implied_prob):
                    new_edge = new_prob - implied_prob
                else:
                    new_edge = None
            else:
                new_ev = None
                new_edge = None
            
            # Update processed_props
            update_query = """
            UPDATE processed_props
            SET model_probability = %s,
                expected_value = %s,
                edge = %s
            WHERE id = %s
            """
            cursor.execute(update_query, (new_prob, new_ev, new_edge, prop_id))
            updated_count += 1
        
        conn.commit()
        print(f"✓ Updated {updated_count} records in processed_props")
        
        # Step 2: Update bet_tracking
        print("\n[Step 2/3] Updating bet_tracking table...")
        query = """
        SELECT bt.id, bt.prop_id, bt.model_probability, bt.expected_value, bt.odds,
               pp.implied_probability
        FROM bet_tracking bt
        LEFT JOIN processed_props pp ON bt.prop_id = pp.id
        WHERE bt.model_probability IS NOT NULL
        """
        cursor.execute(query)
        bets = cursor.fetchall()
        
        updated_bets = 0
        for bet_id, prop_id, old_prob, old_ev, odds, implied_prob in bets:
            new_prob = apply_new_calibration(old_prob, implied_prob)
            
            # Recalculate EV using market-adjusted calculation
            if odds and not pd.isna(odds):
                from expected_value import calculate_expected_value_from_american
                new_ev = calculate_expected_value_from_american(new_prob, odds, implied_prob)
            else:
                new_ev = old_ev
            
            # Update bet_tracking
            update_query = """
            UPDATE bet_tracking
            SET model_probability = %s,
                expected_value = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """
            cursor.execute(update_query, (new_prob, new_ev, bet_id))
            updated_bets += 1
        
        conn.commit()
        print(f"✓ Updated {updated_bets} records in bet_tracking")
        
        # Step 3: Regenerate performance metrics
        print("\n[Step 3/3] Regenerating performance metrics...")
        from track_outcomes import export_performance_json
        export_performance_json()
        print("✓ Performance metrics regenerated")
        
        print("\n" + "=" * 60)
        print("✅ Historical calibration update complete!")
        print(f"   - Updated {updated_count} props")
        print(f"   - Updated {updated_bets} tracked bets")
        print("=" * 60)
        
        cursor.close()
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error updating historical probabilities: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    try:
        update_historical_probabilities()
    except KeyboardInterrupt:
        print("\n⚠ Interrupted by user")
    except Exception as e:
        print(f"❌ Unhandled exception: {e}")
        import traceback
        traceback.print_exc()
