"""
Main workflow for NBA betting dashboard
Combines live odds, historical data, modeling, and expected value calculation
"""
import pandas as pd
import numpy as np
from typing import Optional, List
import warnings
warnings.filterwarnings('ignore')

from fanduel_scraper import scrape_to_dataframe
from database import get_player_historical_data, get_table_schema
from feature_engineering import create_training_data, prepare_features_for_prediction
from modeling import PropPredictor
from expected_value import calculate_expected_value_from_american, american_to_decimal, calculate_kelly_criterion
from datetime import datetime
from save_to_database import save_props_to_database

def process_prop(row: pd.Series, filter_overs_only: bool = True, min_games: int = 10) -> Optional[dict]:
    """
    Process a single prop: get historical data, train model, predict probability, calculate EV
    
    Args:
        row: Row from odds dataframe with Player, Prop, Line, Over/Under, Odds
        filter_overs_only: If True, only process Over props
        min_games: Minimum number of historical games required
    
    Returns:
        Dictionary with prop info, probability, and expected value, or None if insufficient data
    """
    player_name = row['Player']
    prop_type = row['Prop']
    line = row['Line']
    over_under = row['Over/Under']
    odds = row['Odds']
    
    # Filter to overs only if requested
    if filter_overs_only and over_under != 'Over':
        return None
    
    # Skip if Over/Under is Unknown
    if over_under == 'Unknown':
        return None
    
    print(f"Processing: {player_name} - {prop_type} {over_under} {line} (Odds: {odds})")
    
    try:
        # Get historical data - ONLY for this specific player
        # The model is trained exclusively on this player's historical data
        historical_df = get_player_historical_data(player_name, prop_type)
        
        if len(historical_df) < min_games:
            print(f"  Insufficient data: {len(historical_df)} games (need {min_games})")
            return None
        
        # Create training data - ONLY from this player's historical games
        X, y = create_training_data(historical_df, prop_type, line, over_under)
        
        if len(X) == 0:
            print(f"  No valid training data after feature engineering")
            return None
        
        # Train model - ONLY on this player's data
        predictor = PropPredictor(model_type='random_forest')
        predictor.train(X, y)
        
        # Predict probability using most recent game features
        # Need to pass line to prepare_features_for_prediction
        from feature_engineering import prepare_features_for_prediction
        recent_features = prepare_features_for_prediction(historical_df.iloc[[-1]], prop_type, line=line)
        probability, prob_ci_lower, prob_ci_upper = predictor.predict_probability_with_ci(recent_features)
        
        # Calculate implied probability from odds FIRST (before final calibration)
        decimal_odds = american_to_decimal(odds)
        if not np.isnan(decimal_odds):
            implied_prob = 1 / decimal_odds
        else:
            implied_prob = np.nan
        
        # POST-CALIBRATION: Blend with implied probability if model is way off
        # This prevents assigning 75% probability to a +136 bet (which implies ~42%)
        if not np.isnan(implied_prob) and not np.isnan(probability):
            implied_prob = max(0.05, min(0.95, implied_prob))  # Clamp implied prob
            
            # If model probability is more than 25% different from implied, blend them
            # This is a sanity check - the market is usually pretty efficient
            prob_diff = abs(probability - implied_prob)
            if prob_diff > 0.25:
                # The bigger the difference, the more we trust the market
                # If model says 75% but market says 40%, blend heavily toward market
                blend_weight = min(0.5, prob_diff * 1.5)  # Up to 50% weight on market
                probability = (1 - blend_weight) * probability + blend_weight * implied_prob
                # Also adjust CI bounds proportionally
                if not np.isnan(prob_ci_lower):
                    prob_ci_lower = (1 - blend_weight) * prob_ci_lower + blend_weight * max(0.05, implied_prob - 0.10)
                if not np.isnan(prob_ci_upper):
                    prob_ci_upper = (1 - blend_weight) * prob_ci_upper + blend_weight * min(0.95, implied_prob + 0.10)
        
        # Final clamp to reasonable range [10%, 75%]
        probability = max(0.10, min(0.75, probability))
        if not np.isnan(prob_ci_lower):
            prob_ci_lower = max(0.05, min(0.70, prob_ci_lower))
        if not np.isnan(prob_ci_upper):
            prob_ci_upper = max(0.15, min(0.80, prob_ci_upper))
        
        # Calculate expected value (now accounts for market efficiency)
        ev = calculate_expected_value_from_american(probability, odds, implied_prob)
        
        # Calculate EV confidence intervals using probability bounds
        ev_lower = calculate_expected_value_from_american(prob_ci_lower, odds, implied_prob) if not np.isnan(prob_ci_lower) else np.nan
        ev_upper = calculate_expected_value_from_american(prob_ci_upper, odds, implied_prob) if not np.isnan(prob_ci_upper) else np.nan
        
        # Calculate edge (our probability - implied probability)
        edge = probability - implied_prob if not np.isnan(implied_prob) else np.nan
        
        # Calculate Kelly Criterion for optimal bet sizing
        kelly_fraction = calculate_kelly_criterion(probability, decimal_odds) if not np.isnan(decimal_odds) else 0.0
        
        # Calculate confidence/quality score (0-1)
        # Based on: sample size, CI width, and data quality
        ci_width = prob_ci_upper - prob_ci_lower if not (np.isnan(prob_ci_upper) or np.isnan(prob_ci_lower)) else 1.0
        sample_size_score = min(1.0, len(X) / 50.0)  # Normalize to 50 games = perfect score
        ci_score = max(0.0, 1.0 - ci_width)  # Narrower CI = higher score
        confidence_score = (sample_size_score * 0.6 + ci_score * 0.4)  # Weighted average
        
        result = {
            'Player': player_name,
            'Prop': prop_type,
            'Line': line,
            'Over/Under': over_under,
            'Odds': odds,
            'Decimal_Odds': decimal_odds,
            'Implied_Probability': implied_prob,
            'Model_Probability': probability,
            'Probability_CI_Lower': prob_ci_lower,
            'Probability_CI_Upper': prob_ci_upper,
            'Edge': edge,
            'Expected_Value': ev,
            'EV_CI_Lower': ev_lower,
            'EV_CI_Upper': ev_upper,
            'Kelly_Fraction': kelly_fraction,  # Optimal bet size as fraction of bankroll
            'Confidence_Score': confidence_score,  # Data quality score (0-1)
            'Historical_Games': len(historical_df),
            'Training_Samples': len(X)
        }
        
        print(f"  Probability: {probability:.3f} (95% CI: [{prob_ci_lower:.3f}, {prob_ci_upper:.3f}]), "
              f"EV: {ev:.3f} (95% CI: [{ev_lower:.3f}, {ev_upper:.3f}]), Edge: {edge:.3f}")
        
        return result
        
    except Exception as e:
        print(f"  Error processing prop: {e}")
        return None

