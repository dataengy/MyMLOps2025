"""
Test configuration and fixtures.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil
from datetime import datetime, timedelta


@pytest.fixture
def sample_taxi_data():
    """Create sample taxi data for testing."""
    np.random.seed(42)
    n_samples = 1000
    
    base_date = datetime(2024, 1, 1)
    
    data = {
        'tpep_pickup_datetime': [
            base_date + timedelta(minutes=np.random.randint(0, 60*24*30))
            for _ in range(n_samples)
        ],
        'tpep_dropoff_datetime': [],
        'trip_distance': np.random.exponential(3, n_samples),
        'passenger_count': np.random.choice([1, 2, 3, 4], n_samples, p=[0.6, 0.2, 0.15, 0.05]),
        'PULocationID': np.random.randint(1, 265, n_samples),
        'DOLocationID': np.random.randint(1, 265, n_samples),
        'fare_amount': np.random.exponential(15, n_samples) + 2.5,
    }
    
    # Generate dropoff times (pickup + trip duration)
    trip_durations = np.random.normal(600, 300, n_samples)  # ~10 minutes average
    trip_durations = np.clip(trip_durations, 60, 3600)  # 1 min to 1 hour
    
    data['tpep_dropoff_datetime'] = [
        pickup + timedelta(seconds=duration)
        for pickup, duration in zip(data['tpep_pickup_datetime'], trip_durations)
    ]
    
    df = pd.DataFrame(data)
    
    # Add trip duration
    df['trip_duration'] = (
        df['tpep_dropoff_datetime'] - df['tpep_pickup_datetime']
    ).dt.total_seconds()
    
    return df


@pytest.fixture
def temp_data_dir():
    """Create temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_features():
    """Sample feature names for testing."""
    return [
        'trip_distance',
        'passenger_count', 
        'pickup_hour',
        'pickup_weekday',
        'pickup_is_weekend',
        'is_rush_hour',
        'speed_mph'
    ]


@pytest.fixture
def sample_model_data(sample_taxi_data):
    """Processed data ready for ML model."""
    from src.data.data_processor import TaxiDataProcessor
    
    processor = TaxiDataProcessor()
    cleaned_data = processor.clean_data(sample_taxi_data)
    feature_data = processor.engineer_features(cleaned_data)
    X, y, features = processor.prepare_model_data(feature_data)
    
    return X, y, features