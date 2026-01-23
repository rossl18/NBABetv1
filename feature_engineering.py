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
    Prepare feature set for model prediction with enhanced feature engineering
    
    The database already has engineered features (feat_roll_pts_5, etc.)
    We'll use those plus additional sophisticated features we can create.
    
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
    
    # Find the relevant stat column for this prop type
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
    for keyword in stat_keywords:
        matching_cols = [col for col in result_df.columns if keyword.lower() in col.lower() 
                        and 'target' not in col.lower() and 'feat' not in col.lower()]
        if matching_cols:
            stat_column = matching_cols[0]
            break
    
    # Enhanced feature engineering
    if stat_column and stat_column in features_df.columns and len(features_df) > 0:
        stats = features_df[stat_column].values
        
        # Calculate rolling statistics if we have enough data
        if len(stats) >= 5:
            # Recent averages
            recent_5_avg = np.mean(stats[-5:]) if len(stats) >= 5 else np.nan
            recent_10_avg = np.mean(stats[-10:]) if len(stats) >= 10 else np.nan
            season_avg = np.mean(stats) if len(stats) > 0 else np.nan
            
            # Recent standard deviation
            recent_10_std = np.std(stats[-10:]) if len(stats) >= 10 else np.nan
            
            # Add line context features if line is provided
            if line is not None and not np.isnan(line):
                result_df['line'] = line
                
                # Line vs recent performance
                if not np.isnan(recent_5_avg):
                    result_df['line_vs_recent_5'] = line - recent_5_avg
                    result_df['line_vs_recent_5_pct'] = (line - recent_5_avg) / max(recent_5_avg, 0.1)
                
                if not np.isnan(recent_10_avg):
                    result_df['line_vs_recent_10'] = line - recent_10_avg
                    result_df['line_vs_recent_10_pct'] = (line - recent_10_avg) / max(recent_10_avg, 0.1)
                
                # Line vs season average
                if not np.isnan(season_avg):
                    result_df['line_vs_season_avg'] = line - season_avg
                    result_df['line_vs_season_avg_pct'] = (line - season_avg) / max(season_avg, 0.1)
                
                # Line difficulty (normalized by volatility)
                if not np.isnan(recent_10_std) and recent_10_std > 0:
                    result_df['line_difficulty'] = (line - recent_10_avg) / recent_10_std
                
                # Historical hit rate at similar lines (within ±1.5 of current line)
                if len(stats) >= 5:
                    similar_line_mask = np.abs(stats - line) <= 1.5
                    if similar_line_mask.sum() > 0:
                        # For training, we'll calculate this per row in create_training_data
                        # For prediction, use recent games
                        recent_similar = np.abs(stats[-10:] - line) <= 1.5
                        if recent_similar.sum() > 0:
                            result_df['recent_similar_line_count'] = recent_similar.sum()
                        else:
                            result_df['recent_similar_line_count'] = 0
                    else:
                        result_df['recent_similar_line_count'] = 0
            
            # Trend features
            if len(stats) >= 5:
                # Trend: slope of last 5 games
                recent_5 = stats[-5:]
                x = np.arange(len(recent_5))
                if len(recent_5) > 1 and np.std(x) > 0:
                    trend_5 = np.polyfit(x, recent_5, 1)[0]  # Slope
                    result_df['trend_5_games'] = trend_5
                else:
                    result_df['trend_5_games'] = 0
            
            if len(stats) >= 6:
                # Momentum: change from previous 3 to last 3
                prev_3_avg = np.mean(stats[-6:-3]) if len(stats) >= 6 else np.nan
                last_3_avg = np.mean(stats[-3:])
                if not np.isnan(prev_3_avg) and prev_3_avg > 0:
                    result_df['momentum'] = (last_3_avg - prev_3_avg) / prev_3_avg
                else:
                    result_df['momentum'] = 0
            
            # Volatility
            if not np.isnan(recent_10_std):
                result_df['volatility'] = recent_10_std
            
            # Consistency score (1 - coefficient of variation)
            if not np.isnan(recent_10_avg) and recent_10_avg > 0 and not np.isnan(recent_10_std):
                result_df['consistency_score'] = 1 - (recent_10_std / recent_10_avg)
            else:
                result_df['consistency_score'] = 0.5
            
            # Recent vs season performance
            if not np.isnan(season_avg) and season_avg > 0:
                if not np.isnan(recent_5_avg):
                    result_df['recent_vs_season_5'] = (recent_5_avg - season_avg) / season_avg
                if not np.isnan(recent_10_avg):
                    result_df['recent_vs_season_10'] = (recent_10_avg - season_avg) / season_avg
            
            # Interaction features (if line is provided)
            if line is not None and not np.isnan(line):
                if not np.isnan(recent_5_avg):
                    result_df['rolling_5_x_line'] = recent_5_avg * line
                    result_df['line_div_rolling_5'] = line / max(recent_5_avg, 0.1)
                if not np.isnan(recent_10_std) and recent_10_std > 0:
                    result_df['volatility_x_line'] = recent_10_std * line
        
        # Fill NaN values with 0 for new features
        new_feature_cols = [col for col in result_df.columns if col not in feature_cols]
        for col in new_feature_cols:
            result_df[col] = result_df[col].fillna(0)
    else:
        # Fallback: just add line if provided
        if line is not None:
            result_df['line'] = line
    
    # Final safety: ensure no NaNs leak into modeling/prediction
    result_df = result_df.fillna(0)

    return result_df

