#!/usr/bin/env python3
"""
Data processing script for NYC Taxi data.
Cleans, validates, and engineers features for ML pipeline.
"""

import argparse
import warnings
from pathlib import Path
from typing import List, Tuple

import duckdb
import pandas as pd
from rich.console import Console
from rich.progress import track

warnings.filterwarnings('ignore')
console = Console()


def load_taxi_data(file_paths: List[Path]) -> pd.DataFrame:
    """Load and combine multiple taxi data files using DuckDB."""
    console.print(f"[blue]Loading {len(file_paths)} data files...")
    
    # Use DuckDB for efficient parquet reading
    conn = duckdb.connect()
    
    # Create a view combining all files
    file_list = "', '".join(str(p) for p in file_paths)
    query = f"""
    SELECT * FROM read_parquet(['{file_list}'])
    """
    
    df = conn.execute(query).df()
    conn.close()
    
    console.print(f"[green]Loaded {len(df):,} records from {len(file_paths)} files")
    return df


def clean_taxi_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and filter taxi data."""
    console.print("[blue]Cleaning data...")
    
    initial_count = len(df)
    
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
    filters = [
        # Valid trip duration (30 seconds to 3 hours)
        (df['trip_duration'] >= 30) & (df['trip_duration'] <= 10800),
        # Valid passenger count
        (df['passenger_count'] >= 1) & (df['passenger_count'] <= 8),
        # Valid trip distance
        (df['trip_distance'] > 0) & (df['trip_distance'] <= 100),
        # Valid fare amount
        (df['fare_amount'] > 0) & (df['fare_amount'] <= 1000),
    ]
    
    # Apply all filters
    for i, filter_condition in enumerate(filters):
        before_count = len(df)
        df = df[filter_condition]
        after_count = len(df)
        console.print(f"  Filter {i+1}: {before_count:,} → {after_count:,} records")
    
    console.print(f"[green]Cleaned data: {initial_count:,} → {len(df):,} records")
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create engineered features for ML model."""
    console.print("[blue]Engineering features...")
    
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
    
    # Airport trips (JFK, LGA, EWR common location IDs)
    airport_locations = [132, 138, 161]  # Common airport location IDs
    df['is_airport_pickup'] = df['PULocationID'].isin(airport_locations).astype(int)
    df['is_airport_dropoff'] = df['DOLocationID'].isin(airport_locations).astype(int)
    
    # Rush hour indicator
    rush_hours = [7, 8, 9, 17, 18, 19]  # 7-9 AM and 5-7 PM
    df['is_rush_hour'] = df['pickup_hour'].isin(rush_hours).astype(int)
    
    console.print(f"[green]Feature engineering complete")
    return df


def select_model_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Select and prepare features for ML model."""
    
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
        'PULocationID',
        'DOLocationID',
    ]
    
    # Add categorical features (one-hot encoded)
    categorical_features = ['hour_category', 'distance_category']
    for cat_col in categorical_features:
        if cat_col in df.columns:
            dummies = pd.get_dummies(df[cat_col], prefix=cat_col)
            df = pd.concat([df, dummies], axis=1)
            feature_columns.extend(dummies.columns.tolist())
    
    # Target column
    target_column = 'trip_duration'
    
    # Select available columns
    available_features = [col for col in feature_columns if col in df.columns]
    
    # Create final dataset
    model_df = df[available_features + [target_column]].copy()
    model_df = model_df.dropna()
    
    console.print(f"[green]Model features: {len(available_features)} features, {len(model_df):,} samples")
    
    return model_df, available_features


def save_processed_data(df: pd.DataFrame, features: List[str], output_dir: Path):
    """Save processed data for ML pipeline."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save full processed dataset
    train_path = output_dir / "processed_data.parquet"
    df.to_parquet(train_path, index=False)
    console.print(f"[green]Saved processed data: {train_path}")
    
    # Save feature list
    features_path = output_dir / "features.txt"
    with open(features_path, 'w') as f:
        for feature in features:
            f.write(f"{feature}\n")
    console.print(f"[green]Saved feature list: {features_path}")
    
    # Save data summary
    summary_path = output_dir / "data_summary.txt"
    with open(summary_path, 'w') as f:
        f.write(f"Dataset Summary\n")
        f.write(f"===============\n")
        f.write(f"Total samples: {len(df):,}\n")
        f.write(f"Features: {len(features)}\n")
        f.write(f"Target: trip_duration\n\n")
        f.write(f"Target statistics:\n")
        f.write(f"Mean: {df['trip_duration'].mean():.2f} seconds\n")
        f.write(f"Median: {df['trip_duration'].median():.2f} seconds\n")
        f.write(f"Std: {df['trip_duration'].std():.2f} seconds\n")
        f.write(f"Min: {df['trip_duration'].min():.2f} seconds\n")
        f.write(f"Max: {df['trip_duration'].max():.2f} seconds\n")
    
    console.print(f"[green]Saved data summary: {summary_path}")


def main():
    parser = argparse.ArgumentParser(description="Process NYC Taxi data for ML")
    parser.add_argument(
        "--input-dir", 
        type=Path, 
        default=Path("data/raw"),
        help="Input directory with raw parquet files"
    )
    parser.add_argument(
        "--output-dir", 
        type=Path, 
        default=Path("data/processed"),
        help="Output directory for processed data"
    )
    parser.add_argument(
        "--sample-size", 
        type=int,
        help="Sample N records for testing (use all data if not specified)"
    )
    
    args = parser.parse_args()
    
    # Find all parquet files
    parquet_files = list(args.input_dir.glob("*.parquet"))
    
    if not parquet_files:
        console.print(f"[red]No parquet files found in {args.input_dir}")
        console.print(f"[blue]Run: make data  # to download data first")
        return
    
    console.print(f"[green]Processing NYC Taxi data")
    console.print(f"[blue]Input: {args.input_dir}")
    console.print(f"[blue]Output: {args.output_dir}")
    console.print(f"[blue]Files: {len(parquet_files)}")
    
    # Load data
    df = load_taxi_data(parquet_files)
    
    # Sample if requested
    if args.sample_size and args.sample_size < len(df):
        df = df.sample(n=args.sample_size, random_state=42)
        console.print(f"[yellow]Sampled {args.sample_size:,} records for testing")
    
    # Process data
    df = clean_taxi_data(df)
    df = engineer_features(df)
    model_df, features = select_model_features(df)
    
    # Save processed data
    save_processed_data(model_df, features, args.output_dir)
    
    console.print(f"\n[green]Data processing complete!")
    console.print(f"[blue]Next steps:")
    console.print(f"  make train-baseline  # Train baseline model")
    console.print(f"  make dagster        # Start Dagster UI")


if __name__ == "__main__":
    main()