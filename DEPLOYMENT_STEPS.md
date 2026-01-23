# Step-by-Step: Update Data and Deploy Dashboard to GitHub

## Quick Summary

1. Regenerate dashboard data with new model improvements
2. Build the React dashboard
3. Commit and push to GitHub
4. GitHub Actions will automatically deploy to GitHub Pages

---

## Detailed Steps

### Step 1: Regenerate Dashboard Data

This generates new predictions using all the model improvements (enhanced features, time weighting, optimized hyperparameters).

**Command:**
```powershell
python regenerate_all_data.py
```

**What this does:**
- Scrapes latest odds from FanDuel
- Generates predictions with new model improvements
- Tracks outcomes for past games
- Exports to `dashboard/public/data/latest-bets.json`
- Exports performance metrics to `dashboard/public/data/performance.json`

**Expected output:**
- You should see progress messages
- Should end with "✅ Dashboard export complete!"
- Check that files were created in `dashboard/public/data/`

**Troubleshooting:**
- If you get database connection errors, check your `DB_CONNECTION_STRING` environment variable
- If no props are generated, there may be no games today (this is normal)

---

### Step 2: Build the Dashboard

This compiles the React dashboard for production deployment.

**Commands:**
```powershell
cd dashboard
npm run build
```

**What this does:**
- Compiles React components
- Optimizes assets
- Creates production build in `dashboard/dist/`
- This is what GitHub Pages will serve

**Expected output:**
- Should show build progress
- Should end with "build complete" or similar
- Check that `dashboard/dist/` folder was created

**Troubleshooting:**
- If `npm` is not found, make sure Node.js is installed
- If build fails, check for errors in the output
- Make sure you're in the `dashboard` directory

---

### Step 3: Verify Files Are Ready

Before committing, verify the key files exist:

**Check these files exist:**
- `dashboard/public/data/latest-bets.json` - Latest betting predictions
- `dashboard/public/data/performance.json` - Performance metrics
- `dashboard/dist/` - Built dashboard (should have `index.html` inside)

**Quick check:**
```powershell
# From project root
Test-Path dashboard/public/data/latest-bets.json
Test-Path dashboard/public/data/performance.json
Test-Path dashboard/dist/index.html
```

All should return `True`.

---

### Step 4: Stage All Changes

Add all modified and new files to Git.

**Commands:**
```powershell
# Make sure you're in the project root (not dashboard folder)
cd ..  # If you're still in dashboard folder
git add .
```

**What this does:**
- Stages all changes including:
  - Updated Python scripts with model improvements
  - New JSON data files
  - Built dashboard files
  - Documentation updates

**Alternative (if you want to be selective):**
```powershell
git add feature_engineering.py modeling.py main_workflow.py
git add dashboard/public/data/*.json
git add dashboard/dist/
git add *.md
```

---

### Step 5: Commit Changes

Create a commit with a descriptive message.

**Command:**
```powershell
git commit -m "Update dashboard with model improvements: enhanced features, time weighting, optimized hyperparameters"
```

**Or a shorter message:**
```powershell
git commit -m "Deploy dashboard with improved model predictions"
```

**What this does:**
- Creates a commit with all staged changes
- Records the current state of your codebase

---

### Step 6: Push to GitHub

Upload your changes to GitHub.

**Command:**
```powershell
git push origin main
```

**What this does:**
- Uploads all commits to GitHub
- Triggers GitHub Actions workflow (if configured)
- Updates your repository

**Expected output:**
- Should show upload progress
- Should end with "done" or similar

**Troubleshooting:**
- If authentication fails, you may need to set up GitHub credentials
- If push is rejected, you may need to pull first: `git pull origin main`

---

### Step 7: Verify GitHub Actions (Automatic)

GitHub Actions will automatically:
1. Run the daily update workflow (if scheduled)
2. Build and deploy the dashboard to GitHub Pages

**Check status:**
1. Go to your GitHub repository
2. Click on "Actions" tab
3. You should see workflow runs
4. Green checkmark = success, red X = failure

**Note:** If you have a scheduled workflow (like `daily-update.yml`), it will run automatically at the scheduled time. The manual push triggers an immediate update.

---

## Complete Command Sequence

Here's the complete sequence in one go:

```powershell
# Step 1: Regenerate data
python regenerate_all_data.py

# Step 2: Build dashboard
cd dashboard
npm run build
cd ..

# Step 3: Stage, commit, and push
git add .
git commit -m "Deploy dashboard with improved model predictions"
git push origin main
```

---

## After Deployment

### Check GitHub Pages

1. Go to your repository on GitHub
2. Click "Settings" → "Pages"
3. Your dashboard should be available at: `https://[your-username].github.io/[repo-name]/`

### Verify Dashboard Works

1. Open the GitHub Pages URL
2. Check that:
   - Bets are displayed
   - Performance metrics show up
   - All pages load correctly

### Monitor Performance

- Check the dashboard daily to see new predictions
- Monitor performance metrics to track model improvements
- GitHub Actions will automatically update data daily (if configured)

---

## Troubleshooting

### "No data" on dashboard
- Make sure `latest-bets.json` exists in `dashboard/public/data/`
- Check that the file has content (not empty array)
- Verify the file path in the dashboard code matches

### Dashboard shows old data
- Clear browser cache (Ctrl+Shift+Delete)
- Check that `latest-bets.json` was updated (check file timestamp)
- Verify GitHub Pages is serving the latest build

### Build fails
- Check Node.js version: `node --version` (should be 14+)
- Try deleting `node_modules` and `package-lock.json`, then `npm install`
- Check for error messages in build output

### GitHub Actions fails
- Check the Actions tab for error details
- Verify environment variables are set in GitHub repository settings
- Check that `DB_CONNECTION_STRING` is configured in GitHub Secrets

### Data not updating
- Run `python regenerate_all_data.py` manually
- Check that database connection is working
- Verify FanDuel scraper is working (odds may be unavailable)

---

## Quick Reference

| Step | Command | Purpose |
|------|---------|---------|
| 1 | `python regenerate_all_data.py` | Generate new predictions |
| 2 | `cd dashboard && npm run build` | Build dashboard |
| 3 | `git add .` | Stage changes |
| 4 | `git commit -m "message"` | Commit changes |
| 5 | `git push origin main` | Push to GitHub |

---

## Notes

- **First time?** Make sure GitHub Pages is enabled in repository settings
- **Environment variables?** Set `DB_CONNECTION_STRING` in GitHub Secrets if using Actions
- **Scheduled updates?** The workflow will run automatically at scheduled times
- **Manual updates?** Run `regenerate_all_data.py` anytime to update data

---

## Need Help?

If something goes wrong:
1. Check error messages carefully
2. Verify all files exist where expected
3. Check GitHub Actions logs for detailed errors
4. Make sure all dependencies are installed
