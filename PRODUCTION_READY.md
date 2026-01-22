# 🎉 Production Deployment - Ready to Go!

Your NBA Betting Dashboard is ready for production deployment to GitHub Pages.

## 📋 Pre-Deployment Checklist

Before deploying, make sure you have:

- [x] ✅ All code complete and tested
- [x] ✅ Database connection string ready
- [x] ✅ Database tables created (`database_schema.sql`)
- [x] ✅ GitHub account created
- [ ] ⚠️ **Repository name decided** (needed for base path)

---

## 🚀 Deployment Steps (15 minutes)

### Step 1: Update Base Path (2 min)

**CRITICAL**: Edit `dashboard/vite.config.js`:

```javascript
base: '/YOUR_REPO_NAME/',  // Change NBABetv1 to your actual GitHub repo name
```

**Example**: If your repo will be `nba-betting-dashboard`, change to:
```javascript
base: '/nba-betting-dashboard/',
```

### Step 2: Create GitHub Repository (2 min)

1. Go to https://github.com/new
2. Repository name: Choose a name (remember it!)
3. **Don't** check README/gitignore/license
4. Create repository

### Step 3: Push Code (3 min)

```powershell
cd c:\Users\rnl31\Desktop\NBABetv1

# If git not initialized
git init
git add .
git commit -m "Initial commit: NBA Betting Dashboard"

# Add remote and push
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

### Step 4: Add Database Secret (2 min)

1. GitHub → Your Repo → **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret**
3. Name: `DB_CONNECTION_STRING`
4. Value: `postgresql://neondb_owner:npg_4mPxqU1CzSoI@ep-summer-band-ahle3ux5-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require`
5. Add secret

### Step 5: Create Database Tables (3 min)

Run `database_schema.sql` in your Neon database:

**Option A - Neon Console:**
1. Go to https://console.neon.tech
2. Open your database → SQL Editor
3. Copy/paste contents of `database_schema.sql`
4. Run

**Option B - Command Line:**
```powershell
psql 'postgresql://neondb_owner:npg_4mPxqU1CzSoI@ep-summer-band-ahle3ux5-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require' -f database_schema.sql
```

### Step 6: Enable GitHub Pages (1 min)

1. GitHub → Your Repo → **Settings** → **Pages**
2. **Source**: Select **GitHub Actions**
3. Save

### Step 7: Trigger First Deployment (2 min)

1. GitHub → **Actions** tab
2. Click **Daily Bet Update**
3. Click **Run workflow** → **Run workflow**
4. Wait ~5-10 minutes for completion

### Step 8: Access Your Dashboard

Once workflow completes (green checkmark):

```
https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/
```

---

## ✅ What Happens Automatically

### Daily Schedule
- **Runs every day at 8 AM EST** (1 PM UTC)
- Scrapes latest odds
- Generates predictions
- Saves to database
- Tracks outcomes
- Builds and deploys dashboard

### Manual Trigger
- Go to **Actions** → **Daily Bet Update** → **Run workflow**
- Useful for testing or immediate updates

---

## 🔧 Configuration

### Change Update Schedule

Edit `.github/workflows/daily-update.yml`:

```yaml
schedule:
  - cron: '0 13 * * *'  # Change this (UTC time)
```

Cron format: `minute hour day month day-of-week`
- `0 13 * * *` = 1:00 PM UTC = 8:00 AM EST

### Change Admin Password

Edit these files:
- `dashboard/src/pages/BetsPage.jsx` (line ~37)
- `dashboard/app.js` (line ~178)

Change: `if (password !== 'admin123')`

---

## 🐛 Common Issues

### Blank Page / 404
- **Fix**: Update `vite.config.js` base path to match repo name

### Workflow Fails - Database Error
- **Fix**: Check `DB_CONNECTION_STRING` secret is set correctly

### Workflow Fails - Table Missing
- **Fix**: Run `database_schema.sql` in Neon database

### Build Fails
- **Fix**: Check Actions logs for specific error
- Usually Node.js or dependency issue

---

## 📚 Documentation Files

- **`GITHUB_PAGES_SETUP.md`** - Detailed step-by-step guide
- **`QUICK_DEPLOY.md`** - Quick reference checklist
- **`DEPLOYMENT.md`** - General deployment info
- **`ADMIN_NOTES.md`** - Admin access and passwords

---

## 🎯 You're Ready!

Follow the steps above and your dashboard will be live in ~15 minutes!

**Need help?** Check the troubleshooting section in `GITHUB_PAGES_SETUP.md`.
