# 🚀 Quick Deploy Checklist

## Before You Start

1. **Decide on repository name** (e.g., `NBABetv1`, `nba-betting`)
2. **Have your Neon database connection string ready**

---

## 5-Minute Setup

### 1. Update Base Path ⚠️ CRITICAL

Edit `dashboard/vite.config.js`:
```javascript
base: '/YOUR_REPO_NAME/',  // Change NBABetv1 to your actual repo name
```

### 2. Create GitHub Repo

- Go to https://github.com/new
- Name it (remember the name!)
- **Don't** initialize with README/gitignore
- Create repository

### 3. Push Code

```powershell
cd c:\Users\rnl31\Desktop\NBABetv1
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

### 4. Add Secret

GitHub → Settings → Secrets → Actions → New secret:
- **Name**: `DB_CONNECTION_STRING`
- **Value**: Your Neon connection string

### 5. Enable Pages

GitHub → Settings → Pages:
- **Source**: GitHub Actions

### 6. Create Database Tables

Run `database_schema.sql` in your Neon database.

### 7. Trigger First Run

GitHub → Actions → Daily Bet Update → Run workflow

### 8. Access Dashboard

Wait ~5-10 minutes, then visit:
```
https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/
```

---

## ✅ Done!

Your dashboard is live and will update automatically every day at 8 AM EST.

For detailed instructions, see `GITHUB_PAGES_SETUP.md`.
