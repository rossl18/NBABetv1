"""
Feature engineering module for creating target variables and features from historical data
"""
import pandas as pd
import numpy as np
from typing import Dict, Any

def create_target_variable(df: pd.DataFrame, prop_type: str, line: float, over_under: str) -> pd.Series:
    """
    Create target variable (binary: 1 if prop hit, 0 if not) based on historical data
    
    The database has target columns (target_pts, target_reb, etc.) but these are for 
    different lines. We need to check if we have raw stat columns, or use a different approach.
    
    Args:
        df: Historical dataframe with player stats
        prop_type: Type of prop (Points, Rebounds, Assists, Threes, etc.)
        line: The line value for the prop
        over_under: 'Over' or 'Under'
    
    Returns:
        Series with binary target (1 if hit, 0 if not)
    """
    # First, try to find raw stat columns
    prop_to_stat = {
        'Points': ['pts', 'points', 'point'],
        'Rebounds': ['reb', 'rebounds', 'rebound'],
        'Assists': ['ast', 'assists', 'assist'],
        'Threes': ['3p', 'threes', 'three', '3pm', '3p_made'],
        'Made Threes': ['3p', 'threes', 'three', '3pm', '3p_made'],
        'Steals': ['stl', 'steals', 'steal'],
        'Blocks': ['blk', 'blocks', 'block']
    }
    
    stat_keywords = prop_to_stat.get(prop_type, [prop_type.lower()])
    stat_column = None
    
    # Look for stat column
    for keyword in stat_keywords:
        matching_cols = [col for col in df.columns if keyword.lower() in col.lower() 
                        and 'target' not in col.lower() and 'feat' not in col.lower()]
        if matching_cols:
            stat_column = matching_cols[0]
            break
    
    if stat_column and stat_column in df.columns:
        # We have raw stats - calculate target based on line
        actual_value = df[stat_column]
        if over_under == 'Over':
            target = (actual_value > line).astype(int)
        elif over_under == 'Under':
            target = (actual_value < line).astype(int)
        else:
            raise ValueError(f"over_under must be 'Over' or 'Under', got: {over_under}")
        return target
    else:
        # No raw stats found - use target column as proxy (but note: it's for different lines)
        # This is a fallback - ideally we'd have raw stats
        prop_to_target = {
            'Points': 'target_pts',
            'Rebounds': 'target_reb',
            'Assists': 'target_ast',
            'Threes': 'target_stl',  # May need adjustment
            'Made Threes': 'target_stl',
            'Steals': 'target_stl',
            'Blocks': 'target_blk'
        }
        
        target_col = prop_to_target.get(prop_type)
        if target_col and target_col in df.columns:
            # Use existing target - ensure it's binary (0/1)
            target = df[target_col].astype(float)
            # Convert to binary: any value > 0 becomes 1, else 0
            target = (target > 0).astype(int)
            return target
        else:
            raise ValueError(f"Could not find stat or target column for prop type: {prop_type}. "
                          f"Available columns: {list(df.columns)}")

def prepare_features_for_prediction(df: pd.DataFrame, prop_type: str, line: float = None) -> pd.DataFrame:
    """
    Prepare feature set for model prediction
    
    The database already has engineered features (feat_roll_pts_5, etc.)
    We'll use those plus any additional features we can create.
    
    Args:
        df: Historical dataframe
        prop_type: Type of prop
        line: Line value (optional, will be added as feature if provided)
    
    Returns:
        DataFrame with features ready for modeling
    """
    # Create a copy to avoid modifying original
    features_df = df.copy()
    
    # Sort by date (most recent first, then reverse for rolling calculations)
    if 'game_date' in features_df.columns:
        features_df = features_df.sort_values(by='game_date').reset_index(drop=True)
    
    # The database already has features like feat_roll_pts_5, feat_roll_reb_5, etc.
    # We'll use all feature columns (those starting with 'feat_')
    # Plus we can add the line value as a feature
    
    # Select feature columns (all feat_ columns plus other numeric features)
    # Exclude identifier and target columns
    exclude_cols = ['player_full_name', 'player_name', 'game_id', 'game_date', 
                   'target_pts', 'target_reb', 'target_ast', 'target_blk', 'target_stl']
    
    # Get all columns that start with 'feat_' or are numeric
    feature_cols = []
    for col in features_df.columns:
        if col not in exclude_cols:
            if col.startswith('feat_'):
                feature_cols.append(col)
            elif features_df[col].dtype in [np.float64, np.int64, np.float32, np.int32, np.float16, np.int16]:
                # Include other numeric columns (like is_home)
                feature_cols.append(col)
    
    if len(feature_cols) == 0:
        raise ValueError(f"No feature columns found. Available columns: {list(features_df.columns)}")
    
    result_df = features_df[feature_cols].copy()
    
    # Add line as a feature if provided (important for prediction)
    if line is not None:
        result_df['line'] = line
    
    return result_df

def create_training_data(df: pd.DataFrame, prop_type: str, line: float, over_under: str) -> tuple:
    """
    Create complete training dataset with features and target
    
    Args:
        df: Historical dataframe
        prop_type: Type of prop
        line: Line value
        over_under: 'Over' or 'Under'
    
    Returns:
        Tuple of (X_features, y_target) DataFrames
    """
    # Create target variable
    y = create_target_variable(df, prop_type, line, over_under)
    
    # Ensure target is binary (0/1)
    unique_values = y.unique()
    if len(unique_values) > 2:
        # Convert to binary: any value > 0 becomes 1, else 0
        y = (y > 0).astype(int)
    else:
        # Ensure it's integer type
        y = y.astype(int)
    
    # Prepare features (include line for each historical row)
    # For training, we use the same line for all rows (the current line we're predicting)
    X = prepare_features_for_prediction(df, prop_type, line=line)
    
    # Align indices
    common_idx = X.index.intersection(y.index)
    X = X.loc[common_idx]
    y = y.loc[common_idx]
    
    # Remove rows with NaN in features
    valid_mask = ~X.isna().any(axis=1)
    X = X[valid_mask]
    y = y[valid_mask]
    
    return X, y
