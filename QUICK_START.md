# Quick Start Guide

## Step 1: Install Dependencies (If Not Done)

```powershell
python -m pip install -r requirements.txt
```

**Note**: On Windows, use `python -m pip` instead of just `pip`.

## Step 2: Test Database Connection

```powershell
python test_connection.py
```

This verifies you can connect to the Neon database.

## Step 3: Inspect Database Structure

```powershell
python inspect_database.py
```

This shows you:
- What columns exist in your database
- Sample data structure
- Available prop types

**Important**: After this step, you may need to update column mappings in `feature_engineering.py` if your column names differ.

## Step 4: Update Column Mappings (If Needed)

Open `feature_engineering.py` and check these mappings:

1. **Line 15-23**: `prop_column_map` - Maps prop types to stat columns
   - Example: `'Points': 'points'` means Points prop uses 'points' column
   - Update if your columns are named differently

2. **Line 45-52**: `stat_column_map` - Maps prop types to stat columns for features
   - Similar to above, update if needed

## Step 5: Run Main Workflow

```powershell
python main_workflow.py
```

This will:
- Fetch live odds (takes ~30-60 seconds)
- Process each prop (can take several minutes)
- Generate `betting_dataset.csv` with results

## Step 6: Review Results

Open `betting_dataset.csv` and sort by `Expected_Value` to see best bets.

## Common Issues

### "Could not find column for prop type"
- Your database column names don't match the mappings
- Run `inspect_database.py` to see actual column names
- Update `feature_engineering.py` mappings

### "Insufficient data"
- Player doesn't have enough historical games
- Lower `min_games` parameter in `main_workflow.py` (default is 10)

### Database connection fails
- Check connection string in `database.py`
- Verify network connectivity
- Check if IP whitelisting is required

## Customization

### Process All Props (Not Just Overs)

In `main_workflow.py`, change:
```python
df = generate_betting_dataset(filter_overs_only=False)
```

### Limit Number of Props (For Testing)

In `main_workflow.py`, change:
```python
df = generate_betting_dataset(max_props=10)  # Only process 10 props
```

### Change Minimum Games Required

In `main_workflow.py`, change:
```python
df = generate_betting_dataset(min_games=5)  # Require only 5 games
```
