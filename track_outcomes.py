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
import sys

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

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

def get_actual_stat_from_api(player_name: str, prop_type: str, game_date: date) -> Optional[float]:
    """
    Query NBA API using nba_api package to get actual stat value for a player on a specific game date
    This is used for current season games not in the training dataset
    
    Returns:
        Actual stat value, or None if not found
    """
    try:
        from nba_api.stats.endpoints import playergamelog
        from nba_api.stats.static import players
        import time
        
        # Find player ID by name using nba_api static players list
        all_players = players.get_players()
        
        # Try to find matching player
        player_id = None
        matched_name = None
        
        # First try exact match
        for player in all_players:
            full_name = f"{player['first_name']} {player['last_name']}"
            if full_name.lower() == player_name.lower():
                player_id = player['id']
                matched_name = full_name
                break
        
        # If no exact match, try partial match (handle cases like "Jaren Jackson Jr.")
        if not player_id:
            for player in all_players:
                full_name = f"{player['first_name']} {player['last_name']}"
                # Handle special cases like "Jaren Jackson Jr." vs "Jaren Jackson"
                name_normalized = player_name.replace('.', '').replace(' ', '').lower()
                full_name_normalized = full_name.replace('.', '').replace(' ', '').lower()
                if (player_name.lower() in full_name.lower() or 
                    full_name.lower() in player_name.lower() or
                    name_normalized == full_name_normalized):
                    player_id = player['id']
                    matched_name = full_name
                    break
        
        if not player_id:
            print(f"  API: Could not match '{player_name}' to any player")
            return None
        
        print(f"  API: Matched '{player_name}' to '{matched_name}' (ID: {player_id})")
        
        # Get player game log for the season
        # Determine season string (e.g., "2025-26" for 2026-01-21)
        year = game_date.year
        month = game_date.month
        if month >= 10:  # Season starts in October
            season = f"{year}-{str(year+1)[-2:]}"
        else:
            season = f"{year-1}-{str(year)[-2:]}"
        
        print(f"  API: Fetching game log for season {season}, date {game_date}")
        
        # Get game log for the player
        game_log = playergamelog.PlayerGameLog(
            player_id=player_id,
            season=season
        )
        
        # Small delay to avoid rate limiting
        time.sleep(0.6)
        
        df = game_log.get_data_frames()[0]
        
        if len(df) == 0:
            print(f"  API: No games found for {matched_name} in season {season}")
            return None
        
        # Filter to the specific date
        # nba_api returns dates in format "MMM DD, YYYY" (e.g., "Jan 21, 2026")
        df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'], format='%b %d, %Y', errors='coerce')
        game_row = df[df['GAME_DATE'].dt.date == game_date]
        
        if len(game_row) == 0:
            print(f"  API: No game found for {matched_name} on {game_date}")
            return None
        
        # Map prop types to stat columns in nba_api
        prop_to_stat_field = {
            'Points': 'PTS',
            'Rebounds': 'REB',
            'Assists': 'AST',
            'Threes': 'FG3M',  # 3-pointers made
            'Made Threes': 'FG3M',
            'Steals': 'STL',
            'Blocks': 'BLK'
        }
        
        stat_field = prop_to_stat_field.get(prop_type)
        if stat_field and stat_field in game_row.columns:
            value = float(game_row[stat_field].iloc[0])
            print(f"  API: Found {prop_type} = {value} for {matched_name} on {game_date}")
            return value
        else:
            print(f"  API: Stat field '{stat_field}' not found in response for {prop_type}")
            return None
        
    except ImportError:
        print(f"  API: nba_api package not installed. Install with: pip install nba-api")
        return None
    except Exception as e:
        print(f"  API Error for {player_name} on {game_date}: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_actual_stat(player_name: str, prop_type: str, game_date: date) -> Optional[float]:
    """
    Get the actual stat value for a player on a specific game date
    First checks the historical training dataset, then falls back to NBA API for current season
    
    Returns:
        Actual stat value, or None if not found
    """
    print(f"  [get_actual_stat] Looking up {player_name} - {prop_type} on {game_date}")
    
    # First, try the historical training dataset
    conn = get_db_connection()
    try:
        query = """
        SELECT * FROM nba_ml_training_set 
        WHERE player_full_name = %s 
        AND game_date = %s
        LIMIT 1
        """
        df = pd.read_sql_query(query, conn, params=[player_name, game_date])
        
        if len(df) > 0:
            # Found in training dataset
            print(f"  [get_actual_stat] Found in training dataset")
            stat_column = find_stat_column(df, prop_type)
            if stat_column and stat_column in df.columns:
                return float(df[stat_column].iloc[0])
    except Exception as e:
        print(f"  [get_actual_stat] Error querying training dataset: {e}")
    finally:
        conn.close()
    
    # If not found in training dataset, try NBA API (for current season games)
    # Only try API if the date is recent (within last 2 years)
    from datetime import timedelta
    two_years_ago = date.today() - timedelta(days=730)
    print(f"  [get_actual_stat] Not in training dataset. Date check: {game_date} >= {two_years_ago} = {game_date >= two_years_ago}")
    if game_date >= two_years_ago:
        print(f"  [get_actual_stat] Trying NBA API for {player_name} on {game_date}...")
        result = get_actual_stat_from_api(player_name, prop_type, game_date)
        print(f"  [get_actual_stat] API returned: {result}")
        return result
    else:
        print(f"  [get_actual_stat] Date {game_date} is too old for API lookup")
    
    return None

def determine_outcome(actual_stat: float, line: float, over_under: str) -> Optional[bool]:
    """
    Determine if a prop hit based on actual stat, line, and over/under
    
    Handles ties (pushes) explicitly:
    - Over: actual > line (win), actual == line (push/None), actual < line (loss)
    - Under: actual < line (win), actual == line (push/None), actual > line (loss)
    
    Returns:
        True if prop hit, False if prop lost, None if push (tie)
    """
    if over_under == 'Over':
        if actual_stat > line:
            return True
        elif actual_stat < line:
            return False
        else:  # actual_stat == line (push)
            return None
    elif over_under == 'Under':
        if actual_stat < line:
            return True
        elif actual_stat > line:
            return False
        else:  # actual_stat == line (push)
            return None
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
        
        # Only track games that have already occurred (game_date < today, not <= today)
        # Games from today haven't finished yet, so we can't track them
        end_date = today - timedelta(days=1)  # Only track up to yesterday
        
        # Get props with game_date between start_date and end_date (yesterday) that have already occurred
        # Props generated today are for today's games, so we track outcomes for yesterday's games
        # Use game_date (not generated_at) to find props for games that have already happened
        query = """
        SELECT pp.id, pp.player, pp.prop, pp.line, pp.over_under, pp.odds, 
               pp.game_date,
               DATE(pp.generated_at) as generated_date
        FROM processed_props pp
        LEFT JOIN bet_tracking bt ON pp.id = bt.prop_id
        WHERE pp.game_date IS NOT NULL
        AND pp.game_date >= %s
        AND pp.game_date <= %s
        AND (bt.outcome IS NULL OR bt.id IS NULL)
        ORDER BY pp.game_date DESC, pp.generated_at DESC
        """
        
        # Look for props with game_date >= start_date and <= end_date (yesterday) that have already occurred
        # This ensures we're tracking outcomes for yesterday's games and any missed days
        print(f"Looking for props with game_date >= {start_date} and game_date <= {end_date} (past games only)...")
        df = pd.read_sql_query(query, conn, params=[start_date, end_date])
        
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
            print(f"Looking up: {player} - {prop} on {game_date}")
            actual_stat = get_actual_stat(player, prop, game_date)
            
            if actual_stat is None:
                print(f"❌ Could not find actual stat for {player} - {prop} on {game_date}")
                not_found += 1
                continue
            
            # Determine outcome (handles pushes/ties)
            outcome = determine_outcome(actual_stat, line, over_under)
            
            # Skip pushes (ties) - don't track them as wins or losses
            if outcome is None:
                print(f"⚪ PUSH: {player} {prop} {over_under} {line} | Actual: {actual_stat} | Line: {line} (tie - not tracked)")
                continue
            
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
        # Get all tracked bets with outcomes, including model probabilities
        query = """
        SELECT 
            outcome,
            profit_loss,
            prop,
            game_date,
            result_date,
            model_probability,
            odds,
            expected_value
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
                "avgEV": 0,
                "byProp": [],
                "byOdds": [],
                "probCalibration": [],
                "expectedVsActual": {},
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
        
        # Cumulative profit over time and win rate by day
        over_time = []
        if 'game_date' in df.columns and df['game_date'].notna().sum() > 0:
            # Group by date and calculate daily stats
            daily_stats = df.groupby('game_date').agg({
                'outcome': ['sum', 'count'],
                'profit_loss': 'sum'
            }).reset_index()
            daily_stats.columns = ['game_date', 'wins', 'total', 'profit']
            daily_stats['win_rate'] = (daily_stats['wins'] / daily_stats['total'] * 100).round(1)
            daily_stats = daily_stats.sort_values('game_date')
            daily_stats['cumulative'] = daily_stats['profit'].cumsum()
            
            for _, row in daily_stats.iterrows():
                over_time.append({
                    "date": row['game_date'].strftime('%Y-%m-%d'),
                    "cumulative": round(row['cumulative'], 2),
                    "winRate": row['win_rate'],
                    "bets": int(row['total']),
                    "wins": int(row['wins']),
                    "profit": round(row['profit'], 2)
                })
        
        # Probability calibration analysis
        prob_calibration = []
        if 'model_probability' in df.columns and df['model_probability'].notna().sum() > 0:
            # Group bets by probability ranges and calculate actual win rates
            df['prob_bucket'] = pd.cut(df['model_probability'], 
                                       bins=[0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
                                       labels=['<50%', '50-60%', '60-70%', '70-80%', '80-90%', '90-100%'])
            
            for bucket in df['prob_bucket'].cat.categories:
                bucket_df = df[df['prob_bucket'] == bucket]
                if len(bucket_df) > 0:
                    bucket_wins = bucket_df['outcome'].sum()
                    bucket_total = len(bucket_df)
                    actual_win_rate = (bucket_wins / bucket_total) * 100 if bucket_total > 0 else 0
                    avg_predicted = bucket_df['model_probability'].mean() * 100
                    
                    prob_calibration.append({
                        "range": str(bucket),
                        "count": int(bucket_total),
                        "predicted": round(avg_predicted, 1),
                        "actual": round(actual_win_rate, 1),
                        "difference": round(avg_predicted - actual_win_rate, 1)
                    })
        
        # Performance by odds range
        by_odds = []
        if 'odds' in df.columns and df['odds'].notna().sum() > 0:
            # Categorize odds: favorites (-), small favorites, small dogs, big dogs
            def categorize_odds(odds):
                if pd.isna(odds):
                    return "Unknown"
                if odds < -150:
                    return "Heavy Favorite (<-150)"
                elif odds < -110:
                    return "Favorite (-150 to -110)"
                elif odds <= 110:
                    return "Pick'em (-110 to +110)"
                elif odds <= 150:
                    return "Underdog (+110 to +150)"
                else:
                    return "Big Underdog (>+150)"
            
            df['odds_category'] = df['odds'].apply(categorize_odds)
            
            for category in df['odds_category'].unique():
                cat_df = df[df['odds_category'] == category]
                if len(cat_df) > 0:
                    cat_wins = cat_df['outcome'].sum()
                    cat_losses = len(cat_df) - cat_wins
                    cat_profit = cat_df['profit_loss'].sum() if 'profit_loss' in cat_df.columns else 0
                    cat_win_rate = (cat_wins / len(cat_df)) * 100 if len(cat_df) > 0 else 0
                    
                    by_odds.append({
                        "category": category,
                        "count": int(len(cat_df)),
                        "wins": int(cat_wins),
                        "losses": int(cat_losses),
                        "winRate": round(cat_win_rate, 1),
                        "profit": round(cat_profit, 2)
                    })
        
        # Expected vs Actual performance
        expected_vs_actual = {}
        if 'model_probability' in df.columns and df['model_probability'].notna().sum() > 0:
            expected_wins = df['model_probability'].sum()
            actual_wins = df['outcome'].sum()
            expected_vs_actual = {
                "expectedWins": round(expected_wins, 1),
                "actualWins": int(actual_wins),
                "difference": round(actual_wins - expected_wins, 1)
            }
        
        # Average EV of bets placed
        avg_ev = 0
        if 'expected_value' in df.columns and df['expected_value'].notna().sum() > 0:
            avg_ev = df['expected_value'].mean()
        
        return {
            "totalBets": int(len(df)),
            "wins": int(wins),
            "losses": int(losses),
            "winRate": round(win_rate, 1),
            "totalProfit": round(total_profit, 2),
            "roi": round(roi, 1),
            "avgEV": round(avg_ev, 3),
            "byProp": by_prop,
            "byOdds": by_odds,
            "probCalibration": prob_calibration,
            "expectedVsActual": expected_vs_actual,
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
    print("\nNOTE: This script processes props that:")
    print("  - Have game_date set (NOT NULL)")
    print("  - Have game_date <= today (game has already occurred)")
    print("  - Haven't been tracked yet")
    print("\nUsage:")
    print("  python track_outcomes.py           # Track yesterday's games")
    print("  python track_outcomes.py 2        # Track last 2 days")
    print("  python track_outcomes.py 7        # Track last 7 days")
    print("=" * 60)
    
    # Default: track yesterday's games (most common use case)
    days_back = 1
    if len(sys.argv) > 1:
        try:
            days_back = int(sys.argv[1])
        except ValueError:
            print(f"⚠ Invalid argument '{sys.argv[1]}', using default: 1 day")
    
    start_date = date.today() - timedelta(days=days_back)
    
    # Process props from start_date onward
    # Only processes games that have already happened (game_date <= today)
    print(f"\n1. Processing props from {start_date} to {date.today()}...")
    print(f"   Looking for props with game_date >= {start_date} that have already occurred")
    process_past_props(start_date=start_date)
    
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
