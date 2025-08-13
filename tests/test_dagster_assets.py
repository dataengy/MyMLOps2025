"""
Tests for Dagster assets.
"""

import pytest
import pandas as pd
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the assets (may need mocking for dependencies)
try:
    from src.dagster_app.assets import (
        raw_taxi_data, processed_taxi_data, trained_model, 
        model_metrics, data_drift_report
    )
except ImportError:
    # Mock if imports fail due to missing dependencies
    raw_taxi_data = None


class TestDagsterAssets:
    """Test cases for Dagster assets."""
    
    @pytest.mark.skipif(raw_taxi_data is None, reason="Dagster assets not available")
    def test_asset_definitions_exist(self):
        """Test that all required assets are defined."""
        from src.dagster_app.assets import (
            raw_taxi_data, processed_taxi_data, trained_model,
            model_metrics, data_drift_report
        )
        
        # Check assets are callable
        assert callable(raw_taxi_data)
        assert callable(processed_taxi_data)  
        assert callable(trained_model)
        assert callable(model_metrics)
        assert callable(data_drift_report)
    
    @patch('src.dagster_app.assets.download_sample_data')
    def test_raw_taxi_data_asset(self, mock_download, sample_taxi_data):
        """Test raw taxi data asset."""
        if raw_taxi_data is None:
            pytest.skip("Dagster assets not available")
        
        mock_download.return_value = sample_taxi_data
        
        # This would be called by Dagster in practice
        result = raw_taxi_data()
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        assert 'tpep_pickup_datetime' in result.columns
    
    @patch('src.dagster_app.assets.TaxiDataProcessor')
    def test_processed_taxi_data_asset(self, mock_processor, sample_taxi_data):
        """Test processed taxi data asset."""
        if processed_taxi_data is None:
            pytest.skip("Dagster assets not available")
        
        # Mock processor
        mock_processor_instance = MagicMock()
        mock_processor_instance.clean_data.return_value = sample_taxi_data
        mock_processor_instance.engineer_features.return_value = sample_taxi_data
        mock_processor.return_value = mock_processor_instance
        
        # This would be called by Dagster with raw data as input
        result = processed_taxi_data(sample_taxi_data)
        
        assert isinstance(result, pd.DataFrame)
        mock_processor_instance.clean_data.assert_called_once()
        mock_processor_instance.engineer_features.assert_called_once()
    
    @patch('src.dagster_app.assets.ModelTrainer')
    @patch('src.dagster_app.assets.TaxiDataProcessor')
    def test_trained_model_asset(self, mock_processor, mock_trainer, sample_taxi_data):
        """Test trained model asset."""
        if trained_model is None:
            pytest.skip("Dagster assets not available")
        
        # Mock processor
        mock_processor_instance = MagicMock()
        mock_processor_instance.prepare_model_data.return_value = (
            sample_taxi_data.iloc[:, :5],  # X
            sample_taxi_data['trip_duration'],  # y  
            ['feature1', 'feature2']  # features
        )
        mock_processor.return_value = mock_processor_instance
        
        # Mock trainer
        mock_trainer_instance = MagicMock()
        mock_trainer_instance.train.return_value = (MagicMock(), {"rmse": 100})
        mock_trainer.return_value = mock_trainer_instance
        
        # This would be called by Dagster with processed data
        result = trained_model(sample_taxi_data)
        
        # Should return trainer object
        assert result is not None
        mock_trainer_instance.train.assert_called_once()