# Quick Start: Dashboard Setup

## 🚀 Get Your Dashboard Running in 5 Steps

### Step 1: Create Database Tables (One-time)

Run this in your Neon SQL editor:
```sql
-- Copy contents of database_schema.sql and run in Neon
```

### Step 2: Install Dashboard Dependencies

```powershell
cd dashboard
npm install
```

### Step 3: Generate Initial Data

```powershell
cd ..
python export_to_json.py
```

This will:
- Generate betting data
- Save to Neon database
- Export to JSON for dashboard

### Step 4: Test Dashboard Locally

```powershell
cd dashboard
npm run dev
```

Visit `http://localhost:5173` to see your dashboard!

### Step 5: Deploy to GitHub Pages

1. **Build the dashboard:**
```powershell
cd dashboard
npm run build
```

2. **Update `vite.config.js`** with your GitHub repo name

3. **Deploy:**
   - Option A: Copy `dist` folder to `gh-pages` branch
   - Option B: Set up GitHub Actions (see `.github/workflows/daily-update.yml`)

## 🎨 Dashboard Features

✅ **Beautiful UI** with gradient backgrounds and modern design
✅ **EV Meters** - Visual indicators showing expected value
✅ **Color-coded cards** - Green for high EV, red for negative
✅ **Confidence bars** - Visual confidence score indicators
✅ **Kelly Fraction** - Optimal bet sizing displayed
✅ **Filtering & Sorting** - By EV, confidence, or Kelly
✅ **Performance Tracking** - Win/loss stats and charts
✅ **Manual Reload** - Refresh button to update data

## 📊 What You'll See

### Main Page
- Stats cards showing total props, positive EV count, etc.
- Grid of bet cards with:
  - Player name and prop type
  - Line and odds
  - Visual EV meter
  - Confidence score bar
  - Kelly fraction (if positive)
  - Edge calculation

### Performance Page
- Total bets, wins, losses
- Win rate and ROI
- Charts showing performance over time
- Performance breakdown by prop type

## 🔄 Daily Automation

The GitHub Action (`.github/workflows/daily-update.yml`) will:
1. Run daily at 8 AM EST
2. Generate new betting data
3. Save to Neon database
4. Export to JSON
5. Build and deploy dashboard

**To trigger manually:** Go to Actions tab → "Daily Bet Update" → "Run workflow"

## 🛠️ Customization

- **Colors:** Edit CSS files in `dashboard/src/components/`
- **Layout:** Modify `BetsPage.css` for grid layout
- **Metrics:** Add fields in `BetCard.jsx`

## 📝 Next Steps

1. ✅ Set up database tables
2. ✅ Test locally
3. ✅ Deploy to GitHub Pages
4. ✅ Set up GitHub Actions
5. Start tracking actual bets in `bet_tracking` table!

Your dashboard is ready! 🎉
