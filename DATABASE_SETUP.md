# Database Setup for Tracking

## ✅ Database Tables Created

The database schema (`database_schema.sql`) includes two tables:

### 1. `processed_props` Table
Stores daily predictions with:
- All prop details (player, prop type, line, odds)
- Model predictions (probability, EV, confidence intervals)
- Kelly fraction, edge, etc.
- `game_date` field (currently NULL until game dates are extracted from API)
- `generated_at` timestamp

### 2. `bet_tracking` Table
Tracks outcomes and performance with:
- Links to `processed_props` via `prop_id`
- `outcome` (TRUE/FALSE/NULL) - whether prop hit
- `actual_result` - actual stat value from historical database
- `profit_loss` - calculated profit/loss based on odds
- `game_date` and `result_date`

## ✅ Automatic Tracking Setup

### Daily Workflow (GitHub Actions)

The `.github/workflows/daily-update.yml` workflow:
1. Runs daily at 8 AM EST
2. Executes `export_to_json.py` which:
   - Generates new predictions
   - Saves to `processed_props` table
   - **Tracks outcomes** for past games (calls `track_outcomes.py`)
   - **Exports performance JSON** for dashboard
3. Builds and deploys dashboard

### Manual Tracking

You can also manually track outcomes:
```powershell
python track_outcomes.py
```

This will:
- Process props from today that have already occurred
- Match them to historical game data
- Update `bet_tracking` table
- Generate `dashboard/public/data/performance.json`

## ⚠️ Important: Game Date Requirement

For automatic tracking to work, `game_date` must be populated in `processed_props`.

**Current Status:**
- `game_date` column exists in database
- FanDuel scraper does not currently extract game dates
- Props are saved with `game_date = NULL`

**Options:**
1. **Extract game dates from FanDuel API** (future enhancement)
2. **Set `game_date = date.today()`** when saving (works for same-day games)
3. **Leave NULL for now** - tracking will work once game dates are added

## How It Works

1. **Daily Predictions**: `export_to_json.py` saves new props to `processed_props`
2. **Outcome Tracking**: `track_outcomes.py` matches props to historical games
3. **Performance Metrics**: Calculated from `bet_tracking` table
4. **Dashboard Display**: Reads from `performance.json` (auto-generated)

## Database Connection

The database connection string is in:
- `database.py`
- `save_to_database.py`
- `track_outcomes.py`

All use the same Neon PostgreSQL connection string.
