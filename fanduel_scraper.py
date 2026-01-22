import requests
import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import json

# ================= CONFIGURATION =================
AK_KEY = "FhMFpcPWXMeyZxOx"
DISCOVERY_URL = "https://api.sportsbook.fanduel.com/ips/stats/eventIds"
PRICE_URL = "https://smp.ny.sportsbook.fanduel.com/api/sports/fixedodds/readonly/v1/getMarketPrices?priceHistory=0"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://sportsbook.fanduel.com/",
    "x-sportsbook-region": "ny",
}

TARGET_TABS = ["player-points", "player-rebounds", "player-assists", "player-threes", "player-defense"]

def get_tab_data(game_id, tab):
    url = f"https://api.sportsbook.fanduel.com/sbapi/event-page?_ak={AK_KEY}&eventId={game_id}&tab={tab}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=7)
        if resp.status_code == 200:
            data = resp.json()
            attachments = data.get('attachments', {})
            markets = attachments.get('markets', {})

            athlete_map = {}
            for athlete in attachments.get('athletes', []):
                athlete_map[athlete.get('athleteId')] = athlete.get('nickname')

            return {"markets": markets, "athletes": athlete_map}
    except:
        pass
    return {"markets": {}, "athletes": {}}

def scrape_to_dataframe(debug=False):
    print("Step 1: Discovering games...")
    game_ids = requests.get(DISCOVERY_URL, headers=HEADERS).json()
    game_ids = [gid for gid in game_ids if len(str(gid)) >= 8]

    master_market_map = {}
    master_athlete_map = {}

    print(f"Step 2: Deep-harvesting {len(game_ids)} games...")
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(get_tab_data, gid, tab) for gid in game_ids for tab in TARGET_TABS]
        for future in futures:
            res = future.result()
            master_market_map.update(res['markets'])
            master_athlete_map.update(res['athletes'])

    market_ids = list(master_market_map.keys())
    all_price_data = []
    print(f"Step 3: Fetching live lines for {len(market_ids)} markets...")

    for i in range(0, len(market_ids), 50):
        chunk = market_ids[i:i + 50]
        try:
            p_resp = requests.post(PRICE_URL, json={"marketIds": chunk}, headers=HEADERS)
            if p_resp.status_code == 200:
                all_price_data.extend(p_resp.json())
        except:
            continue

    # Debug: Save a sample response to inspect structure
    if debug and all_price_data:
        with open('debug_sample_response.json', 'w') as f:
            json.dump(all_price_data[0] if all_price_data else {}, f, indent=2)
        print("Debug: Saved sample response to debug_sample_response.json")

    # First pass: Group runners by market and line to determine Over/Under pairs
    # Over/Under markets typically have 2 runners per line
    market_line_groups = {}
    
    for market in all_price_data:
        m_id = market.get('marketId')
        market_info = master_market_map.get(m_id, {})
        raw_title = market_info.get('marketName', '')
        
        for idx, runner in enumerate(market.get('runnerDetails', [])):
            line = runner.get('handicap', 0.0)
            if line == 0.0 or line == '-':
                continue
            
            key = (m_id, line)
            if key not in market_line_groups:
                market_line_groups[key] = []
            market_line_groups[key].append({
                'runner': runner,
                'market_info': market_info,
                'raw_title': raw_title,
                'index': idx
            })
    
    final_rows = []
    for (m_id, line), runners in market_line_groups.items():
        market_info = runners[0]['market_info']
        raw_title = runners[0]['raw_title']
        
        # For each runner in this market/line group
        for runner_data in runners:
            runner = runner_data['runner']
            runner_name = runner.get('runnerName', '')
            player_name = runner_name
            over_under = None
            
            # Method 1: Direct check if runner name is "Over" or "Under"
            if runner_name in ['Over', 'Under']:
                over_under = runner_name
                player_name = master_athlete_map.get(runner.get('selectionId'), 'Unknown')
            elif runner_name in ['Yes', 'No']:
                over_under = runner_name
                player_name = master_athlete_map.get(runner.get('selectionId'), 'Unknown')
            
            # Method 2: Check if runner name contains Over/Under
            if over_under is None:
                runner_name_upper = runner_name.upper()
                if 'OVER' in runner_name_upper:
                    over_under = 'Over'
                elif 'UNDER' in runner_name_upper:
                    over_under = 'Under'
                
                # If found in name, try to extract player name
                if over_under and ' - ' in runner_name:
                    parts = runner_name.split(' - ')
                    if len(parts) >= 2:
                        potential_player = parts[0].strip()
                        if potential_player and potential_player not in ['Over', 'Under']:
                            player_name = potential_player
            
            # Method 3: Use market structure - if we have 2 runners, first is typically Over
            if over_under is None and len(runners) == 2:
                # Group runners by their index or other characteristics
                sorted_runners = sorted(runners, key=lambda x: x['index'])
                if runner_data == sorted_runners[0]:
                    over_under = 'Over'
                else:
                    over_under = 'Under'
                # Get player name from selectionId
                player_name = master_athlete_map.get(runner.get('selectionId'), 'Unknown')
            
            # Method 4: Check runner object fields for Over/Under indicators
            if over_under is None:
                # Check various fields that might contain the info
                for field in ['side', 'outcome', 'outcomeType', 'name', 'displayName']:
                    value = runner.get(field, '')
                    if isinstance(value, str):
                        value_upper = value.upper()
                        if 'OVER' in value_upper:
                            over_under = 'Over'
                            break
                        elif 'UNDER' in value_upper:
                            over_under = 'Under'
                            break
                
                # Check runnerId or selectionId patterns
                runner_id = str(runner.get('runnerId', '')).lower()
                if 'over' in runner_id:
                    over_under = 'Over'
                elif 'under' in runner_id:
                    over_under = 'Under'
            
            # Method 5: Fallback - use market name or other context
            if over_under is None:
                # Sometimes the market structure or name gives hints
                market_name_upper = raw_title.upper()
                # This is a last resort - we'll mark as Unknown
                pass
            
            # Extract player name if still not found
            if (not player_name or player_name == 'Unknown') and " - " in raw_title:
                player_name = raw_title.split(" - ")[0]
            
            # If player name is still Over/Under, try to get from selectionId
            if player_name in ['Over', 'Under', 'Yes', 'No']:
                player_name = master_athlete_map.get(runner.get('selectionId'), 'Unknown')
            
            prop_type = raw_title
            if " - " in raw_title:
                prop_type = raw_title.split(" - ")[-1]

            # Debug: Print first few runners to see structure
            if debug and len(final_rows) < 10:
                print(f"\nDebug Runner Data:")
                print(f"  Runner Name: {runner_name}")
                print(f"  Runner ID: {runner.get('runnerId')}")
                print(f"  Selection ID: {runner.get('selectionId')}")
                print(f"  Handicap: {line}")
                print(f"  Market Name: {raw_title}")
                print(f"  Runners in group: {len(runners)}")
                print(f"  Runner Index: {runner_data['index']}")
                print(f"  All Runner Keys: {list(runner.keys())}")
                print(f"  Over/Under Detected: {over_under}")
                print(f"  Player Name: {player_name}")
                # Print full runner object for first few
                if len(final_rows) < 3:
                    print(f"  Full Runner Object: {json.dumps(runner, indent=2, default=str)}")

            row_data = {
                "Player": player_name,
                "Prop": prop_type,
                "Line": line,
                "Over/Under": over_under if over_under else "Unknown",
                "Odds": runner.get('winRunnerOdds', {}).get('americanDisplayOdds', {}).get('americanOddsInt', 'OFF'),
            }
            
            # Add debug columns if in debug mode
            if debug:
                row_data["RunnerName"] = runner_name
                row_data["RunnerId"] = runner.get('runnerId', '')
            
            final_rows.append(row_data)

    df = pd.DataFrame(final_rows)
    df = df[df['Player'] != 'Unknown']

    df = df[df['Prop'] != '1st Qtr Points']
    df.loc[df['Prop'] == 'Made Threes', 'Prop'] = 'Threes'
    df = df.sort_values(by=['Player', 'Prop'])

    df['Player'] = df['Player'].replace('', np.nan)
    df = df.dropna(subset=['Player'])
    return df

if __name__ == "__main__":
    # Run with debug=True first to see what data is available
    df = scrape_to_dataframe(debug=True)
    print("\n" + "="*50)
    print("Sample of results:")
    print("="*50)
    print(df.head(20).to_string())
    print(f"\nTotal rows: {len(df)}")
    print(f"\nOver/Under distribution:")
    print(df['Over/Under'].value_counts())
