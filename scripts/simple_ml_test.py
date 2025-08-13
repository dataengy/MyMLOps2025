#!/usr/bin/env python3
"""
Simple ML training test without external dependencies.
Implements basic linear regression from scratch for testing.
"""

import csv
import json
import math
import random
from pathlib import Path
from typing import List, Tuple, Dict


class SimpleLinearRegression:
    """Basic linear regression implementation without sklearn."""
    
    def __init__(self):
        self.weights = None
        self.bias = None
        self.feature_names = None
    
    def fit(self, X: List[List[float]], y: List[float], feature_names: List[str] = None):
        """Train the linear regression model using normal equation."""
        print(f"Training linear regression on {len(X)} samples with {len(X[0])} features...")
        
        self.feature_names = feature_names or [f"feature_{i}" for i in range(len(X[0]))]
        
        # Add bias column (all 1s) to X
        X_with_bias = [[1.0] + row for row in X]
        
        # Normal equation: theta = (X^T X)^(-1) X^T y
        X_transpose = self._transpose(X_with_bias)
        XTX = self._matrix_multiply(X_transpose, X_with_bias)
        XTX_inv = self._matrix_inverse(XTX)
        XTy = self._matrix_vector_multiply(X_transpose, y)
        theta = self._matrix_vector_multiply(XTX_inv, XTy)
        
        self.bias = theta[0]
        self.weights = theta[1:]
        
        print(f"✅ Training complete!")
        print(f"   Bias: {self.bias:.4f}")
        print(f"   Weights: {[f'{w:.4f}' for w in self.weights[:3]]}...")
    
    def predict(self, X: List[List[float]]) -> List[float]:
        """Make predictions."""
        if self.weights is None:
            raise ValueError("Model not trained yet!")
        
        predictions = []
        for row in X:
            pred = self.bias
            for i, feature_val in enumerate(row):
                pred += self.weights[i] * feature_val
            predictions.append(pred)
        
        return predictions
    
    def _transpose(self, matrix: List[List[float]]) -> List[List[float]]:
        """Transpose a matrix."""
        return [[matrix[j][i] for j in range(len(matrix))] 
                for i in range(len(matrix[0]))]
    
    def _matrix_multiply(self, A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
        """Multiply two matrices."""
        rows_A, cols_A = len(A), len(A[0])
        rows_B, cols_B = len(B), len(B[0])
        
        if cols_A != rows_B:
            raise ValueError("Matrix dimensions don't match for multiplication")
        
        result = [[0 for _ in range(cols_B)] for _ in range(rows_A)]
        
        for i in range(rows_A):
            for j in range(cols_B):
                for k in range(cols_A):
                    result[i][j] += A[i][k] * B[k][j]
        
        return result
    
    def _matrix_vector_multiply(self, matrix: List[List[float]], vector: List[float]) -> List[float]:
        """Multiply matrix by vector."""
        result = []
        for row in matrix:
            dot_product = sum(row[i] * vector[i] for i in range(len(vector)))
            result.append(dot_product)
        return result
    
    def _matrix_inverse(self, matrix: List[List[float]]) -> List[List[float]]:
        """Compute matrix inverse using Gaussian elimination."""
        n = len(matrix)
        # Create augmented matrix [A|I]
        augmented = [row[:] + [0] * n for row in matrix]
        for i in range(n):
            augmented[i][n + i] = 1
        
        # Forward elimination
        for i in range(n):
            # Find pivot
            max_row = i
            for k in range(i + 1, n):
                if abs(augmented[k][i]) > abs(augmented[max_row][i]):
                    max_row = k
            
            # Swap rows
            augmented[i], augmented[max_row] = augmented[max_row], augmented[i]
            
            # Make diagonal 1
            pivot = augmented[i][i]
            if abs(pivot) < 1e-10:
                raise ValueError("Matrix is singular")
            
            for j in range(2 * n):
                augmented[i][j] /= pivot
            
            # Eliminate column
            for k in range(n):
                if k != i:
                    factor = augmented[k][i]
                    for j in range(2 * n):
                        augmented[k][j] -= factor * augmented[i][j]
        
        # Extract inverse matrix
        inverse = [[augmented[i][j + n] for j in range(n)] for i in range(n)]
        return inverse


def load_processed_data(filepath: Path) -> Tuple[List[List[float]], List[float], List[str]]:
    """Load processed data from CSV."""
    print(f"Loading data from {filepath}...")
    
    with open(filepath, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        data = list(reader)
    
    # Define features and target
    feature_columns = [
        'trip_distance', 'passenger_count', 'pickup_hour', 'pickup_weekday',
        'pickup_is_weekend', 'is_rush_hour', 'speed_mph'
    ]
    
    target_column = 'trip_duration'
    
    X = []
    y = []
    
    for row in data:
        # Extract features
        feature_row = []
        skip_row = False
        
        for col in feature_columns:
            if col in row and row[col]:
                try:
                    feature_row.append(float(row[col]))
                except ValueError:
                    skip_row = True
                    break
            else:
                skip_row = True
                break
        
        # Extract target
        if not skip_row and target_column in row and row[target_column]:
            try:
                target_val = float(row[target_column])
                X.append(feature_row)
                y.append(target_val)
            except ValueError:
                pass
    
    print(f"Loaded {len(X)} samples with {len(feature_columns)} features")
    return X, y, feature_columns


def calculate_metrics(y_true: List[float], y_pred: List[float]) -> Dict[str, float]:
    """Calculate regression metrics."""
    n = len(y_true)
    
    # Mean Squared Error
    mse = sum((y_true[i] - y_pred[i]) ** 2 for i in range(n)) / n
    rmse = math.sqrt(mse)
    
    # Mean Absolute Error  
    mae = sum(abs(y_true[i] - y_pred[i]) for i in range(n)) / n
    
    # R-squared
    y_mean = sum(y_true) / n
    ss_tot = sum((y_true[i] - y_mean) ** 2 for i in range(n))
    ss_res = sum((y_true[i] - y_pred[i]) ** 2 for i in range(n))
    
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    return {
        'rmse': rmse,
        'mae': mae,
        'r2_score': r2,
        'mse': mse,
        'n_samples': n
    }


def train_test_split(X: List[List[float]], y: List[float], test_size: float = 0.2, random_seed: int = 42):
    """Simple train/test split."""
    random.seed(random_seed)
    
    n = len(X)
    test_n = int(n * test_size)
    
    # Create indices and shuffle
    indices = list(range(n))
    random.shuffle(indices)
    
    test_indices = indices[:test_n]
    train_indices = indices[test_n:]
    
    X_train = [X[i] for i in train_indices]
    X_test = [X[i] for i in test_indices]
    y_train = [y[i] for i in train_indices]
    y_test = [y[i] for i in test_indices]
    
    return X_train, X_test, y_train, y_test


def save_model_info(model: SimpleLinearRegression, metrics: Dict, filepath: Path):
    """Save model information as JSON."""
    model_info = {
        'model_type': 'SimpleLinearRegression',
        'bias': model.bias,
        'weights': model.weights,
        'feature_names': model.feature_names,
        'metrics': metrics,
        'timestamp': str(Path(__file__).stat().st_mtime)
    }
    
    with open(filepath, 'w') as f:
        json.dump(model_info, f, indent=2)
    
    print(f"Model info saved to {filepath}")


def main():
    """Main ML training function."""
    print("🧠 MLOps ML Training Test (Simplified)")
    print("=" * 50)
    
    # Check if processed data exists
    data_path = Path("data/processed/processed_taxi_data.csv")
    if not data_path.exists():
        print(f"❌ Processed data not found at {data_path}")
        print("Please run: python scripts/simple_data_test.py first")
        return
    
    # Load data
    X, y, feature_names = load_processed_data(data_path)
    
    if len(X) == 0:
        print("❌ No valid data loaded")
        return
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_seed=42)
    print(f"📊 Data split: {len(X_train)} train, {len(X_test)} test samples")
    
    # Train model
    model = SimpleLinearRegression()
    model.fit(X_train, y_train, feature_names)
    
    # Make predictions
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    
    # Calculate metrics
    train_metrics = calculate_metrics(y_train, y_train_pred)
    test_metrics = calculate_metrics(y_test, y_test_pred)
    
    # Results
    print(f"\n📈 Model Performance:")
    print(f"  Training:")
    print(f"    RMSE: {train_metrics['rmse']:.2f} seconds")
    print(f"    MAE:  {train_metrics['mae']:.2f} seconds")
    print(f"    R²:   {train_metrics['r2_score']:.4f}")
    
    print(f"  Testing:")
    print(f"    RMSE: {test_metrics['rmse']:.2f} seconds")
    print(f"    MAE:  {test_metrics['mae']:.2f} seconds")
    print(f"    R²:   {test_metrics['r2_score']:.4f}")
    
    # Feature importance (absolute weights)
    print(f"\n🔧 Feature Importance (by weight magnitude):")
    feature_importance = list(zip(feature_names, [abs(w) for w in model.weights]))
    feature_importance.sort(key=lambda x: x[1], reverse=True)
    
    for feature, importance in feature_importance:
        print(f"  {feature}: {importance:.4f}")
    
    # Save model
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    model_info_path = models_dir / "simple_model_info.json"
    all_metrics = {
        'train': train_metrics,
        'test': test_metrics
    }
    save_model_info(model, all_metrics, model_info_path)
    
    print(f"\n✅ ML Training Complete!")
    print(f"📁 Model info saved to: {model_info_path}")
    print(f"🎯 Ready for model serving and monitoring!")


if __name__ == "__main__":
    main()