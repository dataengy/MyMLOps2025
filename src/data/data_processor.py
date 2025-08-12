"""
Data processing utilities for NYC Taxi data.
"""

import pandas as pd
import numpy as np
from typing import Tuple, List
from pathlib import Path


class TaxiDataProcessor:
    """Handles data cleaning, feature engineering, and preparation for ML."""
    
    def __init__(self):
        self.feature_columns = None
        
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and filter taxi data."""
        # Convert datetime columns
        datetime_cols = ['tpep_pickup_datetime', 'tpep_dropoff_datetime']
        for col in datetime_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
        
        # Calculate trip duration in seconds
        if 'tpep_pickup_datetime' in df.columns and 'tpep_dropoff_datetime' in df.columns:
            df['trip_duration'] = (
                df['tpep_dropoff_datetime'] - df['tpep_pickup_datetime']
            ).dt.total_seconds()
        
        # Data quality filters
        initial_count = len(df)
        
        # Filter valid trips
        df = df[
            # Valid trip duration (30 seconds to 3 hours)
            (df['trip_duration'] >= 30) & (df['trip_duration'] <= 10800) &
            # Valid passenger count
            (df['passenger_count'] >= 1) & (df['passenger_count'] <= 8) &
            # Valid trip distance
            (df['trip_distance'] > 0) & (df['trip_distance'] <= 100) &
            # Valid fare amount
            (df['fare_amount'] > 0) & (df['fare_amount'] <= 1000)
        ]
        
        print(f"Data cleaning: {initial_count:,} → {len(df):,} records")
        return df
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create engineered features for ML model."""
        df = df.copy()
        
        # Time-based features
        if 'tpep_pickup_datetime' in df.columns:
            df['pickup_hour'] = df['tpep_pickup_datetime'].dt.hour
            df['pickup_day'] = df['tpep_pickup_datetime'].dt.day
            df['pickup_month'] = df['tpep_pickup_datetime'].dt.month
            df['pickup_weekday'] = df['tpep_pickup_datetime'].dt.weekday
            df['pickup_is_weekend'] = (df['pickup_weekday'] >= 5).astype(int)
        
        # Hour categories
        df['hour_category'] = pd.cut(
            df['pickup_hour'], 
            bins=[0, 6, 12, 18, 24], 
            labels=['Night', 'Morning', 'Afternoon', 'Evening'],
            include_lowest=True
        )
        
        # Distance categories
        df['distance_category'] = pd.cut(
            df['trip_distance'],
            bins=[0, 2, 5, 10, float('inf')],
            labels=['Short', 'Medium', 'Long', 'Very_Long'],
            include_lowest=True
        )
        
        # Speed calculation (mph)
        df['speed_mph'] = (df['trip_distance'] / (df['trip_duration'] / 3600)).round(2)
        df['speed_mph'] = df['speed_mph'].clip(0, 100)  # Cap at reasonable speed
        
        # Airport trips (common airport location IDs)
        airport_locations = [132, 138, 161]
        df['is_airport_pickup'] = df['PULocationID'].isin(airport_locations).astype(int)
        df['is_airport_dropoff'] = df['DOLocationID'].isin(airport_locations).astype(int)
        
        # Rush hour indicator
        rush_hours = [7, 8, 9, 17, 18, 19]
        df['is_rush_hour'] = df['pickup_hour'].isin(rush_hours).astype(int)
        
        return df
    
    def prepare_model_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
        """Prepare features and target for ML model."""
        
        # Define feature columns
        feature_columns = [
            'trip_distance',
            'passenger_count',
            'pickup_hour',
            'pickup_weekday',
            'pickup_is_weekend',
            'is_rush_hour',
            'is_airport_pickup',
            'is_airport_dropoff',
            'speed_mph',
        ]
        
        # Add location features if available
        if 'PULocationID' in df.columns:
            feature_columns.append('PULocationID')
        if 'DOLocationID' in df.columns:
            feature_columns.append('DOLocationID')
        
        # Add categorical features (one-hot encoded)
        categorical_features = ['hour_category', 'distance_category']
        for cat_col in categorical_features:
            if cat_col in df.columns:
                dummies = pd.get_dummies(df[cat_col], prefix=cat_col)
                df = pd.concat([df, dummies], axis=1)
                feature_columns.extend(dummies.columns.tolist())
        
        # Select available columns
        available_features = [col for col in feature_columns if col in df.columns]
        self.feature_columns = available_features
        
        # Prepare X and y
        X = df[available_features].copy()
        y = df['trip_duration'].copy()
        
        # Remove any remaining NaN values
        mask = ~(X.isna().any(axis=1) | y.isna())
        X = X[mask]
        y = y[mask]
        
        print(f"Model data: {len(available_features)} features, {len(X):,} samples")
        
        return X, y, available_features
    
    def get_feature_importance_names(self) -> List[str]:
        """Get feature names for model interpretation."""
        return self.feature_columns if self.feature_columns else []