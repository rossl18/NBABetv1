-- SQL script to create tables in Neon database for dashboard

-- Table to store processed props (updated daily)
CREATE TABLE IF NOT EXISTS processed_props (
    id SERIAL PRIMARY KEY,
    player VARCHAR(255) NOT NULL,
    prop VARCHAR(100) NOT NULL,
    line FLOAT NOT NULL,
    over_under VARCHAR(10) NOT NULL,
    odds INTEGER,
    decimal_odds FLOAT,
    implied_probability FLOAT,
    model_probability FLOAT,
    probability_ci_lower FLOAT,
    probability_ci_upper FLOAT,
    edge FLOAT,
    expected_value FLOAT,
    ev_ci_lower FLOAT,
    ev_ci_upper FLOAT,
    kelly_fraction FLOAT,
    confidence_score FLOAT,
    historical_games INTEGER,
    training_samples INTEGER,
    generated_at TIMESTAMP NOT NULL,
    game_date DATE,  -- Date of the game (if available from odds)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table to track bet outcomes and model performance
CREATE TABLE IF NOT EXISTS bet_tracking (
    id SERIAL PRIMARY KEY,
    prop_id INTEGER REFERENCES processed_props(id),
    player VARCHAR(255) NOT NULL,
    prop VARCHAR(100) NOT NULL,
    line FLOAT NOT NULL,
    over_under VARCHAR(10) NOT NULL,
    odds INTEGER,
    model_probability FLOAT,
    expected_value FLOAT,
    bet_placed BOOLEAN DEFAULT FALSE,
    bet_amount FLOAT,
    outcome BOOLEAN,  -- TRUE if prop hit, FALSE if not, NULL if not yet determined
    actual_result FLOAT,  -- Actual stat value
    profit_loss FLOAT,  -- Profit/loss from bet
    game_date DATE,
    result_date DATE,  -- When outcome was determined
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_processed_props_generated_at ON processed_props(generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_processed_props_expected_value ON processed_props(expected_value DESC);
CREATE INDEX IF NOT EXISTS idx_processed_props_player ON processed_props(player);
CREATE INDEX IF NOT EXISTS idx_bet_tracking_prop_id ON bet_tracking(prop_id);
CREATE INDEX IF NOT EXISTS idx_bet_tracking_game_date ON bet_tracking(game_date);
