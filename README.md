# NBA Betting Dashboard

A comprehensive system for analyzing NBA player props by combining live odds from FanDuel with historical data to calculate expected values.

## Overview

This system:
1. **Scrapes live odds** from FanDuel for upcoming NBA games
2. **Queries historical data** from a Neon PostgreSQL database
3. **Trains machine learning models** on historical data for each prop
4. **Predicts probabilities** of props hitting
5. **Calculates expected values** to identify profitable betting opportunities

## Setup

### 1. Install Dependencies

**On Windows PowerShell**, use:
```powershell
python -m pip install -r requirements.txt
```

**Note**: If `pip` command is not found, always use `python -m pip` instead.

### 2. Inspect Database (Recommended First Step)

Before running the main workflow, inspect your database structure to ensure column mappings are correct:

```powershell
python inspect_database.py
```

This will show you:
- Database schema (column names and types)
- Sample data
- Available prop types and player names

**Important**: After inspecting, you may need to update `feature_engineering.py` to match your actual database column names.

### 3. Update Column Mappings (If Needed)

If your database uses different column names, edit `feature_engineering.py` and update the mappings in:
- `prop_column_map` in `create_target_variable()`
- `stat_column_map` in `prepare_features_for_prediction()`

## Usage

### Generate Betting Dataset

Run the main workflow to generate a complete dataset with probabilities and expected values:

```powershell
python main_workflow.py
```

This will:
1. Fetch live odds from FanDuel
2. Process each prop (by default, only "Over" props to save compute)
3. Train models and predict probabilities
4. Calculate expected values
5. Save results to `betting_dataset.csv`

### Configuration Options

Edit `main_workflow.py` to customize:

```python
df = generate_betting_dataset(
    filter_overs_only=True,  # Only process Over props (set False for all)
    min_games=10,            # Minimum historical games required
    max_props=None,          # Limit number of props (None = all)
    debug=False              # Enable debug mode
)
```

### Individual Components

You can also use components separately:

```python
# Get live odds
from fanduel_scraper import scrape_to_dataframe
odds_df = scrape_to_dataframe()

# Query historical data
from database import get_player_historical_data
historical_df = get_player_historical_data("LeBron James", "Points")

# Train model and predict
from feature_engineering import create_training_data
from modeling import PropPredictor
from expected_value import calculate_expected_value_from_american

X, y, sample_weights = create_training_data(historical_df, "Points", 25.5, "Over", use_time_weighting=True)
predictor = PropPredictor(model_type='random_forest')
predictor.train(X, y, sample_weight=sample_weights)
probability = predictor.predict_probability(X.iloc[[-1]])
ev = calculate_expected_value_from_american(probability, -110)
```

## Output

The `betting_dataset.csv` file contains:

- **Player**: Player name
- **Prop**: Prop type (Points, Rebounds, etc.)
- **Line**: The line value
- **Over/Under**: Over or Under
- **Odds**: American odds
- **Decimal_Odds**: Converted decimal odds
- **Implied_Probability**: Probability implied by the odds
- **Model_Probability**: Model's predicted probability
- **Edge**: Difference between model and implied probability
- **Expected_Value**: Expected value of the bet (positive = good bet)
- **Historical_Games**: Number of historical games used
- **Training_Samples**: Number of training samples

## File Structure

```
NBABetv1/
├── fanduel_scraper.py      # Scrapes live odds from FanDuel
├── database.py              # Database connection and queries
├── feature_engineering.py   # Feature creation and target variable
├── modeling.py              # ML model training and prediction
├── expected_value.py        # EV calculations
├── main_workflow.py         # Main workflow (run this)
├── inspect_database.py      # Database inspection tool
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Expected Value Explained

**Expected Value (EV)** = (Probability × Net Profit) - (1 - Probability) × Stake

- **Positive EV**: Profitable bet in the long run
- **Negative EV**: Unprofitable bet
- **EV > 0.05 (5%)**: Good value bet
- **EV > 0.10 (10%)**: Excellent value bet

## Troubleshooting

### Database Connection Issues
- Verify the connection string in `database.py`
- Check that your IP is whitelisted (if required by Neon)

### Column Name Mismatches
- Run `inspect_database.py` to see actual column names
- Update mappings in `feature_engineering.py`

### Insufficient Data
- Some props may be skipped if player has < 10 historical games
- Adjust `min_games` parameter if needed

### Model Training Issues
- If all outcomes are the same (e.g., player always hits), model uses baseline probability
- Check that your historical data has variation

## Next Steps

1. **Run database inspection** to understand your data structure
2. **Update column mappings** if needed
3. **Run main workflow** to generate dataset
4. **Review results** and adjust parameters
5. **Build dashboard** (future enhancement) to visualize results

## Notes

- The system processes props sequentially (can be slow for many props)
- Consider using `max_props` parameter for testing
- Model retrains for each prop (could be optimized with pre-trained models)
- Only processes "Over" props by default to save compute time
