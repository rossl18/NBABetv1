"""
Modeling module for training and predicting prop probabilities
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
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
        self.is_trained = False
        self.feature_names = None
        
    def train(self, X: pd.DataFrame, y: pd.Series, test_size: float = 0.2, random_state: int = 42):
        """
        Train the model on historical data
        
        Args:
            X: Feature dataframe
            y: Target series (binary)
            test_size: Proportion of data for testing
            random_state: Random seed
        """
        if len(X) == 0 or len(y) == 0:
            raise ValueError("Training data is empty")
        
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
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Initialize model
        if self.model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=random_state,
                n_jobs=-1
            )
        elif self.model_type == 'gradient_boosting':
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=random_state
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        self.feature_names = X.columns.tolist()
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
        
        # Ensure features match training features
        if self.feature_names:
            missing_features = set(self.feature_names) - set(X.columns)
            if missing_features:
                print(f"Warning: Missing features {missing_features}, filling with 0")
                for feat in missing_features:
                    X[feat] = 0
            X = X[self.feature_names]
        
        # Scale and predict
        X_scaled = self.scaler.transform(X)
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
        
        # Ensure features match training features
        if self.feature_names:
            missing_features = set(self.feature_names) - set(X.columns)
            if missing_features:
                print(f"Warning: Missing features {missing_features}, filling with 0")
                for feat in missing_features:
                    X[feat] = 0
            X = X[self.feature_names]
        
        # Scale and predict
        X_scaled = self.scaler.transform(X)
        
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
    
    def _calibrate_probability(self, prob: float, compression_factor: float = 0.03) -> float:
        """
        Calibrate probability to prevent extreme values (0% or 100%)
        and account for model uncertainty/noise.
        
        Uses a sigmoid-like compression that pulls probabilities away from extremes.
        compression_factor: How much to compress (0.03 = 3% compression from edges)
        
        Args:
            prob: Raw probability (0-1)
            compression_factor: Amount to compress from edges (default 0.03 = 3%)
        
        Returns:
            Calibrated probability (compression_factor to 1-compression_factor range)
        """
        # Clamp to valid range first
        prob = max(0.0, min(1.0, prob))
        
        # Apply compression: map [0,1] to [compression_factor, 1-compression_factor]
        # This prevents 0% and 100% predictions while keeping most of the signal
        # 3% compression means 97% max probability, which is more realistic
        calibrated = compression_factor + prob * (1 - 2 * compression_factor)
        
        return calibrated
    
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