def generate_betting_dataset(filter_overs_only: bool = True, 
                            min_games: int = 10,
                            max_props: Optional[int] = None,
                            debug: bool = False) -> pd.DataFrame:
    """
    Main function to generate complete betting dataset
    
    Args:
        filter_overs_only: If True, only process Over props (saves compute)
        min_games: Minimum historical games required
        max_props: Maximum number of props to process (None = all)
        debug: Enable debug mode for scraper
    
    Returns:
        DataFrame with all props, probabilities, and expected values
    """
    print("="*60)
    print("NBA BETTING DASHBOARD - Data Generation")
    print("="*60)
    
    # Step 1: Get live odds
    print("\n[Step 1/4] Fetching live odds from FanDuel...")
    odds_df = scrape_to_dataframe(debug=debug)
    print(f"Found {len(odds_df)} props")
    
    if len(odds_df) == 0:
        print("No props found. Exiting.")
        return pd.DataFrame()
    
    # Filter to overs if requested
    if filter_overs_only:
        odds_df = odds_df[odds_df['Over/Under'] == 'Over'].copy()
        print(f"Filtered to {len(odds_df)} Over props")
    
    # Limit number of props if specified
    if max_props:
        odds_df = odds_df.head(max_props)
        print(f"Processing first {max_props} props")
    
    # Step 2: Process each prop
    print(f"\n[Step 2/4] Processing {len(odds_df)} props...")
    results = []
    
    for idx, row in odds_df.iterrows():
        result = process_prop(row, filter_overs_only=filter_overs_only, min_games=min_games)
        if result:
            results.append(result)
    
    if len(results) == 0:
        print("\nNo props successfully processed. Check data availability.")
        return pd.DataFrame()
    
    # Step 3: Create final dataset
    print(f"\n[Step 3/4] Creating final dataset from {len(results)} processed props...")
    final_df = pd.DataFrame(results)
    
    # Add timestamp
    final_df['Generated_At'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Step 4: Sort by expected value (best bets first)
    # Use Kelly-adjusted EV to avoid bias toward high-odds bets
    # This normalizes for risk and gives fair comparison across odds ranges
    print(f"\n[Step 4/4] Sorting by Kelly-adjusted expected value...")
    
    # Calculate Kelly-adjusted score with stronger penalty for high-variance bets
    # Formula: EV * (Kelly_Fraction^1.5) - this penalizes high-odds bets more aggressively
    # The exponent > 1 means bets with lower Kelly fractions (higher variance) get penalized more
    kelly_clipped = final_df['Kelly_Fraction'].clip(lower=0, upper=1)
    final_df['Kelly_Adjusted_EV'] = final_df['Expected_Value'] * (kelly_clipped ** 1.5)
    
    # Sort by Kelly-adjusted EV, then by raw EV as tiebreaker
    final_df = final_df.sort_values(
        ['Kelly_Adjusted_EV', 'Expected_Value'], 
        ascending=[False, False], 
        na_position='last'
    )
    
    # Add some summary statistics
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total props processed: {len(final_df)}")
    print(f"Props with positive EV: {len(final_df[final_df['Expected_Value'] > 0])}")
    print(f"Props with EV > 5%: {len(final_df[final_df['Expected_Value'] > 0.05])}")
    print(f"Props with EV > 10%: {len(final_df[final_df['Expected_Value'] > 0.10])}")
    
    if len(final_df) > 0:
        print(f"\nData Quality:")
        print(f"  Average confidence score: {final_df['Confidence_Score'].mean():.3f}")
        print(f"  Average training samples: {final_df['Training_Samples'].mean():.1f}")
        print(f"  Average historical games: {final_df['Historical_Games'].mean():.1f}")
        print(f"\nBet Sizing (Kelly Criterion):")
        print(f"  Props with Kelly > 0: {len(final_df[final_df['Kelly_Fraction'] > 0])}")
        print(f"  Average Kelly fraction: {final_df[final_df['Kelly_Fraction'] > 0]['Kelly_Fraction'].mean():.3f}" if len(final_df[final_df['Kelly_Fraction'] > 0]) > 0 else "  No positive Kelly bets")
    
    if len(final_df) > 0:
        print(f"\nTop 5 bets by Expected Value:")
        display_cols = ['Player', 'Prop', 'Line', 'Over/Under', 'Odds', 
                       'Model_Probability', 'Probability_CI_Lower', 'Probability_CI_Upper',
                       'Expected_Value', 'EV_CI_Lower', 'EV_CI_Upper', 'Kelly_Fraction', 'Confidence_Score']
        # Only show columns that exist
        available_cols = [col for col in display_cols if col in final_df.columns]
        top_5 = final_df.head(5)[available_cols]
        print(top_5.to_string(index=False))
    
    return final_df

if __name__ == "__main__":
    # Generate the dataset
    df = generate_betting_dataset(
        filter_overs_only=True,  # Only process Over props to save compute
        min_games=10,            # Require at least 10 historical games
        max_props=None,          # Process all props (set to number to limit)
        debug=False
    )
    
    # Save to CSV
    if len(df) > 0:
        output_file = 'betting_dataset.csv'
        df.to_csv(output_file, index=False)
        print(f"\nDataset saved to {output_file}")
        
        # Save to database for dashboard
        try:
            print("\nSaving to database...")
            save_props_to_database(df)
            print("Database save complete!")
        except Exception as e:
            print(f"Warning: Could not save to database: {e}")
            print("CSV file is still available.")
    else:
        print("\nNo data to save.")
