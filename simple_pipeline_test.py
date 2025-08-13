#!/usr/bin/env python3
"""
Simple test script for the MLOps pipeline.
Tests data processing, model training, and saves a model for API testing.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import pandas as pd
import numpy as np
from data.data_processor import TaxiDataProcessor
from models.trainer import ModelTrainer
import pickle
import json


def create_sample_data(n_samples=1000):
    """Create realistic sample taxi data."""
    print(f"🔧 Creating {n_samples:,} sample taxi trips...")
    
    np.random.seed(42)
    
    # Create realistic pickup times (spread over a month)
    start_date = pd.Timestamp('2024-01-01')
    pickup_times = [
        start_date + pd.Timedelta(seconds=np.random.randint(0, 30*24*3600))
        for _ in range(n_samples)
    ]
    
    # Create realistic trip durations (log-normal distribution)
    trip_durations = np.random.lognormal(mean=5.5, sigma=0.8, size=n_samples)
    trip_durations = np.clip(trip_durations, 60, 7200)  # 1 min to 2 hours
    
    # Create dropoff times
    dropoff_times = [
        pickup + pd.Timedelta(seconds=duration)
        for pickup, duration in zip(pickup_times, trip_durations)
    ]
    
    # Create realistic features
    data = pd.DataFrame({
        'tpep_pickup_datetime': pickup_times,
        'tpep_dropoff_datetime': dropoff_times,
        'trip_distance': np.random.exponential(scale=2.5, size=n_samples),
        'passenger_count': np.random.choice([1, 2, 3, 4], n_samples, p=[0.7, 0.2, 0.08, 0.02]),
        'fare_amount': np.random.exponential(scale=12, size=n_samples) + 2.5,
        'PULocationID': np.random.randint(1, 265, n_samples),
        'DOLocationID': np.random.randint(1, 265, n_samples),
    })
    
    print(f"✅ Sample data created with {len(data):,} trips")
    return data


def test_data_processing(data):
    """Test data processing pipeline."""
    print("\n🔧 Testing data processing...")
    
    processor = TaxiDataProcessor()
    
    # Clean data
    cleaned = processor.clean_data(data)
    print(f"✅ Data cleaning: {len(data):,} → {len(cleaned):,} records")
    
    # Engineer features
    engineered = processor.engineer_features(cleaned)
    new_features = [col for col in engineered.columns if col not in data.columns]
    print(f"✅ Feature engineering: {len(new_features)} new features created")
    
    # Prepare for ML
    X, y, features = processor.prepare_model_data(engineered)
    print(f"✅ Model data: {X.shape[0]:,} samples, {X.shape[1]} features")
    
    return X, y, features, processor


def test_model_training(X, y, features):
    """Test model training."""
    print("\n🔧 Testing model training...")
    
    # Train baseline model
    trainer = ModelTrainer(model_type="baseline")
    model, metrics = trainer.train(X, y)
    
    print("✅ Baseline model training complete!")
    print(f"  RMSE: {metrics['train_rmse']:.1f} seconds ({metrics['train_rmse']/60:.1f} min)")
    print(f"  MAE: {metrics['train_mae']:.1f} seconds")
    print(f"  R²: {metrics['train_r2']:.3f}")
    
    # Test Random Forest
    rf_trainer = ModelTrainer(model_type="random_forest")
    rf_model, rf_metrics = rf_trainer.train(X, y)
    
    print("✅ Random Forest model training complete!")
    print(f"  RMSE: {rf_metrics['train_rmse']:.1f} seconds ({rf_metrics['train_rmse']/60:.1f} min)")
    print(f"  MAE: {rf_metrics['train_mae']:.1f} seconds")
    print(f"  R²: {rf_metrics['train_r2']:.3f}")
    
    # Choose best model
    best_trainer = trainer if metrics['train_r2'] > rf_metrics['train_r2'] else rf_trainer
    best_metrics = metrics if metrics['train_r2'] > rf_metrics['train_r2'] else rf_metrics
    
    print(f"✅ Best model: {best_trainer.model_type} (R² = {best_metrics['train_r2']:.3f})")
    
    return best_trainer, best_metrics


def save_model_for_api(trainer, features, metrics):
    """Save model and metadata for API."""
    print("\n🔧 Saving model for API...")
    
    # Create models directory
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # Save trained model
    model_path = models_dir / "taxi_duration_model.pkl"
    trainer.save_model(model_path)
    print(f"✅ Model saved to {model_path}")
    
    # Save feature names
    features_path = models_dir / "feature_names.json"
    with open(features_path, 'w') as f:
        json.dump(features, f)
    print(f"✅ Features saved to {features_path}")
    
    # Save model metadata
    metadata = {
        "model_type": trainer.model_type,
        "features_count": len(features),
        "train_rmse": metrics["train_rmse"],
        "train_mae": metrics["train_mae"],
        "train_r2": metrics["train_r2"],
        "created_at": pd.Timestamp.now().isoformat()
    }
    
    metadata_path = models_dir / "model_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✅ Metadata saved to {metadata_path}")
    
    return model_path, features_path, metadata_path


def test_predictions(trainer, X, y):
    """Test model predictions."""
    print("\n🔧 Testing predictions...")
    
    # Test on sample data
    sample_X = X.head(10)
    sample_y = y.head(10)
    
    predictions = trainer.predict(sample_X)
    
    print("✅ Sample predictions vs actual:")
    for i, (pred, actual) in enumerate(zip(predictions, sample_y)):
        error = abs(pred - actual)
        print(f"  Trip {i+1}: Predicted {int(pred)}s ({pred/60:.1f}min), "
              f"Actual {int(actual)}s ({actual/60:.1f}min), "
              f"Error: {int(error)}s ({error/60:.1f}min)")


def main():
    """Run the complete MLOps pipeline test."""
    print("🚀 MLOps Pipeline Test - NYC Taxi Duration Prediction")
    print("=" * 60)
    
    try:
        # Create sample data
        data = create_sample_data(n_samples=2000)
        
        # Test data processing
        X, y, features, processor = test_data_processing(data)
        
        # Test model training
        trainer, metrics = test_model_training(X, y, features)
        
        # Save model for API
        model_path, features_path, metadata_path = save_model_for_api(trainer, features, metrics)
        
        # Test predictions
        test_predictions(trainer, X, y)
        
        print("\n" + "=" * 60)
        print("🎉 MLOps Pipeline Test Complete!")
        print(f"✅ Data processing: Working")
        print(f"✅ Model training: Working ({trainer.model_type})")
        print(f"✅ Model saving: Working")
        print(f"✅ Predictions: Working")
        print(f"\n📁 Files created:")
        print(f"  • {model_path}")
        print(f"  • {features_path}")
        print(f"  • {metadata_path}")
        print(f"\n🔧 Next steps:")
        print(f"  • Restart API to load the new model")
        print(f"  • Test API endpoints with curl or browser")
        print(f"  • Run 'make docker-up' for full stack")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())