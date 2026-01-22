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

def calculate_expected_value(probability: float, decimal_odds: float) -> float:
    """
    Calculate expected value of a bet
    
    EV = (probability * (decimal_odds - 1)) - (1 - probability)
    
    Args:
        probability: Probability of winning (0-1)
        decimal_odds: Decimal odds (e.g., 1.91 for -110)
    
    Returns:
        Expected value as a percentage (positive = good bet, negative = bad bet)
    """
    if np.isnan(probability) or np.isnan(decimal_odds):
        return np.nan
    
    # EV = (win_prob * net_profit) - (lose_prob * stake)
    # If we bet $1: win = (odds - 1), lose = -1
    ev = (probability * (decimal_odds - 1)) - ((1 - probability) * 1)
    
    return ev

def calculate_expected_value_from_american(probability: float, american_odds: Union[int, str]) -> float:
    """
    Calculate expected value from probability and American odds
    
    Args:
        probability: Probability of winning (0-1)
        american_odds: American odds (e.g., -110, +150, 'OFF')
    
    Returns:
        Expected value as a percentage
    """
    decimal_odds = american_to_decimal(american_odds)
    return calculate_expected_value(probability, decimal_odds)

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