def create_training_data(df: pd.DataFrame, prop_type: str, line: float, over_under: str, 
                         use_time_weighting: bool = True) -> tuple:
    """
    Create complete training dataset with features and target
    
    Args:
        df: Historical dataframe
        prop_type: Type of prop
        line: Line value
        over_under: 'Over' or 'Under'
        use_time_weighting: If True, add sample weights (recent games weighted more)
    
    Returns:
        Tuple of (X_features, y_target, sample_weights) DataFrames/Series
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
    
    # Calculate historical hit rate at similar lines for each row
    # This helps the model understand line context
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
    for keyword in stat_keywords:
        matching_cols = [col for col in df.columns if keyword.lower() in col.lower() 
                        and 'target' not in col.lower() and 'feat' not in col.lower()]
        if matching_cols:
            stat_column = matching_cols[0]
            break
    
    if stat_column and stat_column in df.columns:
        # Calculate historical hit rate at similar lines for each training sample
        stats = df[stat_column].values
        similar_line_hit_rates = []
        
        for i in range(len(stats)):
            # For each historical game, calculate hit rate at similar lines in previous games
            if i > 0:
                prev_stats = stats[:i]
                prev_targets = y.iloc[:i].values
                # Find games with similar lines (within ±1.5)
                similar_mask = np.abs(prev_stats - line) <= 1.5
                if similar_mask.sum() > 0:
                    hit_rate = prev_targets[similar_mask].mean()
                    similar_line_hit_rates.append(hit_rate)
                else:
                    similar_line_hit_rates.append(0.5)  # Default to 50% if no similar lines
            else:
                similar_line_hit_rates.append(0.5)  # First game has no history
        
        X['historical_hit_rate_similar_line'] = similar_line_hit_rates
    
    # Align indices
    common_idx = X.index.intersection(y.index)
    X = X.loc[common_idx]
    y = y.loc[common_idx]
    
    # Remove rows with NaN in features
    valid_mask = ~X.isna().any(axis=1)
    X = X[valid_mask]
    y = y[valid_mask]
    
    # Create sample weights (time-based weighting: recent games weighted more)
    sample_weights = None
    if use_time_weighting and len(X) > 0:
        # Weight recent games more heavily using exponential decay
        # Most recent game gets weight 1.0, older games get progressively less
        n = len(X)
        decay_rate = 0.05  # Adjust this to control how quickly weights decay
        # Reverse order: most recent = index n-1, oldest = index 0
        weights = np.exp(-decay_rate * np.arange(n)[::-1])
        # Normalize so max weight is 1.0
        weights = weights / weights.max()
        sample_weights = pd.Series(weights, index=X.index)
    else:
        sample_weights = pd.Series(np.ones(len(X)), index=X.index)
    
    return X, y, sample_weights
