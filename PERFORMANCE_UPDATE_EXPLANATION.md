# Performance Tracking: Old Model vs New Model

## Important Question: Did Yesterday's Performance Use the New Model?

**Short Answer: No, not automatically.**

## How Performance Tracking Works

### Current Process

1. **Predictions are generated** → Stored in `processed_props` table with:
   - `model_probability` (the prediction)
   - `expected_value`
   - `game_date` (when the game occurs)
   - `generated_at` (when the prediction was made)

2. **After games finish** → `track_outcomes.py` matches:
   - Props from `processed_props` table (with old predictions)
   - Actual game results
   - Records wins/losses in `bet_tracking` table

3. **Performance metrics** → Calculated from `bet_tracking` table

### The Problem

**Yesterday's predictions were made with the OLD model** (before improvements).

When `track_outcomes.py` runs, it:
- Looks up props in `processed_props` table
- These props have predictions made with the OLD model
- Tracks their outcomes
- Performance metrics reflect OLD model performance

## What This Means

### If You Deployed Model Improvements Today:
- ✅ **New predictions** (starting today) use the new model
- ❌ **Yesterday's predictions** were made with the old model
- ❌ **Performance metrics** for yesterday reflect old model performance

### To Get Accurate New Model Performance:

You have two options:

#### Option 1: Track Only New Predictions (Recommended)
- Let old predictions stay as-is
- Only track new predictions going forward
- Performance metrics will gradually reflect new model as more games are tracked
- **Pros**: Simple, no extra computation
- **Cons**: Mixed performance metrics (old + new model)

#### Option 2: Regenerate Historical Predictions (Expensive)
- Re-run predictions for all past props with the new model
- Update `processed_props` table with new predictions
- Then track outcomes
- **Pros**: Pure new model performance metrics
- **Cons**: Very computationally expensive, may take hours

## How to Check

### Check When Predictions Were Made

```sql
SELECT 
    DATE(generated_at) as prediction_date,
    COUNT(*) as num_predictions,
    MIN(generated_at) as first_prediction,
    MAX(generated_at) as last_prediction
FROM processed_props
WHERE game_date = CURRENT_DATE - INTERVAL '1 day'
GROUP BY DATE(generated_at);
```

This shows when yesterday's predictions were generated.

### Check Model Version

The model improvements were made in:
- `feature_engineering.py` - Enhanced features
- `modeling.py` - Optimized hyperparameters
- `main_workflow.py` - Uses new features

If predictions were generated **before** these files were updated, they use the old model.

## Recommendation

### For Immediate Use:
1. **Don't worry about yesterday's performance** - it reflects the old model
2. **New predictions** (starting now) will use the new model
3. **Performance metrics** will gradually improve as more new predictions are tracked

### For Accurate New Model Performance:
1. **Option A (Simple)**: Just track new predictions going forward
2. **Option B (Complete)**: Run a script to regenerate all recent predictions

## Script to Regenerate Recent Predictions

If you want to regenerate predictions for the last N days with the new model:

```python
# This would regenerate predictions for the last 7 days
from main_workflow import generate_betting_dataset
from save_to_database import save_props_to_database

# This will generate new predictions with the new model
# Note: This will create NEW rows in processed_props, not update old ones
df = generate_betting_dataset(filter_overs_only=True, min_games=10)
save_props_to_database(df)
```

**Warning**: This creates duplicate rows in `processed_props` (old predictions + new predictions).

## Bottom Line

**Yesterday's performance metrics reflect the OLD model** unless you:
1. Regenerated predictions after deploying model improvements
2. Or are tracking only new predictions going forward

**Going forward**, all new predictions will use the new model, and performance metrics will gradually reflect the new model's performance.
