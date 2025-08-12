"""
Tests for FastAPI application.
"""

import pytest
from fastapi.testclient import TestClient
import json
from unittest.mock import patch, MagicMock
from pathlib import Path

# Mock the model loading to avoid file dependencies
with patch('src.api.main.ModelTrainer'), \
     patch('src.api.main.TaxiDataProcessor'), \
     patch('src.api.main.Path'), \
     patch('builtins.open'):
    from src.api.main import app

client = TestClient(app)


class TestAPI:
    """Test cases for the FastAPI application."""
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "model_loaded" in data
        assert "timestamp" in data
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "docs" in data
        assert "health" in data
    
    @patch('src.api.main.model_trainer')
    @patch('src.api.main.data_processor')
    @patch('src.api.main.feature_names')
    def test_predict_endpoint_success(self, mock_features, mock_processor, mock_trainer):
        """Test successful prediction."""
        # Mock the model and processor
        mock_trainer.predict.return_value = [720.0]  # 12 minutes
        mock_trainer.model_type = "baseline"
        
        mock_processor_instance = MagicMock()
        mock_processor_instance.engineer_features.return_value = MagicMock()
        mock_processor_instance.prepare_model_data.return_value = (
            MagicMock(), MagicMock(), []
        )
        mock_processor.return_value = mock_processor_instance
        
        mock_features.__len__.return_value = 5
        mock_features.__iter__.return_value = iter(['feature1', 'feature2'])
        
        # Test data
        trip_data = {
            "pickup_datetime": "2024-01-01 10:00:00",
            "trip_distance": 2.5,
            "passenger_count": 1,
            "PULocationID": 100,
            "DOLocationID": 200,
            "fare_amount": 15.0
        }
        
        response = client.post("/predict", json=trip_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "predicted_duration" in data
        assert "predicted_duration_minutes" in data
        assert "model_version" in data
        assert "timestamp" in data
        assert data["predicted_duration"] == 720.0
        assert data["predicted_duration_minutes"] == 12.0
    
    def test_predict_endpoint_validation_errors(self):
        """Test prediction endpoint with validation errors."""
        # Missing required fields
        invalid_data = {
            "trip_distance": 2.5,
            # Missing other required fields
        }
        
        response = client.post("/predict", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_predict_endpoint_invalid_values(self):
        """Test prediction endpoint with invalid values."""
        # Invalid trip distance (negative)
        invalid_data = {
            "pickup_datetime": "2024-01-01 10:00:00",
            "trip_distance": -1.0,  # Invalid
            "passenger_count": 1,
            "PULocationID": 100,
            "DOLocationID": 200,
            "fare_amount": 15.0
        }
        
        response = client.post("/predict", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_predict_endpoint_no_model(self):
        """Test prediction endpoint when model is not loaded."""
        trip_data = {
            "pickup_datetime": "2024-01-01 10:00:00",
            "trip_distance": 2.5,
            "passenger_count": 1,
            "PULocationID": 100,
            "DOLocationID": 200,
            "fare_amount": 15.0
        }
        
        # Model is None by default in test environment
        response = client.post("/predict", json=trip_data)
        assert response.status_code == 503  # Service unavailable
        assert "Model not loaded" in response.json()["detail"]
    
    @patch('src.api.main.model_trainer')
    @patch('src.api.main.data_processor')
    def test_batch_predict_endpoint(self, mock_processor, mock_trainer):
        """Test batch prediction endpoint."""
        # Mock the model
        mock_trainer.predict.return_value = [720.0, 600.0]
        mock_trainer.model_type = "baseline"
        
        mock_processor_instance = MagicMock()
        mock_processor.return_value = mock_processor_instance
        
        # Test data - two trips
        batch_data = [
            {
                "pickup_datetime": "2024-01-01 10:00:00",
                "trip_distance": 2.5,
                "passenger_count": 1,
                "PULocationID": 100,
                "DOLocationID": 200,
                "fare_amount": 15.0
            },
            {
                "pickup_datetime": "2024-01-01 11:00:00",
                "trip_distance": 1.8,
                "passenger_count": 2,
                "PULocationID": 150,
                "DOLocationID": 180,
                "fare_amount": 12.0
            }
        ]
        
        with patch.object(client.app, 'dependency_overrides', {}):
            # We need to mock the predict function to avoid calling the actual endpoint
            pass  # This test needs more complex mocking for the batch endpoint
    
    @patch('src.api.main.model_trainer')
    @patch('src.api.main.feature_names')
    def test_model_info_endpoint(self, mock_features, mock_trainer):
        """Test model info endpoint."""
        mock_trainer.model_type = "baseline"
        mock_features.__len__.return_value = 10
        mock_features.__getitem__.return_value = ["feature1", "feature2"]
        
        response = client.get("/model/info")
        assert response.status_code == 200
        
        data = response.json()
        assert "model_type" in data
        assert "features_count" in data
        assert "model_loaded" in data
        assert "timestamp" in data
    
    def test_model_info_endpoint_no_model(self):
        """Test model info endpoint when model is not loaded."""
        response = client.get("/model/info")
        assert response.status_code == 503
        assert "Model not loaded" in response.json()["detail"]


class TestRequestModels:
    """Test the Pydantic request/response models."""
    
    def test_trip_request_validation(self):
        """Test TripRequest model validation."""
        from src.api.main import TripRequest
        
        # Valid data
        valid_data = {
            "pickup_datetime": "2024-01-01 10:00:00",
            "trip_distance": 2.5,
            "passenger_count": 1,
            "PULocationID": 100,
            "DOLocationID": 200,
            "fare_amount": 15.0
        }
        
        trip = TripRequest(**valid_data)
        assert trip.pickup_datetime == "2024-01-01 10:00:00"
        assert trip.trip_distance == 2.5
        assert trip.passenger_count == 1
    
    def test_trip_request_validation_errors(self):
        """Test TripRequest validation errors."""
        from src.api.main import TripRequest
        from pydantic import ValidationError
        
        # Invalid trip distance
        with pytest.raises(ValidationError):
            TripRequest(
                pickup_datetime="2024-01-01 10:00:00",
                trip_distance=-1.0,  # Invalid
                passenger_count=1,
                PULocationID=100,
                DOLocationID=200,
                fare_amount=15.0
            )
        
        # Invalid passenger count
        with pytest.raises(ValidationError):
            TripRequest(
                pickup_datetime="2024-01-01 10:00:00",
                trip_distance=2.5,
                passenger_count=0,  # Invalid
                PULocationID=100,
                DOLocationID=200,
                fare_amount=15.0
            )