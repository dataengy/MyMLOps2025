"""
Tests for model training module.
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
from pathlib import Path
from src.models.trainer import ModelTrainer, evaluate_model_performance


class TestModelTrainer:
    """Test cases for ModelTrainer."""
    
    def test_baseline_model_training(self, sample_model_data):
        """Test baseline model training."""
        X, y, features = sample_model_data
        
        trainer = ModelTrainer(model_type="baseline")
        model, metrics = trainer.train(X, y)
        
        # Check model is trained
        assert trainer.model is not None
        assert trainer.scaler is not None  # Linear model should use scaler
        
        # Check metrics
        assert "train_rmse" in metrics
        assert "train_mae" in metrics
        assert "train_r2" in metrics
        assert metrics["model_type"] == "baseline"
        assert metrics["train_samples"] == len(X)
        
        # Check model can make predictions
        predictions = trainer.predict(X.head(10))
        assert len(predictions) == 10
        assert all(pred > 0 for pred in predictions)  # Trip duration should be positive
    
    def test_random_forest_model_training(self, sample_model_data):
        """Test random forest model training."""
        X, y, features = sample_model_data
        
        trainer = ModelTrainer(model_type="random_forest")
        model, metrics = trainer.train(X, y)
        
        # Check model is trained
        assert trainer.model is not None
        assert trainer.scaler is None  # Tree models don't need scaling
        
        # Check metrics
        assert "train_rmse" in metrics
        assert "train_mae" in metrics
        assert "train_r2" in metrics
        assert metrics["model_type"] == "random_forest"
        
        # Check model can make predictions
        predictions = trainer.predict(X.head(10))
        assert len(predictions) == 10
        assert all(pred > 0 for pred in predictions)
    
    def test_train_test_split_metrics(self, sample_model_data):
        """Test training with train/test split."""
        X, y, features = sample_model_data
        
        # Split data manually
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        trainer = ModelTrainer(model_type="baseline")
        model, metrics = trainer.train(X_train, y_train, X_test, y_test)
        
        # Should have both train and test metrics
        assert "train_rmse" in metrics
        assert "test_rmse" in metrics
        assert "train_mae" in metrics
        assert "test_mae" in metrics
        assert "train_r2" in metrics
        assert "test_r2" in metrics
        assert metrics["train_samples"] == len(X_train)
        assert metrics["test_samples"] == len(X_test)
    
    def test_model_save_load(self, sample_model_data, temp_data_dir):
        """Test model saving and loading."""
        X, y, features = sample_model_data
        
        # Train model
        trainer = ModelTrainer(model_type="baseline")
        model, metrics = trainer.train(X, y)
        
        # Save model
        model_path = temp_data_dir / "test_model.pkl"
        trainer.save_model(model_path)
        assert model_path.exists()
        
        # Load model
        loaded_trainer = ModelTrainer.load_model(model_path)
        assert loaded_trainer.model_type == "baseline"
        assert loaded_trainer.model is not None
        assert loaded_trainer.scaler is not None
        
        # Check predictions are the same
        original_predictions = trainer.predict(X.head(10))
        loaded_predictions = loaded_trainer.predict(X.head(10))
        np.testing.assert_array_almost_equal(original_predictions, loaded_predictions)
    
    def test_feature_importance(self, sample_model_data):
        """Test feature importance extraction."""
        X, y, features = sample_model_data
        
        # Test with random forest (has feature_importances_)
        rf_trainer = ModelTrainer(model_type="random_forest")
        rf_model, rf_metrics = rf_trainer.train(X, y)
        
        rf_importance = rf_trainer.get_feature_importance(features)
        assert isinstance(rf_importance, dict)
        assert len(rf_importance) == len(features)
        assert all(isinstance(v, (int, float)) for v in rf_importance.values())
        
        # Test with linear model (has coef_)
        lr_trainer = ModelTrainer(model_type="baseline")
        lr_model, lr_metrics = lr_trainer.train(X, y)
        
        lr_importance = lr_trainer.get_feature_importance(features)
        assert isinstance(lr_importance, dict)
        assert len(lr_importance) == len(features)
    
    def test_invalid_model_type(self):
        """Test handling of invalid model type."""
        with pytest.raises(ValueError, match="Unknown model type"):
            trainer = ModelTrainer(model_type="invalid_model")
            trainer.get_model()
    
    def test_predict_without_training(self, sample_model_data):
        """Test prediction without training should raise error."""
        X, y, features = sample_model_data
        
        trainer = ModelTrainer(model_type="baseline")
        
        with pytest.raises(ValueError, match="Model not trained yet"):
            trainer.predict(X.head(10))


class TestEvaluateModelPerformance:
    """Test cases for model evaluation utilities."""
    
    def test_evaluate_model_performance(self):
        """Test model performance evaluation function."""
        # Create sample true and predicted values
        np.random.seed(42)
        y_true = np.random.normal(600, 200, 100)  # Trip durations around 10 minutes
        y_pred = y_true + np.random.normal(0, 50, 100)  # Add some error
        
        metrics = evaluate_model_performance(y_true, y_pred)
        
        # Check all expected metrics are present
        expected_metrics = [
            "rmse", "mae", "r2_score", "mape",
            "mean_residual", "std_residual", 
            "min_residual", "max_residual", "n_samples"
        ]
        
        for metric in expected_metrics:
            assert metric in metrics
        
        # Check metric values are reasonable
        assert metrics["rmse"] > 0
        assert metrics["mae"] > 0
        assert -1 <= metrics["r2_score"] <= 1
        assert metrics["mape"] >= 0
        assert metrics["n_samples"] == 100
        
        # Residuals should be centered around 0
        assert abs(metrics["mean_residual"]) < 20  # Should be close to 0
        assert metrics["std_residual"] > 0
    
    def test_perfect_predictions(self):
        """Test evaluation with perfect predictions."""
        y_true = np.array([100, 200, 300, 400, 500])
        y_pred = y_true.copy()  # Perfect predictions
        
        metrics = evaluate_model_performance(y_true, y_pred)
        
        # Perfect predictions should have specific metric values
        assert metrics["rmse"] == 0
        assert metrics["mae"] == 0
        assert metrics["r2_score"] == 1.0
        assert metrics["mape"] == 0
        assert metrics["mean_residual"] == 0
        assert metrics["std_residual"] == 0