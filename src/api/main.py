"""
FastAPI application for NYC Taxi trip duration prediction.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np
from pathlib import Path
import pickle
from typing import List, Dict, Any
from datetime import datetime
import uvicorn

from ..models.trainer import ModelTrainer
from ..data.data_processor import TaxiDataProcessor

app = FastAPI(
    title="NYC Taxi Duration Prediction API",
    description="MLOps API for predicting taxi trip duration",
    version="1.0.0"
)

# Global variables for model and processor
model_trainer = None
data_processor = None
feature_names = None


class TripRequest(BaseModel):
    """Request model for trip duration prediction."""
    pickup_datetime: str = Field(..., description="Pickup datetime (YYYY-MM-DD HH:MM:SS)")
    trip_distance: float = Field(..., gt=0, le=100, description="Trip distance in miles")
    passenger_count: int = Field(1, ge=1, le=8, description="Number of passengers")
    PULocationID: int = Field(..., ge=1, le=265, description="Pickup location ID")
    DOLocationID: int = Field(..., ge=1, le=265, description="Dropoff location ID")
    fare_amount: float = Field(..., gt=0, le=1000, description="Fare amount")


class TripResponse(BaseModel):
    """Response model for trip duration prediction."""
    predicted_duration: float = Field(..., description="Predicted trip duration in seconds")
    predicted_duration_minutes: float = Field(..., description="Predicted duration in minutes")
    model_version: str = Field(..., description="Model version used")
    timestamp: str = Field(..., description="Prediction timestamp")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model_loaded: bool
    timestamp: str


@app.on_event("startup")
async def load_model():
    """Load model and processor on startup."""
    global model_trainer, data_processor, feature_names
    
    try:
        # Load model
        model_path = Path("models/taxi_duration_model.pkl")
        if model_path.exists():
            model_trainer = ModelTrainer.load_model(model_path)
            print(f"Model loaded from {model_path}")
        else:
            print(f"Warning: Model not found at {model_path}")
        
        # Load feature names
        features_path = Path("models/feature_names.json")
        if features_path.exists():
            import json
            with open(features_path, "r") as f:
                feature_names = json.load(f)
            print(f"Feature names loaded: {len(feature_names)} features")
        
        # Initialize data processor
        data_processor = TaxiDataProcessor()
        print("Data processor initialized")
        
    except Exception as e:
        print(f"Error loading model: {e}")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy" if model_trainer is not None else "unhealthy",
        model_loaded=model_trainer is not None,
        timestamp=datetime.now().isoformat()
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "NYC Taxi Duration Prediction API",
        "docs": "/docs",
        "health": "/health"
    }


@app.post("/predict", response_model=TripResponse)
async def predict_trip_duration(trip: TripRequest):
    """Predict trip duration for a taxi trip."""
    
    if model_trainer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Convert request to DataFrame
        trip_data = {
            "tpep_pickup_datetime": [trip.pickup_datetime],
            "trip_distance": [trip.trip_distance],
            "passenger_count": [trip.passenger_count],
            "PULocationID": [trip.PULocationID],
            "DOLocationID": [trip.DOLocationID],
            "fare_amount": [trip.fare_amount],
        }
        
        df = pd.DataFrame(trip_data)
        df["tpep_pickup_datetime"] = pd.to_datetime(df["tpep_pickup_datetime"])
        
        # Add dummy values for required fields
        df["tpep_dropoff_datetime"] = df["tpep_pickup_datetime"]  # Will be overwritten
        df["trip_duration"] = 600  # Dummy value, not used for prediction
        
        # Process features
        df = data_processor.engineer_features(df)
        X, _, _ = data_processor.prepare_model_data(df)
        
        # Ensure we have all required features
        if feature_names:
            missing_features = set(feature_names) - set(X.columns)
            if missing_features:
                # Add missing features with default values
                for feature in missing_features:
                    X[feature] = 0
            
            # Reorder columns to match training
            X = X[feature_names]
        
        # Make prediction
        prediction = model_trainer.predict(X)[0]
        
        return TripResponse(
            predicted_duration=float(prediction),
            predicted_duration_minutes=float(prediction / 60),
            model_version="baseline_v1",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")


@app.post("/predict/batch")
async def predict_batch(trips: List[TripRequest]):
    """Predict trip duration for multiple trips."""
    
    if model_trainer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        predictions = []
        for trip in trips:
            # Reuse single prediction logic
            result = await predict_trip_duration(trip)
            predictions.append(result)
        
        return {
            "predictions": predictions,
            "count": len(predictions),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Batch prediction error: {str(e)}")


@app.get("/model/info")
async def model_info():
    """Get model information."""
    if model_trainer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return {
        "model_type": model_trainer.model_type,
        "features_count": len(feature_names) if feature_names else 0,
        "feature_names": feature_names[:10] if feature_names else [],  # First 10 features
        "model_loaded": True,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )