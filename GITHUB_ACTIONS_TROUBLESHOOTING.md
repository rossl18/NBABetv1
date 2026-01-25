# GitHub Actions Workflow Troubleshooting

## Scheduled Workflow Issues

### Why the workflow might not run automatically:

1. **Repository Inactivity**: GitHub may delay or skip scheduled workflows if the repository has been inactive for 60+ days
2. **Free Plan Limitations**: Free GitHub accounts have limited Actions minutes per month
3. **Workflow File Location**: The workflow file must be in `.github/workflows/` directory
4. **Branch Protection**: The workflow must be on the default branch (usually `main`)

### Current Schedule

- **Cron Expression**: `0 13 * * *` (1 PM UTC daily)
- **Local Time**: 8 AM EST / 9 AM EDT (depending on daylight saving time)
- **Note**: GitHub Actions always uses UTC timezone

### How to Verify the Workflow is Running

1. **Check Workflow Runs**:
   - Go to your repository on GitHub
   - Click on the "Actions" tab
   - Look for "Daily Bet Update" workflow runs
   - Check if there are recent runs at the scheduled time

2. **Check Workflow Status**:
   - Green checkmark = Success
   - Yellow circle = In progress
   - Red X = Failed
   - Gray circle = Skipped (may happen if repo is inactive)

3. **Manual Trigger**:
   - Go to Actions → Daily Bet Update
   - Click "Run workflow" button
   - This allows you to manually trigger the workflow

### If the Workflow Doesn't Run Automatically

1. **Verify the workflow file exists**: Check that `.github/workflows/daily-update.yml` exists and is committed to the `main` branch

2. **Check repository activity**: Make a commit or push to the repository to reactivate it

3. **Verify GitHub Actions is enabled**:
   - Go to Settings → Actions → General
   - Ensure "Allow all actions and reusable workflows" is selected

4. **Check Actions usage**: 
   - Go to Settings → Actions → Usage
   - Verify you haven't exceeded your monthly limit

5. **Alternative Schedule**: If the workflow consistently doesn't run, consider:
   - Using a different time (e.g., `0 14 * * *` for 2 PM UTC)
   - Adding multiple schedule times as backup
   - Using a webhook service to trigger the workflow

### Performance Update Fix

The workflow now processes games from the **last 7 days** instead of just yesterday. This ensures:
- Games aren't missed if the workflow didn't run for a few days
- All untracked games from recent days are processed
- Performance metrics are more complete

### Testing the Workflow Locally

You can test the export script locally:

```bash
# Set your database connection string
export DB_CONNECTION_STRING="your_connection_string"

# Run the export script
python export_to_json.py
```

This will:
1. Generate new betting predictions
2. Save them to the database
3. Track outcomes for games from the last 7 days
4. Export performance metrics
5. Create JSON files for the dashboard
