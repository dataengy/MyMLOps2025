"""
ML model training utilities.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Any
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
import pickle
from pathlib import Path


class ModelTrainer:
    """Handles model training and evaluation."""
    
    def __init__(self, model_type: str = "baseline"):
        self.model_type = model_type
        self.model = None
        self.scaler = None
        
    def get_model(self):
        """Get model instance based on type."""
        if self.model_type == "baseline":
            return LinearRegression()
        elif self.model_type == "random_forest":
            return RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
    
    def train(
        self, 
        X_train: pd.DataFrame, 
        y_train: pd.Series,
        X_test: pd.DataFrame = None,
        y_test: pd.Series = None
    ) -> Tuple[Any, Dict]:
        """Train model and return model with metrics."""
        
        # Initialize model
        self.model = self.get_model()
        
        # Scale features for linear models
        if self.model_type == "baseline":
            self.scaler = StandardScaler()
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test) if X_test is not None else None
            self.model.fit(X_train_scaled, y_train)
        else:
            # Tree-based models don't need scaling
            X_train_scaled = X_train
            X_test_scaled = X_test if X_test is not None else None
            self.model.fit(X_train_scaled, y_train)
        
        # Calculate metrics
        metrics = self._calculate_metrics(
            X_train_scaled, y_train, X_test_scaled, y_test
        )
        
        return self.model, metrics
    
    def _calculate_metrics(
        self, 
        X_train, 
        y_train, 
        X_test=None, 
        y_test=None
    ) -> Dict:
        """Calculate model performance metrics."""
        
        # Training predictions
        y_train_pred = self.model.predict(X_train)
        
        metrics = {
            "model_type": self.model_type,
            "train_rmse": np.sqrt(mean_squared_error(y_train, y_train_pred)),
            "train_mae": mean_absolute_error(y_train, y_train_pred),
            "train_r2": r2_score(y_train, y_train_pred),
            "train_samples": len(y_train),
        }
        
        # Test predictions if provided
        if X_test is not None and y_test is not None:
            y_test_pred = self.model.predict(X_test)
            metrics.update({
                "test_rmse": np.sqrt(mean_squared_error(y_test, y_test_pred)),
                "test_mae": mean_absolute_error(y_test, y_test_pred),
                "test_r2": r2_score(y_test, y_test_pred),
                "test_samples": len(y_test),
            })
        
        return metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions using trained model."""
        if self.model is None:
            raise ValueError("Model not trained yet")
        
        if self.scaler is not None:
            X_scaled = self.scaler.transform(X)
            return self.model.predict(X_scaled)
        else:
            return self.model.predict(X)
    
    def save_model(self, filepath: Path):
        """Save trained model and scaler."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        model_data = {
            "model": self.model,
            "scaler": self.scaler,
            "model_type": self.model_type
        }
        
        with open(filepath, "wb") as f:
            pickle.dump(model_data, f)
    
    @classmethod
    def load_model(cls, filepath: Path):
        """Load trained model."""
        with open(filepath, "rb") as f:
            model_data = pickle.load(f)
        
        trainer = cls(model_type=model_data["model_type"])
        trainer.model = model_data["model"]
        trainer.scaler = model_data["scaler"]
        
        return trainer
    
    def get_feature_importance(self, feature_names: list) -> Dict[str, float]:
        """Get feature importance for tree-based models."""
        if hasattr(self.model, 'feature_importances_'):
            importance = dict(zip(feature_names, self.model.feature_importances_))
            # Sort by importance
            return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
        elif hasattr(self.model, 'coef_'):
            # For linear models, use absolute coefficients
            importance = dict(zip(feature_names, np.abs(self.model.coef_)))
            return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
        else:
            return {}


def evaluate_model_performance(y_true: np.ndarray, y_pred: np.ndarray) -> Dict:
    """Evaluate model performance with comprehensive metrics."""
    
    # Basic regression metrics
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    
    # Additional metrics
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100  # MAPE
    residuals = y_true - y_pred
    
    return {
        "rmse": rmse,
        "mae": mae,
        "r2_score": r2,
        "mape": mape,
        "mean_residual": np.mean(residuals),
        "std_residual": np.std(residuals),
        "min_residual": np.min(residuals),
        "max_residual": np.max(residuals),
        "n_samples": len(y_true)
    }