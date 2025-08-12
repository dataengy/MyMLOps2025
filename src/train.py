#!/usr/bin/env python3
"""
Training script for NYC Taxi trip duration prediction.
"""

import argparse
import os
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split
import mlflow
import mlflow.sklearn
from rich.console import Console
from dotenv import load_dotenv

from data.data_processor import TaxiDataProcessor
from models.trainer import ModelTrainer

# Load environment variables
load_dotenv()
console = Console()


def setup_mlflow():
    """Configure MLflow tracking."""
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "nytaxi-duration-prediction")
    
    mlflow.set_tracking_uri(tracking_uri)
    
    # Create experiment if it doesn't exist
    try:
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment is None:
            mlflow.create_experiment(experiment_name)
        mlflow.set_experiment(experiment_name)
    except Exception as e:
        console.print(f"[yellow]MLflow setup warning: {e}")
        console.print("[yellow]Continuing without MLflow tracking...")
        return False
    
    return True


def train_model(
    data_path: Path,
    model_type: str = "baseline",
    test_size: float = 0.2,
    random_state: int = 42,
    use_mlflow: bool = True
):
    """Train and evaluate model."""
    
    console.print(f"[green]Training {model_type} model")
    console.print(f"[blue]Data: {data_path}")
    
    # Load processed data
    if not data_path.exists():
        console.print(f"[red]Data file not found: {data_path}")
        console.print(f"[blue]Run: make data  # to process data first")
        return
    
    df = pd.read_parquet(data_path)
    console.print(f"[green]Loaded {len(df):,} records")
    
    # Prepare data
    processor = TaxiDataProcessor()
    X, y, feature_names = processor.prepare_model_data(df)
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    
    console.print(f"[blue]Train: {len(X_train):,}, Test: {len(X_test):,}")
    
    # Start MLflow run
    mlflow_enabled = use_mlflow and setup_mlflow()
    
    if mlflow_enabled:
        with mlflow.start_run():
            model, metrics = _train_with_mlflow(
                X_train, X_test, y_train, y_test, 
                feature_names, model_type, random_state
            )
    else:
        model, metrics = _train_without_mlflow(
            X_train, X_test, y_train, y_test, 
            feature_names, model_type
        )
    
    # Save model
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    trainer = ModelTrainer(model_type=model_type)
    trainer.model = model
    model_path = models_dir / f"{model_type}_model.pkl"
    trainer.save_model(model_path)
    
    console.print(f"[green]Model saved: {model_path}")
    
    # Print metrics
    console.print(f"\n[green]Model Performance:")
    for metric, value in metrics.items():
        if isinstance(value, float):
            console.print(f"  {metric}: {value:.4f}")
        else:
            console.print(f"  {metric}: {value}")
    
    return model, metrics


def _train_with_mlflow(X_train, X_test, y_train, y_test, feature_names, model_type, random_state):
    """Train model with MLflow tracking."""
    
    # Log parameters
    mlflow.log_param("model_type", model_type)
    mlflow.log_param("train_samples", len(X_train))
    mlflow.log_param("test_samples", len(X_test))
    mlflow.log_param("features", len(feature_names))
    mlflow.log_param("random_state", random_state)
    
    # Train model
    trainer = ModelTrainer(model_type=model_type)
    model, metrics = trainer.train(X_train, y_train, X_test, y_test)
    
    # Log metrics
    for metric, value in metrics.items():
        if isinstance(value, (int, float)):
            mlflow.log_metric(metric, value)
    
    # Log model
    mlflow.sklearn.log_model(
        model, 
        "model",
        registered_model_name=f"taxi_duration_{model_type}"
    )
    
    # Log feature importance
    feature_importance = trainer.get_feature_importance(feature_names)
    if feature_importance:
        importance_df = pd.DataFrame([
            {"feature": k, "importance": v} 
            for k, v in feature_importance.items()
        ])
        mlflow.log_table(importance_df, "feature_importance.json")
    
    return model, metrics


def _train_without_mlflow(X_train, X_test, y_train, y_test, feature_names, model_type):
    """Train model without MLflow tracking."""
    trainer = ModelTrainer(model_type=model_type)
    return trainer.train(X_train, y_train, X_test, y_test)


def main():
    parser = argparse.ArgumentParser(description="Train NYC Taxi duration prediction model")
    parser.add_argument(
        "--model", 
        choices=["baseline", "random_forest"], 
        default="baseline",
        help="Model type to train"
    )
    parser.add_argument(
        "--data", 
        type=Path, 
        default=Path("data/processed/processed_data.parquet"),
        help="Path to processed data"
    )
    parser.add_argument(
        "--test-size", 
        type=float, 
        default=0.2,
        help="Test set size (default: 0.2)"
    )
    parser.add_argument(
        "--no-mlflow", 
        action="store_true",
        help="Disable MLflow tracking"
    )
    parser.add_argument(
        "--random-state", 
        type=int, 
        default=42,
        help="Random state for reproducibility"
    )
    
    args = parser.parse_args()
    
    train_model(
        data_path=args.data,
        model_type=args.model,
        test_size=args.test_size,
        random_state=args.random_state,
        use_mlflow=not args.no_mlflow
    )


if __name__ == "__main__":
    main()