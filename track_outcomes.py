"""
Script to track bet outcomes by matching processed_props to historical game results
and updating the bet_tracking table with actual outcomes.
"""
import pandas as pd
import psycopg2
from datetime import datetime, date, timedelta
from typing import Optional, Dict
import json
import os

# Database connection string - use environment variable if set, otherwise use default
DB_CONNECTION_STRING = os.getenv(
    'DB_CONNECTION_STRING',
    "postgresql://neondb_owner:npg_4mPxqU1CzSoI@ep-summer-band-ahle3ux5-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
)

# Prop type to stat column mapping (same as in feature_engineering.py)
PROP_TO_STAT = {
    'Points': ['pts', 'points', 'point'],
    'Rebounds': ['reb', 'rebounds', 'rebound'],
    'Assists': ['ast', 'assists', 'assist'],
    'Threes': ['3p', 'threes', 'three', '3pm', '3p_made'],
    'Made Threes': ['3p', 'threes', 'three', '3pm', '3p_made'],
    'Steals': ['stl', 'steals', 'steal'],
    'Blocks': ['blk', 'blocks', 'block']
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = psycopg2.connect(DB_CONNECTION_STRING)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise

def find_stat_column(df: pd.DataFrame, prop_type: str) -> Optional[str]:
    """Find the actual stat column for a prop type in the dataframe"""
    stat_keywords = PROP_TO_STAT.get(prop_type, [prop_type.lower()])
    
    for keyword in stat_keywords:
        matching_cols = [col for col in df.columns if keyword.lower() in col.lower() 
                        and 'target' not in col.lower() and 'feat' not in col.lower()]
        if matching_cols:
            return matching_cols[0]
    return None

def get_actual_stat(player_name: str, prop_type: str, game_date: date) -> Optional[float]:
    """
    Query historical database to get the actual stat value for a player on a specific game date
    
    Returns:
        Actual stat value, or None if not found
    """
    conn = get_db_connection()
    try:
        query = """
        SELECT * FROM nba_ml_training_set 
        WHERE player_full_name = %s 
        AND game_date = %s
        LIMIT 1
        """
        df = pd.read_sql_query(query, conn, params=[player_name, game_date])
        
        if len(df) == 0:
            return None
        
        # Find the stat column
        stat_column = find_stat_column(df, prop_type)
        if stat_column and stat_column in df.columns:
            return float(df[stat_column].iloc[0])
        else:
            print(f"Warning: Could not find stat column for {prop_type} in player data")
            return None
    except Exception as e:
        print(f"Error querying actual stat: {e}")
        return None
    finally:
        conn.close()

def determine_outcome(actual_stat: float, line: float, over_under: str) -> bool:
    """
    Determine if a prop hit based on actual stat, line, and over/under
    
    Returns:
        True if prop hit, False if not
    """
    if over_under == 'Over':
        return actual_stat > line
    elif over_under == 'Under':
        return actual_stat < line
    else:
        raise ValueError(f"over_under must be 'Over' or 'Under', got: {over_under}")

def calculate_profit_loss(outcome: bool, odds: int, bet_amount: float = 100.0) -> float:
    """
    Calculate profit/loss from a bet
    
    Args:
        outcome: True if bet won, False if lost
        odds: American odds (e.g., -110, +150)
        bet_amount: Amount bet (default $100)
    
    Returns:
        Profit (positive) or loss (negative)
    """
    if not outcome:
        return -bet_amount  # Lost the bet
    
    # Convert American odds to decimal
    if odds > 0:
        decimal_odds = 1 + (odds / 100)
    else:
        decimal_odds = 1 + (100 / abs(odds))
    
    # Profit = (bet_amount * decimal_odds) - bet_amount
    return (bet_amount * decimal_odds) - bet_amount

def update_bet_tracking(prop_id: int, outcome: bool, actual_result: float, 
                       game_date: date, odds: Optional[int] = None) -> None:
    """
    Update or insert bet tracking record with outcome
    """
    conn = get_db_connection()
    try:
        # Check if record already exists
        check_query = "SELECT id FROM bet_tracking WHERE prop_id = %s"
        cursor = conn.cursor()
        cursor.execute(check_query, (prop_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing record
            update_query = """
            UPDATE bet_tracking 
            SET outcome = %s,
                actual_result = %s,
                result_date = %s,
                profit_loss = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE prop_id = %s
            """
            profit_loss = calculate_profit_loss(outcome, odds) if odds else None
            cursor.execute(update_query, (outcome, actual_result, date.today(), profit_loss, prop_id))
        else:
            # Insert new record - first get prop details from processed_props
            prop_query = """
            SELECT player, prop, line, over_under, odds, model_probability, expected_value
            FROM processed_props
            WHERE id = %s
            """
            cursor.execute(prop_query, (prop_id,))
            prop_data = cursor.fetchone()
            
            if prop_data:
                insert_query = """
                INSERT INTO bet_tracking 
                (prop_id, player, prop, line, over_under, odds, model_probability, 
                 expected_value, outcome, actual_result, profit_loss, game_date, result_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                profit_loss = calculate_profit_loss(outcome, odds) if odds else None
                cursor.execute(insert_query, (
                    prop_id, prop_data[0], prop_data[1], prop_data[2], prop_data[3],
                    prop_data[4], prop_data[5], prop_data[6], outcome, actual_result,
                    profit_loss, game_date, date.today()
                ))
        
        conn.commit()
        cursor.close()
    except Exception as e:
        conn.rollback()
        print(f"Error updating bet_tracking: {e}")
        raise
    finally:
        conn.close()

def process_past_props(start_date: Optional[date] = None, days_back: Optional[int] = None) -> None:
    """
    Process props from processed_props that have game_date in the past
    and update bet_tracking with outcomes
    
    Args:
        start_date: Only process props with game_date >= this date (default: today)
        days_back: Alternative: How many days back from today to look (if start_date not provided)
                   If both None, defaults to today (only process from today onward)
    
    Note: This function only processes props that:
    - Have a game_date set (NOT NULL)
    - Have game_date >= start_date (default: today)
    - Have game_date <= today (game has already occurred)
    - Haven't been tracked yet (no existing bet_tracking record)
    """
    conn = get_db_connection()
    try:
        # Default: only process from today onward (no historical backfill)
        if start_date is None:
            if days_back is None:
                start_date = date.today()  # Start from today only
            else:
                start_date = date.today() - timedelta(days=days_back)
        
        today = date.today()
        
        # Get props with game_date on or after start_date that are in the past
        # and haven't been tracked yet
        query = """
        SELECT pp.id, pp.player, pp.prop, pp.line, pp.over_under, pp.odds, pp.game_date
        FROM processed_props pp
        LEFT JOIN bet_tracking bt ON pp.id = bt.prop_id
        WHERE pp.game_date IS NOT NULL
        AND pp.game_date >= %s
        AND pp.game_date <= %s
        AND (bt.outcome IS NULL OR bt.id IS NULL)
        ORDER BY pp.game_date DESC
        """
        
        df = pd.read_sql_query(query, conn, params=[start_date, today])
        
        print(f"Found {len(df)} props to process")
        
        processed = 0
        not_found = 0
        
        for _, row in df.iterrows():
            prop_id = row['id']
            player = row['player']
            prop = row['prop']
            line = row['line']
            over_under = row['over_under']
            odds = row['odds']
            game_date = row['game_date']
            
            # Get actual stat
            actual_stat = get_actual_stat(player, prop, game_date)
            
            if actual_stat is None:
                print(f"Could not find actual stat for {player} - {prop} on {game_date}")
                not_found += 1
                continue
            
            # Determine outcome
            outcome = determine_outcome(actual_stat, line, over_under)
            
            # Update bet_tracking
            update_bet_tracking(prop_id, outcome, actual_stat, game_date, odds)
            
            status = "✅ HIT" if outcome else "❌ MISS"
            print(f"{status}: {player} {prop} {over_under} {line} | Actual: {actual_stat} | Line: {line}")
            processed += 1
        
        print(f"\nProcessed: {processed}")
        print(f"Not found: {not_found}")
        
    except Exception as e:
        print(f"Error processing past props: {e}")
        raise
    finally:
        conn.close()

def generate_performance_metrics() -> Dict:
    """
    Generate performance metrics from bet_tracking table
    
    Returns:
        Dictionary with performance statistics
    """
    conn = get_db_connection()
    try:
        # Get all tracked bets with outcomes
        query = """
        SELECT 
            outcome,
            profit_loss,
            prop,
            game_date,
            result_date
        FROM bet_tracking
        WHERE outcome IS NOT NULL
        ORDER BY game_date DESC
        """
        
        df = pd.read_sql_query(query, conn)
        
        if len(df) == 0:
            return {
                "totalBets": 0,
                "wins": 0,
                "losses": 0,
                "winRate": 0,
                "totalProfit": 0,
                "roi": 0,
                "byProp": [],
                "overTime": []
            }
        
        # Calculate overall stats
        wins = df['outcome'].sum()
        losses = len(df) - wins
        total_profit = df['profit_loss'].sum() if 'profit_loss' in df.columns else 0
        win_rate = (wins / len(df)) * 100 if len(df) > 0 else 0
        
        # Calculate ROI (assuming $100 bets)
        total_bet_amount = len(df) * 100
        roi = (total_profit / total_bet_amount) * 100 if total_bet_amount > 0 else 0
        
        # Performance by prop type
        by_prop = []
        for prop_type in df['prop'].unique():
            prop_df = df[df['prop'] == prop_type]
            prop_wins = prop_df['outcome'].sum()
            prop_losses = len(prop_df) - prop_wins
            prop_profit = prop_df['profit_loss'].sum() if 'profit_loss' in prop_df.columns else 0
            by_prop.append({
                "prop": prop_type,
                "wins": int(prop_wins),
                "losses": int(prop_losses),
                "profit": round(prop_profit, 2)
            })
        
        # Cumulative profit over time
        df_sorted = df.sort_values('game_date')
        df_sorted['cumulative'] = df_sorted['profit_loss'].cumsum() if 'profit_loss' in df_sorted.columns else 0
        
        over_time = []
        for _, row in df_sorted.iterrows():
            over_time.append({
                "date": row['game_date'].strftime('%Y-%m-%d'),
                "cumulative": round(row['cumulative'], 2)
            })
        
        return {
            "totalBets": int(len(df)),
            "wins": int(wins),
            "losses": int(losses),
            "winRate": round(win_rate, 1),
            "totalProfit": round(total_profit, 2),
            "roi": round(roi, 1),
            "byProp": by_prop,
            "overTime": over_time
        }
        
    except Exception as e:
        print(f"Error generating performance metrics: {e}")
        raise
    finally:
        conn.close()

def export_performance_json(output_path: str = "dashboard/public/data/performance.json") -> None:
    """Export performance metrics to JSON file for dashboard"""
    metrics = generate_performance_metrics()
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"Performance metrics exported to {output_path}")

if __name__ == "__main__":
    print("=" * 60)
    print("Tracking Bet Outcomes")
    print("=" * 60)
    print("\nNOTE: This script only processes props that:")
    print("  - Have game_date set (NOT NULL)")
    print("  - Have game_date >= today")
    print("  - Have game_date <= today (game has already occurred)")
    print("  - Haven't been tracked yet")
    print("\nTo track historical props, use: process_past_props(days_back=N)")
    print("=" * 60)
    
    # Process props from today onward (no historical backfill)
    # Only processes games that have already happened (game_date <= today)
    print("\n1. Processing props from today onward...")
    print(f"   Looking for props with game_date >= {date.today()} that have already occurred")
    process_past_props(start_date=date.today())  # Only from today forward
    
    print("\n2. Generating performance metrics...")
    metrics = generate_performance_metrics()
    
    print("\nPerformance Summary:")
    print(f"  Total Bets: {metrics['totalBets']}")
    print(f"  Wins: {metrics['wins']}")
    print(f"  Losses: {metrics['losses']}")
    print(f"  Win Rate: {metrics['winRate']}%")
    print(f"  Total Profit: ${metrics['totalProfit']}")
    print(f"  ROI: {metrics['roi']}%")
    
    print("\n3. Exporting to JSON...")
    export_performance_json()
    
    print("\n✅ Done!")
