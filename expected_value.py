"""
Expected value calculation module
"""
import numpy as np
from typing import Union

def american_to_decimal(american_odds: Union[int, str]) -> float:
    """
    Convert American odds to decimal odds
    
    Args:
        american_odds: American odds (e.g., -110, +150, 'OFF')
    
    Returns:
        Decimal odds (e.g., 1.91 for -110)
    """
    if isinstance(american_odds, str):
        if american_odds == 'OFF' or american_odds == '':
            return np.nan
        try:
            american_odds = int(american_odds)
        except:
            return np.nan
    
    if np.isnan(american_odds):
        return np.nan
    
    if american_odds > 0:
        # Positive odds: (odds / 100) + 1
        return (american_odds / 100) + 1
    else:
        # Negative odds: (100 / abs(odds)) + 1
        return (100 / abs(american_odds)) + 1

def calculate_expected_value(probability: float, decimal_odds: float, implied_probability: float = None) -> float:
    """
    Calculate expected value of a bet, accounting for market efficiency
    
    Since prop odds are usually accurate, we adjust EV based on how much our
    probability differs from the market-implied probability. When there's a large
    discrepancy, we weight the calculation more toward market efficiency.
    
    EV = (probability * (decimal_odds - 1)) - (1 - probability)
    
    With market adjustment: If our probability differs significantly from implied,
    we use a weighted average that trusts the market more when discrepancies are large.
    
    Args:
        probability: Our model's probability of winning (0-1)
        decimal_odds: Decimal odds (e.g., 1.91 for -110)
        implied_probability: Market-implied probability from odds (optional, calculated if not provided)
    
    Returns:
        Expected value as a percentage (positive = good bet, negative = bad bet)
    """
    if np.isnan(probability) or np.isnan(decimal_odds):
        return np.nan
    
    # Calculate implied probability if not provided
    if implied_probability is None or np.isnan(implied_probability):
        implied_probability = 1.0 / decimal_odds
    
    # Base EV calculation
    base_ev = (probability * (decimal_odds - 1)) - ((1 - probability) * 1)
    
    # Market-adjusted EV: Account for market efficiency
    # When our probability differs significantly from implied, adjust EV
    # Prop odds are usually accurate, so large discrepancies suggest we may be wrong
    prob_diff = abs(probability - implied_probability)
    
    if prob_diff > 0.15:  # Significant discrepancy (>15%)
        # Calculate EV using implied probability (market view)
        market_ev = (implied_probability * (decimal_odds - 1)) - ((1 - implied_probability) * 1)
        
        # Weight: The larger the discrepancy, the more we trust the market
        # For discrepancies > 25%, we trust market 40%; for 15-25%, we trust market 20%
        market_weight = min(0.40, (prob_diff - 0.15) * 2.0)  # 0% at 15% diff, up to 40% at 25%+ diff
        
        # Blend our EV with market EV
        adjusted_ev = (1 - market_weight) * base_ev + market_weight * market_ev
        return adjusted_ev
    
    # Small discrepancy: Use our probability directly
    return base_ev

def calculate_expected_value_from_american(probability: float, american_odds: Union[int, str], implied_probability: float = None) -> float:
    """
    Calculate expected value from probability and American odds, accounting for market efficiency
    
    Args:
        probability: Our model's probability of winning (0-1)
        american_odds: American odds (e.g., -110, +150, 'OFF')
        implied_probability: Market-implied probability (optional, calculated if not provided)
    
    Returns:
        Expected value as a percentage
    """
    decimal_odds = american_to_decimal(american_odds)
    if np.isnan(decimal_odds):
        return np.nan
    
    # Calculate implied probability if not provided
    if implied_probability is None or np.isnan(implied_probability):
        implied_probability = 1.0 / decimal_odds
    
    return calculate_expected_value(probability, decimal_odds, implied_probability)

def calculate_kelly_criterion(probability: float, decimal_odds: float) -> float:
    """
    Calculate Kelly Criterion bet size
    
    f = (bp - q) / b
    where:
        f = fraction of bankroll to bet
        b = decimal odds - 1
        p = probability of winning
        q = probability of losing (1 - p)
    
    Args:
        probability: Probability of winning (0-1)
        decimal_odds: Decimal odds
    
    Returns:
        Kelly fraction (0-1), or 0 if negative
    """
    if np.isnan(probability) or np.isnan(decimal_odds):
        return 0.0
    
    b = decimal_odds - 1
    p = probability
    q = 1 - p
    
    kelly = (b * p - q) / b
    
    # Only bet if positive
    return max(0.0, kelly)
