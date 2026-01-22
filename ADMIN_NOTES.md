# Admin Notes

## Reload Button Access

The reload button is **hidden from public view** and only appears when you access the dashboard with an admin URL parameter.

### How to Access the Reload Button

Add `?admin=true` to the dashboard URL:
- React version: `http://localhost:5173/NBABetv1/?admin=true`
- GitHub Pages: `https://yourusername.github.io/NBABetv1/?admin=true`

The button will only appear when this parameter is present.

### Reload Button Password

Once visible, the reload button is password-protected. **Change the password** in:
- `dashboard/src/pages/BetsPage.jsx` (line ~37)
- `dashboard/app.js` (line ~178)

Current default password: `admin123`

**⚠️ IMPORTANT: Change this password before deploying!**

## Automatic Daily Updates

The dashboard is set up to automatically update every morning via GitHub Actions (`.github/workflows/daily-update.yml`).

The workflow:
- Runs daily at 8 AM EST (1 PM UTC)
- Executes `export_to_json.py` to generate new betting data
- Builds and deploys the dashboard to GitHub Pages

**You don't need to manually trigger reloads** - the data updates automatically. The reload button is only for manual testing/updates.

## All-Star Players List

The all-star filter uses a hardcoded list in:
- `dashboard/src/pages/BetsPage.jsx` (line ~9)
- `dashboard/app.js` (line ~3)

Update this list as needed to match current NBA all-stars.
