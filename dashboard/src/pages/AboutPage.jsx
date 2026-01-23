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
            than what the sportsbook's odds imply. If FanDuel says a player has a 50% chance to go over 
            their points line, but our model thinks it's actually 65%, that's a potential edge worth betting.
          </p>
        </section>

        <section className="about-section">
          <h2>How It Works</h2>
          
          <div className="pipeline-step">
            <h3>1. Data Collection</h3>
            <p>
              Every morning, a script scrapes FanDuel's NBA player props page. It grabs all the available 
              lines—points, rebounds, assists, threes, steals, blocks—along with the current odds. This 
              happens automatically via GitHub Actions, so the data stays fresh without any manual work.
            </p>
          </div>

          <div className="pipeline-step">
            <h3>2. Historical Analysis</h3>
            <p>
              For each player and prop type, the system pulls their game-by-game stats from a historical 
              database. It looks at things like recent form, matchup difficulty, rest days, and how often 
              they've hit similar lines in the past. The more games a player has, the more reliable the 
              predictions tend to be.
            </p>
          </div>

          <div className="pipeline-step">
            <h3>3. Model Training</h3>
            <p>
              Instead of one big model for everyone, each player gets their own Random Forest model trained 
              exclusively on their historical data. So LeBron's model only learns from LeBron's games, 
              Steph's model only learns from Steph's games, and so on. This keeps things player-specific 
              and avoids mixing apples with oranges.
            </p>
            <p>
              The models look at features like rolling averages, recent trends, opponent defensive ratings, 
              and how the player has performed against similar lines. After training, they output a 
              probability that the prop will hit.
            </p>
          </div>

          <div className="pipeline-step">
            <h3>4. Probability Calibration</h3>
            <p>
              Raw model outputs can be overconfident—especially when a player has been on a hot streak. 
              To keep things realistic, probabilities get calibrated. High predictions get compressed (nothing 
              goes above 75%), and if the model says 80% but the market odds imply 40%, we blend them together. 
              The market is usually pretty efficient, so ignoring it completely would be foolish.
            </p>
          </div>

          <div className="pipeline-step">
            <h3>5. Expected Value Calculation</h3>
            <p>
              Once we have a calibrated probability, we calculate expected value. This is basically: 
              (probability of winning × payout) - (probability of losing × bet amount). Positive EV means 
              the bet is theoretically profitable in the long run, even if it might lose on any given night.
            </p>
            <p>
              Bets are sorted by "Kelly-adjusted EV," which accounts for risk. A +500 longshot with high 
              EV might look great, but it's also more volatile than a -150 favorite with similar EV. The 
              Kelly adjustment helps balance that out.
            </p>
          </div>

          <div className="pipeline-step">
            <h3>6. Outcome Tracking</h3>
            <p>
              After games finish, the system checks what actually happened. Did the player hit their over? 
              Did they miss? This gets logged in a database so we can see how well the model is performing 
              over time. The Performance tab shows all this—win rates, ROI, calibration accuracy, and 
              where the model is doing well (or poorly).
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
              <strong>Sample size matters.</strong> Players with fewer than 10-15 games in the database 
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
