"""
Database connection and query module for Neon PostgreSQL database
"""
import os
import psycopg2
import pandas as pd
from typing import Optional, Dict, Any

# Database connection string - use environment variable if set, otherwise use default
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

def query_historical_data(player_name: Optional[str] = None, 
                         prop_type: Optional[str] = None,
                         limit: Optional[int] = None) -> pd.DataFrame:
    """
    Query historical data from nba_ml_training_set table
    
    Args:
        player_name: Filter by player name (optional)
        prop_type: Filter by prop type (optional) - not used, kept for compatibility
        limit: Limit number of rows returned (optional)
    
    Returns:
        DataFrame with historical data
    """
    conn = get_db_connection()
    try:
        query = "SELECT * FROM nba_ml_training_set WHERE 1=1"
        params = []
        
        if player_name:
            query += " AND player_full_name = %s"
            params.append(player_name)
        
        # Note: prop_type filtering removed since database doesn't have prop_type column
        # We filter by target columns instead in get_player_historical_data
        
        if limit:
            query += f" LIMIT {limit}"
        
        # Sort by game_date descending to get most recent games first
        query += " ORDER BY game_date DESC"
        
        df = pd.read_sql_query(query, conn, params=params if params else None)
        return df
    except Exception as e:
        print(f"Error querying database: {e}")
        raise
    finally:
        conn.close()

def get_table_schema() -> pd.DataFrame:
    """Get the schema of the nba_ml_training_set table"""
    conn = get_db_connection()
    try:
        query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'nba_ml_training_set'
        ORDER BY ordinal_position;
        """
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        print(f"Error getting schema: {e}")
        raise
    finally:
        conn.close()

def get_player_historical_data(player_name: str, prop_type: str) -> pd.DataFrame:
    """
    Get historical data for a specific player and prop type
    
    Args:
        player_name: Name of the player
        prop_type: Type of prop (e.g., 'Points', 'Rebounds', 'Assists', 'Threes')
    
    Returns:
        DataFrame with historical data for the player/prop combination
    """
    # Get all data for player (no prop_type filtering since DB doesn't have that column)
    df = query_historical_data(player_name=player_name)
    
    # Map prop types to target column names
    # Note: Database doesn't have target_threes, so we'll use a workaround
    prop_to_target = {
        'Points': 'target_pts',
        'Rebounds': 'target_reb',
        'Assists': 'target_ast',
        'Threes': None,  # No target_threes column - will need to use raw stats if available
        'Made Threes': None,  # No target_threes column
        'Steals': 'target_stl',
        'Blocks': 'target_blk'
    }
    
    target_col = prop_to_target.get(prop_type)
    
    # Filter to rows where target column exists and is not null (if target column exists)
    if target_col and target_col in df.columns:
        df = df[df[target_col].notna()].copy()
    # For Threes, we'll return all data and handle it in feature engineering
    
    return df
