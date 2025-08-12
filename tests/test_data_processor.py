"""
Tests for data processing module.
"""

import pytest
import pandas as pd
import numpy as np
from src.data.data_processor import TaxiDataProcessor


class TestTaxiDataProcessor:
    """Test cases for TaxiDataProcessor."""
    
    def test_clean_data(self, sample_taxi_data):
        """Test data cleaning functionality."""
        processor = TaxiDataProcessor()
        cleaned_data = processor.clean_data(sample_taxi_data)
        
        # Check that data is cleaned
        assert len(cleaned_data) <= len(sample_taxi_data)
        assert cleaned_data['trip_duration'].min() >= 30
        assert cleaned_data['trip_duration'].max() <= 10800
        assert cleaned_data['passenger_count'].min() >= 1
        assert cleaned_data['passenger_count'].max() <= 8
        assert cleaned_data['trip_distance'].min() > 0
        assert cleaned_data['fare_amount'].min() > 0
    
    def test_engineer_features(self, sample_taxi_data):
        """Test feature engineering."""
        processor = TaxiDataProcessor()
        cleaned_data = processor.clean_data(sample_taxi_data)
        feature_data = processor.engineer_features(cleaned_data)
        
        # Check that new features are created
        expected_features = [
            'pickup_hour', 'pickup_weekday', 'pickup_is_weekend',
            'is_rush_hour', 'speed_mph', 'hour_category', 'distance_category'
        ]
        
        for feature in expected_features:
            assert feature in feature_data.columns
        
        # Check feature value ranges
        assert feature_data['pickup_hour'].min() >= 0
        assert feature_data['pickup_hour'].max() <= 23
        assert feature_data['pickup_weekday'].min() >= 0
        assert feature_data['pickup_weekday'].max() <= 6
        assert feature_data['pickup_is_weekend'].isin([0, 1]).all()
        assert feature_data['is_rush_hour'].isin([0, 1]).all()
    
    def test_prepare_model_data(self, sample_taxi_data):
        """Test model data preparation."""
        processor = TaxiDataProcessor()
        cleaned_data = processor.clean_data(sample_taxi_data)
        feature_data = processor.engineer_features(cleaned_data)
        X, y, features = processor.prepare_model_data(feature_data)
        
        # Check data shapes
        assert len(X) == len(y)
        assert len(features) > 0
        assert X.shape[1] == len(features)
        
        # Check that there are no NaN values
        assert not X.isnull().any().any()
        assert not y.isnull().any()
        
        # Check target variable
        assert y.min() > 0  # Trip duration should be positive
        
        # Check feature names
        assert isinstance(features, list)
        assert all(isinstance(f, str) for f in features)
    
    def test_feature_columns_consistency(self, sample_taxi_data):
        """Test that feature columns are consistent across calls."""
        processor = TaxiDataProcessor()
        cleaned_data = processor.clean_data(sample_taxi_data)
        feature_data = processor.engineer_features(cleaned_data)
        
        # First call
        X1, y1, features1 = processor.prepare_model_data(feature_data)
        
        # Second call with same data
        X2, y2, features2 = processor.prepare_model_data(feature_data)
        
        # Features should be identical
        assert features1 == features2
        assert list(X1.columns) == list(X2.columns)
        
        # Data should be identical
        pd.testing.assert_frame_equal(X1, X2)
        pd.testing.assert_series_equal(y1, y2)
    
    def test_empty_data_handling(self):
        """Test handling of empty data."""
        processor = TaxiDataProcessor()
        
        # Create empty DataFrame with required columns
        empty_df = pd.DataFrame(columns=[
            'tpep_pickup_datetime', 'tpep_dropoff_datetime',
            'trip_distance', 'passenger_count', 'fare_amount'
        ])
        
        cleaned_data = processor.clean_data(empty_df)
        assert len(cleaned_data) == 0
    
    def test_invalid_data_filtering(self):
        """Test that invalid data is filtered out."""
        # Create data with invalid values
        invalid_data = pd.DataFrame({
            'tpep_pickup_datetime': pd.to_datetime(['2024-01-01 10:00:00']),
            'tpep_dropoff_datetime': pd.to_datetime(['2024-01-01 10:00:10']),  # 10 second trip
            'trip_distance': [0],  # Invalid distance
            'passenger_count': [0],  # Invalid passenger count
            'fare_amount': [-5],  # Invalid fare
        })
        
        invalid_data['trip_duration'] = (
            invalid_data['tpep_dropoff_datetime'] - invalid_data['tpep_pickup_datetime']
        ).dt.total_seconds()
        
        processor = TaxiDataProcessor()
        cleaned_data = processor.clean_data(invalid_data)
        
        # Should filter out all invalid records
        assert len(cleaned_data) == 0