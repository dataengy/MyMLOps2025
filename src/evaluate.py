#!/usr/bin/env python3
"""
Model evaluation script for NYC Taxi trip duration prediction.
Evaluates trained models against test data with comprehensive metrics.
"""

import argparse
import json
import os
from pathlib import Path
import pandas as pd
import numpy as np
import pickle
from typing import Dict, Any, Optional
import mlflow
import mlflow.sklearn
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from sklearn.metrics import (
    mean_squared_error, 
    mean_absolute_error, 
    r2_score,
    mean_absolute_percentage_error
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
console = Console()

DEFAULT_MODEL_PATH = "models/taxi_duration_model.pkl"
DEFAULT_DATA_PATH = "data/processed/processed_data.parquet" 
DEFAULT_OUTPUT_PATH = "models/evaluation_results.json"


def load_model(model_path: Path) -> Optional[Any]:
    """Load trained model from pickle file."""
    try:
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        if isinstance(model_data, dict):
            return model_data.get('model')
        else:
            return model_data
            
    except Exception as e:
        console.print(f"[red]Error loading model: {e}")
        return None


def load_test_data(data_path: Path, expected_features: Optional[list] = None) -> Optional[tuple]:
    """Load and prepare test data using the same feature engineering as training."""
    try:
        # Load raw processed data
        df = pd.read_parquet(data_path)
        console.print(f"[green]Loaded {len(df)} records from {data_path}")
        
        # If expected features include categorical encodings, we need to create them
        if expected_features and any('category_' in feat for feat in expected_features):
            console.print("[yellow]Model expects categorical features, creating dummy variables...")
            
            # Create categorical dummy variables for hour and distance
            if 'hour_category' not in df.columns:
                df['hour_category'] = pd.cut(
                    df['pickup_hour'], 
                    bins=[0, 6, 12, 18, 24], 
                    labels=['Night', 'Morning', 'Afternoon', 'Evening'],
                    include_lowest=True
                )
            
            if 'distance_category' not in df.columns:
                df['distance_category'] = pd.cut(
                    df['trip_distance'],
                    bins=[0, 2, 5, 10, float('inf')],
                    labels=['Short', 'Medium', 'Long', 'Very_Long'],
                    include_lowest=True
                )
            
            # Create dummy variables
            hour_dummies = pd.get_dummies(df['hour_category'], prefix='hour_category')
            dist_dummies = pd.get_dummies(df['distance_category'], prefix='distance_category')
            
            # Combine with existing features
            base_features = [
                'trip_distance', 'passenger_count', 'pickup_hour', 'pickup_weekday', 
                'pickup_is_weekend', 'is_rush_hour', 'is_airport_pickup', 
                'is_airport_dropoff', 'speed_mph', 'PULocationID', 'DOLocationID'
            ]
            
            X = pd.concat([df[base_features], hour_dummies, dist_dummies], axis=1)
            feature_columns = list(X.columns)
            
        else:
            # Use simple feature set
            from data.data_processor import TaxiDataProcessor
            processor = TaxiDataProcessor()
            X, _, feature_columns = processor.prepare_model_data(df)
        
        y = df['trip_duration']
        
        console.print(f"[green]Prepared {len(feature_columns)} features: {feature_columns[:5]}...")
        
        # Use 20% as test set (same split as training)
        from sklearn.model_selection import train_test_split
        _, X_test, _, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        console.print(f"[green]Test set: {len(X_test)} samples, {len(feature_columns)} features")
        return X_test, y_test, feature_columns
        
    except Exception as e:
        console.print(f"[red]Error loading test data: {e}")
        console.print(f"[red]Details: {str(e)}")
        return None


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate comprehensive evaluation metrics."""
    metrics = {
        'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
        'mae': mean_absolute_error(y_true, y_pred),
        'r2': r2_score(y_true, y_pred),
        'mape': mean_absolute_percentage_error(y_true, y_pred) * 100,
        'mean_actual': float(np.mean(y_true)),
        'mean_predicted': float(np.mean(y_pred)),
        'std_actual': float(np.std(y_true)),
        'std_predicted': float(np.std(y_pred)),
        'min_actual': float(np.min(y_true)),
        'max_actual': float(np.max(y_true)),
        'min_predicted': float(np.min(y_pred)),
        'max_predicted': float(np.max(y_pred))
    }
    
    # Calculate percentage error ranges
    errors = np.abs(y_true - y_pred)
    pct_errors = (errors / y_true) * 100
    
    metrics.update({
        'median_error': float(np.median(errors)),
        'p90_error': float(np.percentile(errors, 90)),
        'p95_error': float(np.percentile(errors, 95)),
        'pct_within_10pct': float(np.mean(pct_errors <= 10) * 100),
        'pct_within_20pct': float(np.mean(pct_errors <= 20) * 100),
        'pct_within_50pct': float(np.mean(pct_errors <= 50) * 100)
    })
    
    return metrics


def create_evaluation_table(metrics: Dict[str, float]) -> Table:
    """Create a rich table for displaying metrics."""
    table = Table(title="Model Evaluation Results", show_header=True, header_style="bold magenta")
    
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")
    table.add_column("Description", style="yellow")
    
    # Core metrics
    table.add_row("RMSE", f"{metrics['rmse']:.2f}", "Root Mean Square Error (seconds)")
    table.add_row("MAE", f"{metrics['mae']:.2f}", "Mean Absolute Error (seconds)")
    table.add_row("R²", f"{metrics['r2']:.4f}", "Coefficient of Determination")
    table.add_row("MAPE", f"{metrics['mape']:.2f}%", "Mean Absolute Percentage Error")
    
    table.add_section()
    
    # Distribution metrics
    table.add_row("Mean Actual", f"{metrics['mean_actual']:.1f}s", "Average actual trip duration")
    table.add_row("Mean Predicted", f"{metrics['mean_predicted']:.1f}s", "Average predicted duration")
    table.add_row("Std Actual", f"{metrics['std_actual']:.1f}s", "Standard deviation (actual)")
    table.add_row("Std Predicted", f"{metrics['std_predicted']:.1f}s", "Standard deviation (predicted)")
    
    table.add_section()
    
    # Error analysis
    table.add_row("Median Error", f"{metrics['median_error']:.1f}s", "50th percentile absolute error")
    table.add_row("90th %ile Error", f"{metrics['p90_error']:.1f}s", "90th percentile absolute error")
    table.add_row("95th %ile Error", f"{metrics['p95_error']:.1f}s", "95th percentile absolute error")
    
    table.add_section()
    
    # Accuracy ranges
    table.add_row("Within 10%", f"{metrics['pct_within_10pct']:.1f}%", "Predictions within 10% of actual")
    table.add_row("Within 20%", f"{metrics['pct_within_20pct']:.1f}%", "Predictions within 20% of actual")
    table.add_row("Within 50%", f"{metrics['pct_within_50pct']:.1f}%", "Predictions within 50% of actual")
    
    return table


def save_results(metrics: Dict[str, float], output_path: Path, model_info: Dict[str, Any] = None):
    """Save evaluation results to JSON file."""
    results = {
        'evaluation_metrics': metrics,
        'model_info': model_info or {},
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    console.print(f"[green]Results saved to {output_path}")


def evaluate_model(
    model_path: Path = DEFAULT_MODEL_PATH,
    data_path: Path = DEFAULT_DATA_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    verbose: bool = True
) -> Dict[str, float]:
    """
    Main evaluation function.
    
    Args:
        model_path: Path to trained model pickle file
        data_path: Path to processed data parquet file  
        output_path: Path to save evaluation results JSON
        verbose: Whether to display detailed output
        
    Returns:
        Dictionary containing evaluation metrics
    """
    
    if verbose:
        console.print(Panel.fit("🔍 Model Evaluation Pipeline", style="bold blue"))
    
    # Load model
    console.print("\n[bold]Loading trained model...")
    model = load_model(model_path)
    if model is None:
        raise ValueError(f"Could not load model from {model_path}")
    
    # Get expected features from model
    expected_features = None
    if hasattr(model, 'feature_names_in_'):
        expected_features = list(model.feature_names_in_)
    
    model_info = {
        'model_path': str(model_path),
        'model_type': type(model).__name__,
        'expected_features': expected_features
    }
    
    # Load test data
    console.print("\n[bold]Loading test data...")
    test_data = load_test_data(data_path, expected_features)
    if test_data is None:
        raise ValueError(f"Could not load test data from {data_path}")
    
    X_test, y_test, feature_columns = test_data
    model_info['features'] = feature_columns
    model_info['test_samples'] = len(X_test)
    
    # Make predictions
    console.print("\n[bold]Generating predictions...")
    try:
        y_pred = model.predict(X_test)
        console.print(f"[green]Generated {len(y_pred)} predictions")
    except Exception as e:
        console.print(f"[red]Error making predictions: {e}")
        raise
    
    # Calculate metrics
    console.print("\n[bold]Calculating evaluation metrics...")
    metrics = calculate_metrics(y_test.values, y_pred)
    
    # Display results
    if verbose:
        console.print("\n")
        table = create_evaluation_table(metrics)
        console.print(table)
        
        # Model quality assessment
        r2 = metrics['r2']
        if r2 >= 0.8:
            quality = "[green]Excellent[/green]"
        elif r2 >= 0.6:
            quality = "[yellow]Good[/yellow]"
        elif r2 >= 0.4:
            quality = "[orange]Fair[/orange]"
        else:
            quality = "[red]Poor[/red]"
            
        console.print(f"\n[bold]Model Quality Assessment: {quality} (R² = {r2:.4f})")
        
        within_20pct = metrics['pct_within_20pct']
        console.print(f"[bold]Practical Accuracy: {within_20pct:.1f}% of predictions within 20% of actual")
    
    # Save results
    console.print("\n[bold]Saving evaluation results...")
    save_results(metrics, output_path, model_info)
    
    return metrics


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Evaluate trained NYC Taxi duration model")
    parser.add_argument(
        "--model", 
        type=str, 
        default=DEFAULT_MODEL_PATH,
        help=f"Path to trained model pickle file (default: {DEFAULT_MODEL_PATH})"
    )
    parser.add_argument(
        "--data",
        type=str,
        default=DEFAULT_DATA_PATH, 
        help=f"Path to processed data parquet file (default: {DEFAULT_DATA_PATH})"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_OUTPUT_PATH,
        help=f"Path to save evaluation results (default: {DEFAULT_OUTPUT_PATH})"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress detailed output"
    )
    
    args = parser.parse_args()
    
    try:
        metrics = evaluate_model(
            model_path=Path(args.model),
            data_path=Path(args.data),
            output_path=Path(args.output),
            verbose=not args.quiet
        )
        
        # Print summary for CI/CD
        if args.quiet:
            print(f"R2: {metrics['r2']:.4f}, RMSE: {metrics['rmse']:.2f}, MAE: {metrics['mae']:.2f}")
            
    except Exception as e:
        console.print(f"[red]Evaluation failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())