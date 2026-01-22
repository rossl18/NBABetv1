# Over/Under Detection Solution

## Problem
The original script couldn't determine whether a prop was "Over" or "Under" from the FanDuel API response.

## Solution Approach

The enhanced script uses **multiple detection methods** in order of reliability:

### Method 1: Direct Runner Name Check
- If `runnerName` is exactly "Over" or "Under", capture it immediately
- This is the most reliable method when available

### Method 2: Runner Name Contains Over/Under
- Check if the runner name contains "Over" or "Under" as a substring
- Useful when the format is like "Player Name - Over" or similar

### Method 3: Market Structure Analysis (Most Important)
- **Groups runners by market ID and handicap (line) value**
- Over/Under markets typically have exactly **2 runners per line**:
  - One for Over
  - One for Under
- When 2 runners are found for the same market/line:
  - The **first runner** (by index) is assumed to be **Over**
  - The **second runner** is assumed to be **Under**
- This method works even when runner names don't explicitly contain "Over"/"Under"

### Method 4: Field Inspection
- Checks various fields in the runner object (`side`, `outcome`, `outcomeType`, etc.)
- Looks for "Over" or "Under" in field values
- Checks runnerId/selectionId for patterns

### Method 5: Fallback
- If all methods fail, marks as "Unknown"
- You can review these cases and refine the logic

## Key Improvements

1. **Market Grouping**: Groups runners by `(marketId, line)` to identify Over/Under pairs
2. **Multiple Detection Methods**: Tries 5 different approaches before giving up
3. **Debug Mode**: Set `debug=True` to see detailed information about the API response structure
4. **Backward Compatible**: Function signature matches original (can be called without parameters)

## Usage

```python
# Production use (no debug output)
df = scrape_to_dataframe()

# Debug mode (shows detailed info and saves sample response)
df = scrape_to_dataframe(debug=True)
```

## Debugging

When `debug=True`:
- Prints detailed information about the first 10 runners
- Saves a sample API response to `debug_sample_response.json`
- Includes extra columns (`RunnerName`, `RunnerId`) in the dataframe
- Shows distribution of Over/Under detection results

## Next Steps

1. **Run with debug=True first** to see what data is actually available
2. **Check the `debug_sample_response.json`** file to inspect the full API response structure
3. **Review any "Unknown" Over/Under values** - these indicate cases where detection failed
4. **Refine Method 3** if needed - you might need to adjust the assumption about which runner is Over vs Under based on your data

## Expected Results

The dataframe now includes an **"Over/Under"** column with values:
- `"Over"` - for Over props
- `"Under"` - for Under props  
- `"Yes"` / `"No"` - for Yes/No props (like "Made 3+ Threes")
- `"Unknown"` - when detection failed (should be rare)
