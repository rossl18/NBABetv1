# Bet Tracking System - Ready to Go

## ✅ Status: Ready (Starting from Today)

The bet tracking system is configured and ready to track outcomes starting from **today onward**. No historical data will be processed.

## How It Works

### 1. **Track Outcomes Script** (`track_outcomes.py`)

This script:
- ✅ Queries `processed_props` for props with `game_date >= today` that have already occurred
- ✅ Matches each prop to historical game data in `nba_ml_training_set`
- ✅ Determines if the prop hit (Over: actual > line, Under: actual < line)
- ✅ Updates `bet_tracking` table with outcomes, actual stats, and profit/loss
- ✅ Generates performance metrics JSON for the dashboard

### 2. **Default Behavior**

By default, the script:
- **Only processes props from today forward** (no historical backfill)
- Only processes props where `game_date <= today` (games that have already happened)
- Skips props that have already been tracked

### 3. **Running the Script**

```powershell
python track_outcomes.py
```

This will:
1. Process any props from today that have game_date set and have already occurred
2. Generate performance metrics
3. Export `dashboard/public/data/performance.json`

## Important Notes

### ⚠️ Game Date Requirement

**The `game_date` field must be populated in `processed_props` for tracking to work.**

Currently:
- The `game_date` column exists in the database schema
- The FanDuel scraper does not currently extract game dates
- Props saved to the database will have `game_date = NULL` unless you:
  - Extract game dates from the FanDuel API (future enhancement)
  - Set `game_date` manually when saving props
  - Use `generated_at` date as a proxy (not ideal, but works for same-day games)

### Quick Fix: Set game_date to today for now

If you want to start tracking immediately, you can modify `save_to_database.py` to set `game_date = date.today()` for all props (assuming they're for today's games).

## Integration with Daily Workflow

To automatically track outcomes daily, add to your workflow:

```python
# In export_to_json.py or your daily script:
from track_outcomes import process_past_props, export_performance_json

# After saving props to database:
process_past_props(start_date=date.today())  # Track today's games
export_performance_json()  # Update dashboard JSON
```

## Performance Metrics Generated

The script generates:
- Total bets, wins, losses, win rate
- Total profit and ROI
- Performance by prop type
- Cumulative profit over time

All metrics are exported to `dashboard/public/data/performance.json` for the dashboard to consume.

## Testing

To test the system:
1. Ensure you have props in `processed_props` with `game_date` set
2. Ensure those games have already occurred (game_date <= today)
3. Run: `python track_outcomes.py`
4. Check `bet_tracking` table for updated records
5. Check `dashboard/public/data/performance.json` for metrics

## Future Enhancements

1. **Extract game_date from FanDuel API** - Add game date extraction to scraper
2. **Automatic daily tracking** - Add to GitHub Actions workflow
3. **Backfill historical data** - Use `process_past_props(days_back=N)` when ready
