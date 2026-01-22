"""
Save processed props to Neon database for dashboard access
"""
import pandas as pd
from database import get_db_connection
from datetime import datetime

def save_props_to_database(df: pd.DataFrame, table_name: str = 'processed_props'):
    """
    Save processed props dataframe to Neon database
    
    Args:
        df: DataFrame with processed props
        table_name: Name of table to save to (default: 'processed_props')
    """
    if len(df) == 0:
        print("No data to save to database")
        return
    
    conn = get_db_connection()
    try:
        # Convert DataFrame to list of tuples for insertion
        # Map column names to match database schema
        column_mapping = {
            'Player': 'player',
            'Prop': 'prop',
            'Line': 'line',
            'Over/Under': 'over_under',
            'Odds': 'odds',
            'Decimal_Odds': 'decimal_odds',
            'Implied_Probability': 'implied_probability',
            'Model_Probability': 'model_probability',
            'Probability_CI_Lower': 'probability_ci_lower',
            'Probability_CI_Upper': 'probability_ci_upper',
            'Edge': 'edge',
            'Expected_Value': 'expected_value',
            'EV_CI_Lower': 'ev_ci_lower',
            'EV_CI_Upper': 'ev_ci_upper',
            'Kelly_Fraction': 'kelly_fraction',
            'Confidence_Score': 'confidence_score',
            'Historical_Games': 'historical_games',
            'Training_Samples': 'training_samples',
            'Generated_At': 'generated_at'
        }
        
        # Prepare data for insertion
        insert_data = []
        for _, row in df.iterrows():
            record = {}
            for df_col, db_col in column_mapping.items():
                if df_col in row:
                    value = row[df_col]
                    # Convert timestamp string to datetime if needed
                    if df_col == 'Generated_At' and isinstance(value, str):
                        value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                    record[db_col] = value
            insert_data.append(record)
        
        # Build insert query
        columns = list(column_mapping.values())
        placeholders = ', '.join(['%s'] * len(columns))
        # Note: ON CONFLICT requires a unique constraint
        # For now, we'll just insert (you may want to add unique constraint on player+prop+line+generated_at)
        query = f"""
        INSERT INTO {table_name} ({', '.join(columns)})
        VALUES ({placeholders})
        """
        
        # Execute insertions
        cursor = conn.cursor()
        for record in insert_data:
            values = [record.get(col) for col in columns]
            cursor.execute(query, values)
        
        conn.commit()
        print(f"Successfully saved {len(insert_data)} props to database")
        
    except Exception as e:
        print(f"Error saving to database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def get_latest_props_from_database(limit: int = 1000) -> pd.DataFrame:
    """
    Get latest processed props from database
    
    Args:
        limit: Maximum number of records to return
    
    Returns:
        DataFrame with latest props
    """
    conn = get_db_connection()
    try:
        query = f"""
        SELECT * FROM processed_props
        ORDER BY generated_at DESC
        LIMIT {limit}
        """
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        print(f"Error fetching from database: {e}")
        raise
    finally:
        conn.close()
