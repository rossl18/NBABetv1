"""
Modeling module for training and predicting prop probabilities
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, f_classif, VarianceThreshold
from sklearn.metrics import accuracy_score, roc_auc_score
from typing import Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class PropPredictor:
    """Class for training and predicting prop outcomes"""
    
    def __init__(self, model_type: str = 'random_forest'):
        """
        Initialize predictor
        
        Args:
            model_type: 'random_forest' or 'gradient_boosting'
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.variance_selector = None
        self.feature_selector = None
        self.is_trained = False
        # Feature name tracking:
        # - input_feature_names: columns expected at prediction time (pre-selection)
        # - feature_names: selected feature names (post-selection) for reporting/debug
        self.input_feature_names = None
        self.feature_names = None
        
    def train(self, X: pd.DataFrame, y: pd.Series, test_size: float = 0.2, random_state: int = 42, 
              sample_weight: Optional[pd.Series] = None):
        """
        Train the model on historical data
        
        Args:
            X: Feature dataframe
            y: Target series (binary)
            test_size: Proportion of data for testing
            random_state: Random seed
            sample_weight: Optional sample weights (for time-based weighting)
        """
        if len(X) == 0 or len(y) == 0:
            raise ValueError("Training data is empty")
        
        # Save the full input feature schema (pre-selection) so prediction can align correctly
        self.input_feature_names = X.columns.tolist()

        # Ensure target is binary (0/1)
        unique_values = y.unique()
        if len(unique_values) > 2:
            print(f"Warning: Target has {len(unique_values)} unique values, converting to binary")
            y = (y > 0).astype(int)
        
        if y.sum() == 0 or y.sum() == len(y):
            # All outcomes are the same - can't train meaningful model
            print(f"Warning: All outcomes are the same ({y.iloc[0]}). Using baseline probability.")
            self.is_trained = False
            self.baseline_prob = y.mean()
            return
        
        # Check if we can use stratified split (need at least 2 samples per class)
        unique_classes = y.unique()
        can_stratify = all(y.value_counts()[cls] >= 2 for cls in unique_classes) and len(unique_classes) == 2
        
        # Split data
        if can_stratify:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state, stratify=y
            )
        else:
            # Use regular split without stratification
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state
            )
        
        # Feature selection: Remove low-variance features and select top features
        # Remove features with near-zero variance (less informative)
        self.variance_selector = VarianceThreshold(threshold=0.01)
        X_train_var = self.variance_selector.fit_transform(X_train)
        X_test_var = self.variance_selector.transform(X_test)
        
        # Get feature names after variance filtering
        selected_feature_names = X_train.columns[self.variance_selector.get_support()].tolist()
        
        # Select top K features based on univariate statistical tests
        # Use min of 10 features or 80% of available features
        k_features = min(max(10, int(len(selected_feature_names) * 0.8)), len(selected_feature_names))
        
        if k_features > 0 and len(np.unique(y_train)) == 2:
            try:
                self.feature_selector = SelectKBest(score_func=f_classif, k=k_features)
                X_train_selected = self.feature_selector.fit_transform(X_train_var, y_train)
                X_test_selected = self.feature_selector.transform(X_test_var)
                
                # Update feature names to only include selected features
                selected_indices = self.feature_selector.get_support(indices=True)
                self.feature_names = [selected_feature_names[i] for i in selected_indices]
            except Exception as e:
                print(f"  Warning: Feature selection failed ({e}), using all features")
                X_train_selected = X_train_var
                X_test_selected = X_test_var
                self.feature_names = selected_feature_names
                self.feature_selector = None
        else:
            # Not enough features or not binary classification, skip feature selection
            X_train_selected = X_train_var
            X_test_selected = X_test_var
            self.feature_names = selected_feature_names
            self.feature_selector = None
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train_selected)
        X_test_scaled = self.scaler.transform(X_test_selected)
        
        # Prepare sample weights if provided
        train_weights = None
        if sample_weight is not None:
            train_weights = sample_weight.loc[X_train.index].values
        
        # Initialize model with optimized hyperparameters
        if self.model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=200,  # Increased from 100 for better generalization
                max_depth=12,  # Slightly increased from 10
                min_samples_split=10,  # Increased from 5 to reduce overfitting
                min_samples_leaf=5,  # Increased from 2 to reduce overfitting
                max_features='sqrt',  # Use sqrt of features (best practice for RF)
                class_weight='balanced',  # Handle class imbalance
                random_state=random_state,
                n_jobs=-1
            )
        elif self.model_type == 'gradient_boosting':
            self.model = GradientBoostingClassifier(
                n_estimators=150,  # Increased from 100
                max_depth=6,  # Increased from 5
                learning_rate=0.08,  # Slightly reduced for better generalization
                min_samples_split=10,
                min_samples_leaf=5,
                random_state=random_state
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
        
        # Train model with sample weights if provided
        if train_weights is not None:
            self.model.fit(X_train_scaled, y_train, sample_weight=train_weights)
        else:
            self.model.fit(X_train_scaled, y_train)
        
        self.training_samples = len(X_train)
        self.is_trained = True
        
        # Evaluate
        train_pred = self.model.predict(X_train_scaled)
        test_pred = self.model.predict(X_test_scaled)
        train_proba = self.model.predict_proba(X_train_scaled)[:, 1]
        test_proba = self.model.predict_proba(X_test_scaled)[:, 1]
        
        train_acc = accuracy_score(y_train, train_pred)
        test_acc = accuracy_score(y_test, test_pred)
        
        # Only calculate AUC for binary classification
        train_auc = 0.5
        test_auc = 0.5
        if len(np.unique(y_train)) == 2 and len(np.unique(y_test)) == 2:
            try:
                train_auc = roc_auc_score(y_train, train_proba)
                test_auc = roc_auc_score(y_test, test_proba)
            except Exception as e:
                print(f"Warning: Could not calculate AUC: {e}")
        
        print(f"Model trained - Train Acc: {train_acc:.3f}, Test Acc: {test_acc:.3f}, "
              f"Train AUC: {train_auc:.3f}, Test AUC: {test_auc:.3f}")
    
    def predict_probability(self, X: pd.DataFrame) -> float:
        """
        Predict probability of prop hitting
        
        Args:
            X: Feature dataframe (should be last row or aggregated features)
        
        Returns:
            Probability (0-1) that prop will hit
        """
        if not self.is_trained:
            # Return baseline probability if model not trained
            if hasattr(self, 'baseline_prob'):
                return self.baseline_prob
            else:
                return 0.5  # Default to 50% if no training data
        
        # Use most recent row if multiple rows provided
        if len(X) > 1:
            X = X.iloc[[-1]]
        
        # Align to the training-time input feature schema (pre-selection)
        if self.input_feature_names:
            missing_features = set(self.input_feature_names) - set(X.columns)
            if missing_features:
                # Keep noise low: only print if we're genuinely missing expected inputs
                print(f"Warning: Missing features {missing_features}, filling with 0")
                for feat in missing_features:
                    X[feat] = 0
            X = X[self.input_feature_names]
        
        # Convert to numpy array for feature selection
        X_array = X.values if isinstance(X, pd.DataFrame) else X
        # Ensure no NaNs/infs reach sklearn selectors
        X_array = np.nan_to_num(X_array, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Apply variance threshold if used during training
        if self.variance_selector is not None:
            X_var = self.variance_selector.transform(X_array)
        else:
            X_var = X_array
        
        # Apply feature selection if used during training
        if self.feature_selector is not None:
            X_selected = self.feature_selector.transform(X_var)
        else:
            X_selected = X_var
        
        # Scale and predict
        X_scaled = self.scaler.transform(X_selected)
        proba = self.model.predict_proba(X_scaled)[0, 1]
        
        # Apply probability calibration to prevent extreme values and account for model uncertainty
        # Use sigmoid-like compression to pull probabilities away from 0 and 1
        calibrated_proba = self._calibrate_probability(proba)
        
        return float(calibrated_proba)
    
    def predict_probability_with_ci(self, X: pd.DataFrame, confidence: float = 0.95) -> tuple:
        """
        Predict probability with 95% confidence interval using Random Forest tree variance
        
        Args:
            X: Feature dataframe (should be last row or aggregated features)
            confidence: Confidence level (default 0.95 for 95% CI)
        
        Returns:
            Tuple of (probability, lower_bound, upper_bound)
        """
        if not self.is_trained:
            # Return baseline probability if model not trained
            if hasattr(self, 'baseline_prob'):
                prob = self.baseline_prob
            else:
                prob = 0.5
            # For untrained model, return wide CI
            return prob, max(0.0, prob - 0.2), min(1.0, prob + 0.2)
        
        # Use most recent row if multiple rows provided
        if len(X) > 1:
            X = X.iloc[[-1]]
        
        # Align to the training-time input feature schema (pre-selection)
        if self.input_feature_names:
            missing_features = set(self.input_feature_names) - set(X.columns)
            if missing_features:
                print(f"Warning: Missing features {missing_features}, filling with 0")
                for feat in missing_features:
                    X[feat] = 0
            X = X[self.input_feature_names]
        
        # Apply variance threshold if used during training
        X_array = X.values if isinstance(X, pd.DataFrame) else X
        X_array = np.nan_to_num(X_array, nan=0.0, posinf=0.0, neginf=0.0)
        if self.variance_selector is not None:
            X_var = self.variance_selector.transform(X_array)
        else:
            X_var = X_array
        
        # Apply feature selection if used during training
        if self.feature_selector is not None:
            X_selected = self.feature_selector.transform(X_var)
        else:
            X_selected = X_var
        
        # Scale and get predictions
        X_scaled = self.scaler.transform(X_selected)
        
        # Get predictions from all trees (for Random Forest)
        if self.model_type == 'random_forest' and hasattr(self.model, 'estimators_'):
            # Get probability predictions from each tree
            tree_probas = []
            for tree in self.model.estimators_:
                tree_proba = tree.predict_proba(X_scaled)[0, 1]
                tree_probas.append(tree_proba)
            
            # Calculate mean and standard deviation
            mean_proba = np.mean(tree_probas)
            std_proba = np.std(tree_probas)
            
            # Apply calibration to mean probability
            calibrated_mean = self._calibrate_probability(mean_proba)
            
            # Calculate confidence interval using normal approximation
            # For 95% CI, z = 1.96
            z_score = 1.96 if confidence == 0.95 else 2.576 if confidence == 0.99 else 1.645
            
            # Calibrate bounds as well, but keep them wider to account for uncertainty
            lower = max(0.0, mean_proba - z_score * std_proba)
            upper = min(1.0, mean_proba + z_score * std_proba)
            calibrated_lower = self._calibrate_probability(lower)
            calibrated_upper = self._calibrate_probability(upper)
            
            return float(calibrated_mean), float(calibrated_lower), float(calibrated_upper)
        else:
            # Fallback: use single prediction with estimated uncertainty
            # Apply variance threshold if used during training
            X_array = X.values if isinstance(X, pd.DataFrame) else X
            X_array = np.nan_to_num(X_array, nan=0.0, posinf=0.0, neginf=0.0)
            if self.variance_selector is not None:
                X_var = self.variance_selector.transform(X_array)
            else:
                X_var = X_array
            
            # Apply feature selection if used during training
            if self.feature_selector is not None:
                X_selected = self.feature_selector.transform(X_var)
            else:
                X_selected = X_var
            
            X_scaled = self.scaler.transform(X_selected)
            proba = self.model.predict_proba(X_scaled)[0, 1]
            
            # Apply calibration
            calibrated_proba = self._calibrate_probability(proba)
            
            # Estimate uncertainty based on training sample size
            # Rough approximation: larger sample = smaller uncertainty
            if hasattr(self, 'training_samples'):
                n = self.training_samples
                # Standard error approximation for proportion
                se = np.sqrt(proba * (1 - proba) / n) if n > 0 else 0.1
            else:
                se = 0.05  # Default uncertainty
            
            z_score = 1.96 if confidence == 0.95 else 2.576 if confidence == 0.99 else 1.645
            lower = max(0.0, proba - z_score * se)
            upper = min(1.0, proba + z_score * se)
            
            # Calibrate bounds
            calibrated_lower = self._calibrate_probability(lower)
            calibrated_upper = self._calibrate_probability(upper)
            
            return float(calibrated_proba), float(calibrated_lower), float(calibrated_upper)
    
    def _calibrate_probability(self, prob: float, compression_factor: float = 0.05, implied_prob: float = None) -> float:
        """
        Calibrate probability to prevent extreme values (0% or 100%)
        and account for model uncertainty/noise. Much more aggressive calibration.
        
        Uses a sigmoid-like compression that pulls probabilities away from extremes.
        Also considers implied probability from odds as a sanity check.
        
        Args:
            prob: Raw probability (0-1)
            compression_factor: Amount to compress from edges (default 0.05 = 5%)
            implied_prob: Implied probability from odds (optional, used as sanity check)
        
        Returns:
            Calibrated probability (much more conservative range)
        """
        # Clamp to valid range first
        prob = max(0.0, min(1.0, prob))
        
        # MUCH MORE AGGRESSIVE CALIBRATION
        # Cap maximum probability at 75% (down from 90%)
        # This prevents overconfidence on high-odds bets
        
        if prob > 0.90:
            # Map [0.90, 1.0] to [0.65, 0.75] - so 100% becomes 75% max
            excess = (prob - 0.90) / 0.10  # Normalize to [0, 1]
            calibrated = 0.65 + excess * 0.10  # Map to [0.65, 0.75]
        elif prob > 0.75:
            # Map [0.75, 0.90] to [0.60, 0.65] - compress high probabilities
            excess = (prob - 0.75) / 0.15  # Normalize to [0, 1]
            calibrated = 0.60 + excess * 0.05  # Map to [0.60, 0.65]
        elif prob < 0.10:
            # Map [0.0, 0.10] to [0.10, 0.20] - so 0% becomes ~10%
            excess = prob / 0.10  # Normalize to [0, 1]
            calibrated = 0.10 + excess * 0.10  # Map to [0.10, 0.20]
        else:
            # For middle probabilities [0.10, 0.75], compress to [0.20, 0.60]
            normalized = (prob - 0.10) / 0.65  # Normalize to [0, 1]
            calibrated = 0.20 + normalized * 0.40  # Map to [0.20, 0.60]
        
        # If we have implied probability, use it as a sanity check
        # If model probability is way off from market, blend them
        if implied_prob is not None and not np.isnan(implied_prob):
            implied_prob = max(0.05, min(0.95, implied_prob))  # Clamp implied prob
            
            # If calibrated prob is way higher than implied (e.g., 75% vs 40%),
            # blend them to prevent extreme overconfidence
            if calibrated > implied_prob + 0.20:  # More than 20% higher
                # Blend: 60% model, 40% implied (trust market more when model is way off)
                calibrated = 0.6 * calibrated + 0.4 * implied_prob
            elif calibrated < implied_prob - 0.20:  # More than 20% lower
                # Blend: 60% model, 40% implied
                calibrated = 0.6 * calibrated + 0.4 * implied_prob
        
        return max(0.10, min(0.75, calibrated))  # Final clamp to [10%, 75%]
    
    def predict_from_historical(self, historical_df: pd.DataFrame, prop_type: str, feature_prep_func, line: float = None) -> float:
        """
        Convenience method to predict from raw historical dataframe
        
        Args:
            historical_df: Historical data dataframe
            prop_type: Type of prop
            feature_prep_func: Function to prepare features (from feature_engineering module)
            line: Line value (optional, passed to feature_prep_func)
        
        Returns:
            Probability of hitting
        """
        features = feature_prep_func(historical_df, prop_type, line=line)
        if len(features) == 0:
            return 0.5
        
        # Use most recent game's features
        return self.predict_probability(features.iloc[[-1]])
