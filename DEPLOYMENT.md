# GitHub Pages Deployment Guide

## 🚀 Quick Start

Follow these steps to deploy your NBA Betting Dashboard to GitHub Pages.

## Step 1: Create GitHub Repository

1. Go to [GitHub](https://github.com) and create a new repository
2. Name it (e.g., `NBABetv1` - **remember this name!**)
3. **Don't** initialize with README, .gitignore, or license (you already have these)
4. Copy the repository URL

## Step 2: Update Repository Name in Config

**IMPORTANT**: Update the base path in `dashboard/vite.config.js` to match your repository name:

```javascript
base: '/YOUR_REPO_NAME/',  // Change NBABetv1 to your actual repo name
```

For example, if your repo is `nba-betting`, change it to:
```javascript
base: '/nba-betting/',
```

## Step 3: Initialize Git and Push

```powershell
# Navigate to your project directory
cd c:\Users\rnl31\Desktop\NBABetv1

# Initialize git (if not already done)
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: NBA Betting Dashboard"

# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 4: Configure GitHub Secrets

You need to add your database connection string as a GitHub secret:

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `DB_CONNECTION_STRING`
5. Value: Your full Neon database connection string:
   ```
   postgresql://neondb_owner:npg_4mPxqU1CzSoI@ep-summer-band-ahle3ux5-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
   ```
6. Click **Add secret**

## Step 5: Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** → **Pages**
3. Under **Source**, select:
   - **Source**: `GitHub Actions`
4. Click **Save**

## Step 6: Create Database Tables

Before the first deployment, create the database tables:

1. Connect to your Neon database (using psql or a database client)
2. Run the SQL script:
   ```sql
   -- Copy and paste the contents of database_schema.sql
   ```

Or use the connection string:
```powershell
psql 'postgresql://neondb_owner:npg_4mPxqU1CzSoI@ep-summer-band-ahle3ux5-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require' -f database_schema.sql
```

## Step 7: Trigger First Deployment

### Option A: Manual Trigger (Recommended for First Time)

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Click **Daily Bet Update** workflow
4. Click **Run workflow** → **Run workflow** (green button)
5. Wait for it to complete (takes ~5-10 minutes)

### Option B: Automatic (After First Push)

The workflow will automatically run:
- **Daily at 8 AM EST** (1 PM UTC)
- Every time you push to `main` branch (if you want)

## Step 8: Access Your Dashboard

Once deployment completes, your dashboard will be available at:

```
https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/
```

For example:
```
https://rnl31.github.io/NBABetv1/
```

## ✅ Verification Checklist

- [ ] Repository created on GitHub
- [ ] `vite.config.js` base path updated to match repo name
- [ ] Code pushed to GitHub
- [ ] `DB_CONNECTION_STRING` secret added to GitHub
- [ ] GitHub Pages enabled (Source: GitHub Actions)
- [ ] Database tables created (`processed_props` and `bet_tracking`)
- [ ] First workflow run completed successfully
- [ ] Dashboard accessible at GitHub Pages URL

## 🔄 Manual Updates

To manually trigger an update:

1. Go to **Actions** tab in your repository
2. Click **Daily Bet Update** workflow
3. Click **Run workflow** → **Run workflow**

This will:
- Generate new betting predictions
- Save to database
- Track outcomes for past games
- Build and deploy the dashboard

## 📅 Automatic Schedule

The workflow runs **automatically every day at 8 AM EST** (1 PM UTC).

To change the schedule, edit `.github/workflows/daily-update.yml`:

```yaml
schedule:
  - cron: '0 13 * * *'  # Change this (uses UTC time)
```

Cron format: `minute hour day month day-of-week`
- `0 13 * * *` = 1:00 PM UTC daily (8 AM EST)

## 🐛 Troubleshooting

### Dashboard shows 404 or blank page
- Check that `vite.config.js` base path matches your repo name
- Verify GitHub Pages is enabled and using GitHub Actions as source
- Check the Actions tab for workflow errors

### Workflow fails with database error
- Verify `DB_CONNECTION_STRING` secret is set correctly
- Check that database tables exist (run `database_schema.sql`)
- Ensure database connection string is correct

### Data not updating
- Check Actions tab to see if workflow is running
- Verify workflow completed successfully (green checkmark)
- Check workflow logs for errors

### Build fails
- Check that `dashboard/package.json` has all dependencies
- Verify Node.js version in workflow (currently 3.11 for Python, latest for Node)
- Check workflow logs for specific error messages

## 🔐 Admin Access

To access the reload button (admin only):
- Add `?admin=true` to your dashboard URL
- Example: `https://yourusername.github.io/NBABetv1/?admin=true`
- Password: `admin123` (change this in code!)

## 📝 Next Steps After Deployment

1. **Change admin password** in:
   - `dashboard/src/pages/BetsPage.jsx`
   - `dashboard/app.js`

2. **Update all-star players list** if needed:
   - `dashboard/src/pages/BetsPage.jsx`
   - `dashboard/app.js`

3. **Monitor first few runs** to ensure everything works correctly

4. **Set game_date** when you extract game dates from FanDuel API (for automatic tracking)

## 🎉 You're Live!

Your dashboard is now live and will update automatically every morning!
