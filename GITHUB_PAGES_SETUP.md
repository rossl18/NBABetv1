# GitHub Pages Setup - Step by Step

## 🎯 Complete Deployment Guide

Follow these steps in order to deploy your NBA Betting Dashboard to GitHub Pages.

---

## Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. **Repository name**: Choose a name (e.g., `NBABetv1`, `nba-betting-dashboard`)
   - ⚠️ **Remember this name** - you'll need it for the base path!
3. **Description**: "NBA Betting Dashboard with ML predictions"
4. **Visibility**: Public (required for free GitHub Pages)
5. **DO NOT** check:
   - ❌ Add a README file
   - ❌ Add .gitignore
   - ❌ Choose a license
6. Click **Create repository**

---

## Step 2: Update Base Path in Vite Config

**CRITICAL**: Update `dashboard/vite.config.js` to match your repository name:

```javascript
// Change this line:
base: '/NBABetv1/',  // ← Change NBABetv1 to YOUR repository name

// Example if your repo is "nba-betting":
base: '/nba-betting/',
```

**If you skip this step, your dashboard will show a blank page!**

---

## Step 3: Initialize Git and Push Code

Open PowerShell in your project directory:

```powershell
# Navigate to project
cd c:\Users\rnl31\Desktop\NBABetv1

# Initialize git (if not already done)
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: NBA Betting Dashboard"

# Add your GitHub repository (replace with your actual URL)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Replace:**
- `YOUR_USERNAME` with your GitHub username
- `YOUR_REPO_NAME` with your repository name

---

## Step 4: Add Database Secret to GitHub

1. Go to your repository on GitHub
2. Click **Settings** (top menu)
3. Click **Secrets and variables** → **Actions** (left sidebar)
4. Click **New repository secret**
5. Fill in:
   - **Name**: `DB_CONNECTION_STRING`
   - **Secret**: Your full Neon connection string:
     ```
     postgresql://neondb_owner:npg_4mPxqU1CzSoI@ep-summer-band-ahle3ux5-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
     ```
6. Click **Add secret**

---

## Step 5: Create Database Tables

Before the first deployment, create the required tables in your Neon database.

### Option A: Using psql (Command Line)

```powershell
# If you have psql installed
psql 'postgresql://neondb_owner:npg_4mPxqU1CzSoI@ep-summer-band-ahle3ux5-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require' -f database_schema.sql
```

### Option B: Using Neon Console

1. Go to https://console.neon.tech
2. Open your database
3. Go to **SQL Editor**
4. Copy and paste the contents of `database_schema.sql`
5. Click **Run**

### Option C: Using Python Script

```powershell
python -c "from database import get_db_connection; conn = get_db_connection(); cursor = conn.cursor(); cursor.execute(open('database_schema.sql').read()); conn.commit(); print('Tables created!')"
```

---

## Step 6: Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** → **Pages** (left sidebar)
3. Under **Source**:
   - Select: **GitHub Actions**
4. Click **Save**

**Note**: The page will show "Your site is ready to be published" until the first workflow runs.

---

## Step 7: Trigger First Deployment

### Manual Trigger (Recommended)

1. Go to **Actions** tab in your repository
2. You should see **Daily Bet Update** workflow
3. Click **Run workflow** (dropdown button)
4. Click **Run workflow** (green button)
5. Wait for it to complete (~5-10 minutes)

### What the Workflow Does

1. ✅ Checks out your code
2. ✅ Sets up Python and installs dependencies
3. ✅ Runs `export_to_json.py`:
   - Scrapes live odds from FanDuel
   - Generates predictions
   - Saves to `processed_props` table
   - Tracks outcomes for past games
   - Exports JSON files
4. ✅ Sets up Node.js and builds React dashboard
5. ✅ Deploys to GitHub Pages

---

## Step 8: Access Your Dashboard

Once deployment completes (green checkmark in Actions):

Your dashboard URL will be:
```
https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/
```

For example:
```
https://rnl31.github.io/NBABetv1/
```

---

## ✅ Verification Checklist

Before considering deployment complete, verify:

- [ ] Repository created on GitHub
- [ ] `vite.config.js` base path updated to match repo name
- [ ] Code pushed to GitHub (all files committed)
- [ ] `DB_CONNECTION_STRING` secret added to GitHub
- [ ] Database tables created (`processed_props` and `bet_tracking`)
- [ ] GitHub Pages enabled (Source: GitHub Actions)
- [ ] First workflow run completed successfully (green checkmark)
- [ ] Dashboard accessible at GitHub Pages URL
- [ ] Data loads correctly (check browser console for errors)

---

## 🔄 Automatic Updates

### Daily Schedule

The workflow runs **automatically every day at 8 AM EST** (1 PM UTC).

### Manual Trigger

To manually update:
1. Go to **Actions** tab
2. Click **Daily Bet Update**
3. Click **Run workflow** → **Run workflow**

---

## 🐛 Troubleshooting

### Dashboard shows 404 or blank page

**Problem**: Base path mismatch

**Solution**:
1. Check `dashboard/vite.config.js` - base path must match repo name exactly
2. Verify GitHub Pages is enabled and using GitHub Actions
3. Check Actions tab for build errors

### Workflow fails with "Database connection" error

**Problem**: Secret not set or incorrect

**Solution**:
1. Go to Settings → Secrets and variables → Actions
2. Verify `DB_CONNECTION_STRING` exists
3. Check that the connection string is correct (no extra spaces)
4. Re-run the workflow

### Workflow fails with "Table does not exist"

**Problem**: Database tables not created

**Solution**:
1. Run `database_schema.sql` in your Neon database
2. Verify tables exist:
   ```sql
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public' 
   AND table_name IN ('processed_props', 'bet_tracking');
   ```

### Build fails with npm errors

**Problem**: Node.js version or dependency issues

**Solution**:
1. Check Actions logs for specific error
2. Verify `dashboard/package.json` is correct
3. Try deleting `dashboard/node_modules` and `package-lock.json` locally, then:
   ```powershell
   cd dashboard
   npm install
   npm run build
   ```
4. If it works locally, commit and push

### Data not showing on dashboard

**Problem**: JSON files not generated or wrong path

**Solution**:
1. Check Actions logs - verify `export_to_json.py` completed
2. Verify `dashboard/public/data/latest-bets.json` exists in the build
3. Check browser console for fetch errors
4. Verify base path in `vite.config.js` matches repo name

---

## 🔐 Admin Access

To access the reload button (admin only):

Add `?admin=true` to your dashboard URL:
```
https://yourusername.github.io/NBABetv1/?admin=true
```

Default password: `admin123` (change this before going live!)

---

## 📝 Post-Deployment Checklist

After successful deployment:

- [ ] Change admin password in code
- [ ] Test dashboard loads correctly
- [ ] Verify filters work
- [ ] Check performance page (should be empty initially)
- [ ] Test admin reload button (with `?admin=true`)
- [ ] Monitor first automatic run (next day at 8 AM EST)
- [ ] Update all-star players list if needed

---

## 🎉 You're Live!

Your dashboard is now deployed and will update automatically every morning!

**Dashboard URL**: `https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/`

**Next automatic update**: Tomorrow at 8 AM EST

---

## 📞 Quick Reference

- **Workflow file**: `.github/workflows/daily-update.yml`
- **Base path config**: `dashboard/vite.config.js`
- **Database schema**: `database_schema.sql`
- **Admin password**: Change in `dashboard/src/pages/BetsPage.jsx` and `dashboard/app.js`
