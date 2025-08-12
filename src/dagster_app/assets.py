"""
Dagster assets for NYC Taxi MLOps pipeline.
"""

import pandas as pd
from dagster import asset, AssetIn, Config
from pathlib import Path
import duckdb
from typing import List, Tuple
import pickle

from ..data.data_processor import TaxiDataProcessor
from ..models.trainer import ModelTrainer


class DataConfig(Config):
    """Configuration for data processing."""
    sample_size: int = None
    data_dir: str = "data"
    force_refresh: bool = False


class ModelConfig(Config):
    """Configuration for model training."""
    model_type: str = "baseline"
    test_size: float = 0.2
    random_state: int = 42


@asset(description="Raw NYC taxi trip data downloaded from TLC website")
def raw_taxi_data(config: DataConfig) -> pd.DataFrame:
    """Load raw taxi data from parquet files."""
    data_dir = Path(config.data_dir) / "raw"
    parquet_files = list(data_dir.glob("*.parquet"))
    
    if not parquet_files:
        raise FileNotFoundError(f"No parquet files found in {data_dir}")
    
    # Use DuckDB for efficient parquet reading
    conn = duckdb.connect()
    file_list = "', '".join(str(p) for p in parquet_files)
    query = f"SELECT * FROM read_parquet(['{file_list}'])"
    
    df = conn.execute(query).df()
    conn.close()
    
    # Sample if requested
    if config.sample_size and config.sample_size < len(df):
        df = df.sample(n=config.sample_size, random_state=42)
    
    return df


@asset(description="Cleaned and validated taxi data")
def cleaned_taxi_data(raw_taxi_data: pd.DataFrame) -> pd.DataFrame:
    """Clean and validate taxi data."""
    processor = TaxiDataProcessor()
    return processor.clean_data(raw_taxi_data)


@asset(description="Feature engineered dataset ready for ML")
def feature_engineered_data(cleaned_taxi_data: pd.DataFrame) -> pd.DataFrame:
    """Engineer features for ML model."""
    processor = TaxiDataProcessor()
    return processor.engineer_features(cleaned_taxi_data)


@asset(description="Train/test split datasets")
def train_test_data(
    feature_engineered_data: pd.DataFrame, 
    config: ModelConfig
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Split data into train and test sets."""
    from sklearn.model_selection import train_test_split
    
    processor = TaxiDataProcessor()
    X, y, features = processor.prepare_model_data(feature_engineered_data)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=config.test_size, 
        random_state=config.random_state,
        stratify=None  # For regression
    )
    
    return X_train, X_test, y_train, y_test


@asset(description="Trained ML model")
def trained_model(
    train_test_data: Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series],
    config: ModelConfig
) -> dict:
    """Train ML model for trip duration prediction."""
    X_train, X_test, y_train, y_test = train_test_data
    
    trainer = ModelTrainer(model_type=config.model_type)
    model, metrics = trainer.train(X_train, y_train, X_test, y_test)
    
    return {
        "model": model,
        "metrics": metrics,
        "feature_names": list(X_train.columns)
    }


@asset(description="Model evaluation results")
def model_evaluation(
    trained_model: dict,
    train_test_data: Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]
) -> dict:
    """Evaluate trained model performance."""
    model = trained_model["model"]
    X_train, X_test, y_train, y_test = train_test_data
    
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    import numpy as np
    
    # Predictions
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    
    # Metrics
    evaluation = {
        "train_rmse": np.sqrt(mean_squared_error(y_train, y_train_pred)),
        "test_rmse": np.sqrt(mean_squared_error(y_test, y_test_pred)),
        "train_mae": mean_absolute_error(y_train, y_train_pred),
        "test_mae": mean_absolute_error(y_test, y_test_pred),
        "train_r2": r2_score(y_train, y_train_pred),
        "test_r2": r2_score(y_test, y_test_pred),
        "train_samples": len(y_train),
        "test_samples": len(y_test),
    }
    
    return evaluation


@asset(description="Saved model artifacts")
def model_artifacts(
    trained_model: dict,
    model_evaluation: dict
) -> str:
    """Save model and evaluation results."""
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # Save model
    model_path = models_dir / "trip_duration_model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(trained_model["model"], f)
    
    # Save metrics
    metrics_path = models_dir / "model_metrics.pkl"
    with open(metrics_path, "wb") as f:
        pickle.dump(model_evaluation, f)
    
    # Save feature names
    features_path = models_dir / "feature_names.pkl"
    with open(features_path, "wb") as f:
        pickle.dump(trained_model["feature_names"], f)
    
    return str(model_path)