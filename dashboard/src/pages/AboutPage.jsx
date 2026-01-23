import React from 'react'
import './AboutPage.css'

function AboutPage() {
  return (
    <div className="about-page">
      <div className="container">
        <h1>About This Dashboard</h1>
        
        <section className="about-section">
          <h2>What This Is</h2>
          <p>
            This dashboard scrapes live NBA player prop odds from FanDuel and uses machine learning 
            to identify value bets. Every day, it pulls the latest lines, trains player-specific models 
            on historical performance, and calculates expected value for each prop.
          </p>
            <p>
              The goal is simple: find bets where the model thinks the probability of hitting is higher 
              than what the sportsbook odds imply. If FanDuel says a player has a 50% chance to go over 
              their points line, but our model thinks it's actually 65%, that's a potential edge worth betting.
            </p>
        </section>

        <section className="about-section">
          <h2>How It Works</h2>
          
          <div className="pipeline-step">
            <h3>1. FanDuel Odds Scraping</h3>
            <p>
              The scraping process uses FanDuel's internal API endpoints (not web scraping). Here's how it works:
            </p>
            <ul className="technical-details">
              <li>
                <strong>Game Discovery:</strong> First, it hits FanDuel's event discovery endpoint to get all 
                active NBA game IDs for the day. This returns a list of game identifiers.
              </li>
              <li>
                <strong>Market Harvesting:</strong> For each game, it queries five prop categories in parallel 
                using ThreadPoolExecutor with 15 workers: player points, player rebounds, player assists, 
                player threes, and player defense. Each API call returns market metadata and athlete mappings.
              </li>
              <li>
                <strong>Price Fetching:</strong> Once all markets are discovered, it batches market IDs 
                (50 at a time) and POSTs to FanDuel's price endpoint to get live odds. This endpoint returns 
                the current American odds, handicap (line), and runner details for each market.
              </li>
              <li>
                <strong>Data Parsing:</strong> The scraper groups runners by market and line to identify 
                Over/Under pairs. It uses multiple fallback methods to extract player names and determine 
                which runner is Over versus Under by checking runner names, market structure, selection IDs, 
                and athlete mappings.
              </li>
              <li>
                <strong>Output:</strong> The final result is a pandas DataFrame with Player, Prop, Line, 
                Over/Under, and Odds columns. Typically pulls between 1,000 and 1,500 props per day.
              </li>
            </ul>
            <p>
              This all happens automatically every morning at 8 AM EST via GitHub Actions, so the data stays 
              fresh without any manual work.
            </p>
          </div>

          <div className="pipeline-step">
            <h3>2. Historical Data Retrieval</h3>
            <p>
              For each player and prop type combination, the system queries a Neon PostgreSQL database 
              containing historical NBA game data. The database has game-by-game stats going back several 
              seasons, with columns for points, rebounds, assists, threes, steals, blocks, plus metadata 
              like game date, opponent, and whether the player was home or away.
            </p>
            <p>
              The query filters to only that specific player's games and sorts chronologically. Players 
              need at least 10 games in the database to be eligible for modeling—this minimum threshold 
              ensures there's enough data to learn meaningful patterns.
            </p>
          </div>

          <div className="pipeline-step">
            <h3>3. Feature Engineering & Model Training</h3>
            <p>
              Before training, the historical data gets transformed into features:
            </p>
            <ul className="technical-details">
              <li>
                <strong>Rolling Statistics:</strong> Five game and ten game rolling averages for the relevant 
                stat like points or rebounds. This captures recent form.
              </li>
              <li>
                <strong>Line Context:</strong> The current line value is added as a feature, plus 
                historical hit rate against similar lines.
              </li>
              <li>
                <strong>Game Context:</strong> Features like rest days, home/away, and opponent strength 
                (if available in the dataset).
              </li>
              <li>
                <strong>Target Variable:</strong> For each historical game, a binary target is created: 
                1 if the player hit the prop (e.g., scored over the line), 0 if they didn't.
              </li>
            </ul>
            <p>
              Instead of one big model for everyone, each player gets their own Random Forest model trained 
              exclusively on their historical data. So LeBron's model only learns from LeBron's games, 
              Steph's model only learns from Steph's games, and so on. This keeps things player-specific 
              and avoids mixing apples with oranges.
            </p>
            <p>
              The Random Forest uses 100 trees, max depth of 10, and splits data 80/20 for training/testing. 
              After training, it outputs a raw probability that the prop will hit. The model also calculates 
              confidence intervals by looking at variance across the individual trees.
            </p>
          </div>

          <div className="pipeline-step">
            <h3>4. Probability Calibration</h3>
            <p>
              Raw model outputs can be overconfident—especially when a player has been on a hot streak. 
              To keep things realistic, probabilities get calibrated through a multi-step process:
            </p>
            <ul className="technical-details">
              <li>
                <strong>Compression Mapping:</strong> Probabilities above 90% get mapped down to the 65 to 75% 
                range. Probabilities between 75 and 90% compress to 60 to 65%. Middle probabilities from 10 to 
                75% map to 20 to 60%. This prevents extreme predictions like 100% or 0%.
              </li>
              <li>
                <strong>Market Blending:</strong> After compression, if the calibrated probability differs 
                from the implied probability from odds by more than 25%, they get blended together. The 
                blend weight increases with the difference. If the model says 80% but the market says 40%, 
                we trust the market more and blend 60% model and 40% market. This prevents ignoring efficient 
                market signals.
              </li>
              <li>
                <strong>Final Clamp:</strong> All probabilities are clamped to a 10 to 75% range. Nothing goes 
                above 75% or below 10%, keeping predictions realistic.
              </li>
            </ul>
          </div>

          <div className="pipeline-step">
            <h3>5. Expected Value & Risk Adjustment</h3>
            <p>
              Once we have a calibrated probability, we calculate expected value using the formula:
            </p>
            <p className="formula">
              EV = (probability × (decimal_odds - 1)) - ((1 - probability) × 1)
            </p>
            <p>
              This gives us the expected profit per dollar bet. Positive EV means the bet is theoretically 
              profitable in the long run, even if it might lose on any given night.
            </p>
            <p>
              We also calculate the Kelly Criterion fraction, which tells you the optimal bet size as a 
              percentage of your bankroll. Then we multiply EV by Kelly Fraction to the power of 1.5 to get 
              "Kelly adjusted EV." The exponent of 1.5 adds extra penalty for high variance bets. A plus 500 
              longshot with high EV might look great, but it's also more volatile than a minus 150 favorite 
              with similar EV. The Kelly adjustment helps balance that out and prevents the dashboard from 
              being biased toward high odds bets.
            </p>
            <p>
              Bets are sorted by this Kelly-adjusted EV, so the best risk-adjusted opportunities appear first.
            </p>
          </div>

          <div className="pipeline-step">
            <h3>6. Data Storage & Outcome Tracking</h3>
            <p>
              All processed props get saved to a PostgreSQL database in two tables:
            </p>
            <ul className="technical-details">
              <li>
                <strong>processed_props:</strong> Stores daily predictions with all the details including player, 
                prop, line, odds, model probability, expected value, confidence intervals, Kelly fraction, 
                and a timestamp of when it was generated.
              </li>
              <li>
                <strong>bet_tracking:</strong> Links to processed_props and stores actual outcomes. After 
                games finish, the system queries the NBA API using the nba_api Python package to get 
                actual game stats, then matches them to the predictions. It records whether the prop hit, 
                the actual stat value, profit or loss, and when the outcome was determined.
              </li>
            </ul>
            <p>
              The outcome tracking happens automatically the day after games are played. It queries props 
              that were generated yesterday, looks up the actual stats from the NBA API, and updates the 
              bet_tracking table. The Performance tab pulls from this table to show win rates, ROI, 
              calibration accuracy, and breakdowns by prop type and odds range.
            </p>
          </div>
        </section>

        <section className="about-section">
          <h2>The Automation Pipeline</h2>
          <p>
            Everything runs automatically via GitHub Actions. Here's the daily workflow:
          </p>
          <div className="pipeline-step">
            <h3>Daily GitHub Actions Workflow</h3>
            <ol className="technical-details" style={{paddingLeft: '1.5rem'}}>
              <li>
                <strong>Trigger:</strong> Runs every day at 8:00 AM EST via cron schedule
              </li>
              <li>
                <strong>Environment Setup:</strong> Spins up a fresh Ubuntu runner, installs Python 3.11, 
                and installs all dependencies from requirements.txt
              </li>
              <li>
                <strong>Data Generation:</strong> Runs export_to_json.py which calls generate_betting_dataset 
                to scrape FanDuel, train models, and calculate EVs. It saves all props to the processed_props 
                database table and exports the results to dashboard/public/data/latest-bets.json
              </li>
              <li>
                <strong>Outcome Tracking:</strong> Processes props from yesterday to check actual outcomes 
                and update the bet_tracking table
              </li>
              <li>
                <strong>Performance Export:</strong> Generates performance metrics and saves to 
                dashboard/public/data/performance.json
              </li>
              <li>
                <strong>Dashboard Build:</strong> Runs npm install and npm run build to compile the React app
              </li>
              <li>
                <strong>Deployment:</strong> Pushes the built files to the gh-pages branch, which GitHub Pages 
                serves automatically
              </li>
            </ol>
            <p>
              The entire process takes about 5 to 10 minutes, and the dashboard updates automatically. No 
              manual intervention needed.
            </p>
          </div>
        </section>

        <section className="about-section">
          <h2>Technical Stack</h2>
          <div className="tech-grid">
            <div className="tech-item">
              <strong>Backend:</strong> Python (pandas, scikit-learn, psycopg2)
            </div>
            <div className="tech-item">
              <strong>Database:</strong> Neon PostgreSQL
            </div>
            <div className="tech-item">
              <strong>Frontend:</strong> React with Vite
            </div>
            <div className="tech-item">
              <strong>Deployment:</strong> GitHub Pages + GitHub Actions
            </div>
            <div className="tech-item">
              <strong>Data Sources:</strong> FanDuel (odds), NBA API (game stats)
            </div>
          </div>
        </section>

        <section className="about-section">
          <h2>Important Notes</h2>
          <ul className="notes-list">
            <li>
              <strong>This is for entertainment/educational purposes.</strong> Sports betting involves risk, 
              and past performance doesn't guarantee future results. The model can be wrong, and even good 
              bets lose sometimes.
            </li>
            <li>
              <strong>Model probabilities are estimates, not guarantees.</strong> A 70% probability means 
              the model thinks it'll hit about 7 out of 10 times, but any single bet is still a coin flip 
              in the moment.
            </li>
            <li>
              <strong>Odds change constantly.</strong> By the time you see a bet here, the line might have 
              moved or the bet might not even be available anymore. Always check the current odds before 
              placing anything.
            </li>
            <li>
              <strong>Sample size matters.</strong> Players with fewer than 10 to 15 games in the database 
              have less reliable predictions. The confidence score on each bet tries to reflect this.
            </li>
          </ul>
        </section>

        <section className="about-section">
          <h2>What's Next</h2>
          <p>
            The model keeps learning as more games get played. Every night's outcomes get tracked, which 
            helps refine the predictions over time. The Performance tab shows how things are going—if 
            certain prop types or odds ranges are performing better than others, that's all visible there.
          </p>
          <p>
            If you notice the model is consistently overconfident on certain types of bets, or if there's 
            a pattern in the misses, that feedback helps improve the calibration. The goal is to get better 
            over time, not to be perfect from day one.
          </p>
        </section>
      </div>
    </div>
  )
}

export default AboutPage
