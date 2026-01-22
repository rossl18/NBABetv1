# Dashboard Setup Guide

## Overview

Your dashboard is ready! Here's how to set it up and deploy to GitHub Pages.

## Step 1: Create Database Tables

Run the SQL script in Neon to create the tables:

```bash
# Connect to your Neon database and run:
psql 'your-connection-string' -f database_schema.sql
```

Or copy the contents of `database_schema.sql` and run it in your Neon SQL editor.

## Step 2: Set Up Dashboard

1. **Install Node.js** (if not already installed)

2. **Install dashboard dependencies:**
```bash
cd dashboard
npm install
```

3. **Update GitHub repo name** in `dashboard/vite.config.js`:
   - Change `base: '/NBABetv1/'` to match your actual GitHub repo name

## Step 3: Test Locally

1. **Generate sample data:**
```bash
python export_to_json.py
```

2. **Run dashboard:**
```bash
cd dashboard
npm run dev
```

3. Visit `http://localhost:5173` to see the dashboard

## Step 4: Deploy to GitHub Pages

### Option A: Manual Deployment

1. Build the dashboard:
```bash
cd dashboard
npm run build
```

2. Copy contents of `dashboard/dist` to your `gh-pages` branch

3. Enable GitHub Pages in your repo settings

### Option B: Automatic Deployment (Recommended)

1. **Set up GitHub Secrets:**
   - Go to your repo → Settings → Secrets and variables → Actions
   - Add `DB_CONNECTION_STRING` with your Neon connection string

2. **The GitHub Action will:**
   - Run daily at 8 AM EST
   - Generate new betting data
   - Save to Neon database
   - Export to JSON
   - Build and deploy dashboard

3. **Manual trigger:** You can also trigger it manually from the Actions tab

## Step 5: Manual Reload

To manually reload bets:

1. **Via GitHub Actions:**
   - Go to Actions tab
   - Click "Daily Bet Update"
   - Click "Run workflow"

2. **Via API (if you set up serverless function):**
   - Call the `/api/reload` endpoint
   - Or create a simple webhook

3. **Locally:**
   ```bash
   python export_to_json.py
   ```

## Dashboard Features

### Main Page (Best Bets)
- ✅ Visual EV meters showing expected value
- ✅ Color-coded confidence indicators
- ✅ Kelly fraction for bet sizing
- ✅ Filter by EV threshold
- ✅ Sort by EV, confidence, or Kelly
- ✅ Reload button to refresh data

### Performance Page
- ✅ Win/loss tracking
- ✅ ROI and profit metrics
- ✅ Charts showing performance over time
- ✅ Performance by prop type

## Data Flow

```
main_workflow.py 
  → Generates betting data
  → Saves to Neon DB (processed_props table)
  → Exports to JSON (dashboard/public/data/latest-bets.json)
  → Dashboard reads JSON and displays
```

## Customization

### Update Colors
Edit `dashboard/src/components/BetCard.css` and `EVMeter.css`

### Add More Metrics
Edit `dashboard/src/components/BetCard.jsx` to display additional fields

### Change Layout
Edit `dashboard/src/pages/BetsPage.css` for grid layout

## Troubleshooting

### Dashboard shows "No bets found"
- Check that `dashboard/public/data/latest-bets.json` exists
- Run `python export_to_json.py` to generate it
- Check browser console for errors

### Database connection fails
- Verify connection string in `database.py`
- Check that tables exist (run `database_schema.sql`)
- Ensure IP is whitelisted if required

### GitHub Pages not updating
- Check Actions tab for errors
- Verify `vite.config.js` base path matches repo name
- Ensure `gh-pages` branch exists

## Next Steps

1. ✅ Set up database tables
2. ✅ Test locally
3. ✅ Deploy to GitHub Pages
4. ✅ Set up GitHub Actions for automation
5. ✅ Start tracking bets in `bet_tracking` table
6. ✅ Build out performance tracking

Your dashboard is ready to go! 🚀
