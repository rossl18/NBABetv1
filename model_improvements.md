# Model Performance Improvements (Without Adding Data)

## 1. Enhanced Feature Engineering

### Current Features
- Rolling averages (5-game, 10-game)
- Line value
- Basic game context

### Proposed New Features (from existing data)
- **Line Context Features**:
  - `line_vs_season_avg`: How does current line compare to player's season average?
  - `line_vs_recent_avg`: How does current line compare to last 5/10 game average?
  - `line_difficulty`: (line - recent_avg) / recent_std (normalized difficulty)
  - `historical_hit_rate_at_similar_line`: Win rate when line was within ±1 of current line

- **Trend Features**:
  - `trend_5_games`: Slope of last 5 games (increasing/decreasing performance)
  - `momentum`: (last_3_avg - prev_3_avg) / prev_3_avg (percentage change)
  - `volatility`: Standard deviation of last 10 games
  - `consistency_score`: 1 - (std / mean) for recent games

- **Relative Performance Features**:
  - `recent_vs_season`: (recent_avg - season_avg) / season_avg
  - `over_under_rate_recent`: Hit rate in last 10 games
  - `over_under_rate_season`: Overall hit rate for season

- **Interaction Features**:
  - `rolling_avg * line`: Interaction between form and line
  - `line / rolling_avg`: Ratio feature
  - `recent_std * line`: Volatility-adjusted line

## 2. Hyperparameter Optimization

### Current Random Forest Settings
- n_estimators=100
- max_depth=10
- min_samples_split=5
- min_samples_leaf=2

### Optimized Settings (based on typical prop betting data)
- **n_estimators=200-300**: More trees for better generalization
- **max_depth=8-12**: Tune based on data size (prevent overfitting)
- **min_samples_split=10**: Require more samples before splitting (reduce overfitting)
- **min_samples_leaf=5**: Require more samples in leaf nodes
- **max_features='sqrt'**: Use sqrt of features (typical for RF)
- **class_weight='balanced'**: Handle class imbalance if present

## 3. Time-Based Weighting

### Current Approach
- All historical games weighted equally

### Improved Approach
- Weight recent games more heavily using exponential decay
- Formula: `weight = exp(-decay_rate * days_ago)`
- Recent games (last 10) get 2-3x weight
- Older games get progressively less weight

## 4. Better Model Selection

### Current
- Only Random Forest

### Options
- **Gradient Boosting**: Already imported, often better for small datasets
- **Ensemble**: Combine RF + GB predictions (average or weighted)
- **XGBoost/LightGBM**: Better performance, faster training

## 5. Feature Selection

### Current
- Uses all `feat_*` columns

### Improved
- Use feature importance to select top N features
- Remove features with near-zero variance
- Remove highly correlated features (keep one)
- Focus on features with highest information gain

## 6. Better Probability Calibration

### Current
- Manual compression mapping

### Improved
- **Platt Scaling**: Learn calibration from validation set
- **Isotonic Regression**: Non-parametric calibration
- **Cross-validation based calibration**: Use out-of-fold predictions

## 7. Training Strategy Improvements

### Current
- Simple 80/20 train/test split

### Improved
- **Time-based split**: Train on older data, test on newer (more realistic)
- **Walk-forward validation**: Train on data up to date X, test on date X+1
- **Stratified sampling**: Ensure balanced classes in train/test

## 8. Handling Edge Cases

### Current Issues
- Small sample sizes → unreliable predictions
- All wins/all losses → can't train model
- Extreme lines → model may not have seen similar lines

### Improvements
- **Bayesian prior**: Blend model prediction with prior (e.g., 50% or historical average)
- **Line similarity matching**: If line is extreme, use predictions from similar lines
- **Minimum sample requirements**: Require more games for extreme lines

## 9. Opponent Context (if available in data)

### Features to Add
- Opponent defensive ranking for that stat
- Player's historical performance vs that opponent
- Opponent's pace (if available)

## 10. Model Evaluation Metrics

### Current
- Accuracy, AUC

### Add
- **Brier Score**: Better for probability predictions
- **Log Loss**: Penalizes confident wrong predictions
- **Calibration curve**: Visual check of probability calibration
- **Profit simulation**: Simulate betting with model predictions

## Implementation Priority

### High Impact, Easy to Implement:
1. ✅ Enhanced feature engineering (line context, trends)
2. ✅ Time-based weighting
3. ✅ Hyperparameter tuning
4. ✅ Feature selection

### High Impact, Medium Effort:
5. Better probability calibration (Platt scaling)
6. Time-based cross-validation
7. Gradient Boosting as alternative

### Medium Impact:
8. Ensemble methods
9. Bayesian priors for edge cases
10. Advanced evaluation metrics
