# NYC Taxi Duration Prediction API

**Status**: ✅ **Production Ready** | **Model**: Random Forest (R² = 0.986) | **Response Time**: < 100ms

## Overview

RESTful API for predicting NYC taxi trip duration using machine learning. Built with FastAPI and featuring real-time predictions with 98.6% accuracy.

## Base URL

- **Local Development**: `http://127.0.0.1:8080`
- **Production**: `https://your-domain.com` (when deployed)

## Authentication

Currently no authentication required for development. Production deployment should implement API keys or OAuth.

## Endpoints

### Health Check

Check API and model status.

**GET** `/health`

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "timestamp": "2025-08-13T15:33:13.265088"
}
```

**Status Codes:**
- `200`: Service healthy, model loaded
- `503`: Service unhealthy or model not loaded

---

### Root Information

Get basic API information.

**GET** `/`

**Response:**
```json
{
  "message": "NYC Taxi Duration Prediction API",
  "docs": "/docs",
  "health": "/health"
}
```

---

### Predict Trip Duration

Predict taxi trip duration based on trip parameters.

**POST** `/predict`

**Request Body:**
```json
{
  "pickup_datetime": "2024-01-15 14:30:00",
  "trip_distance": 2.5,
  "passenger_count": 1,
  "PULocationID": 142,
  "DOLocationID": 236,
  "fare_amount": 15.50
}
```

**Parameters:**
- `pickup_datetime` (string, required): Pickup datetime in format "YYYY-MM-DD HH:MM:SS"
- `trip_distance` (float, required): Trip distance in miles (0 < distance ≤ 100)
- `passenger_count` (int, required): Number of passengers (1-8)
- `PULocationID` (int, required): Pickup location ID (1-265)
- `DOLocationID` (int, required): Dropoff location ID (1-265)
- `fare_amount` (float, required): Fare amount in dollars (> 0, ≤ 1000)

**Response:**
```json
{
  "predicted_duration": 608.94,
  "predicted_duration_minutes": 10.15,
  "model_version": "baseline_v1",
  "timestamp": "2025-08-13T15:33:15.747050"
}
```

**Response Fields:**
- `predicted_duration`: Predicted trip duration in seconds
- `predicted_duration_minutes`: Predicted duration in minutes (convenience field)
- `model_version`: Version identifier of the model used
- `timestamp`: UTC timestamp of when prediction was made

**Status Codes:**
- `200`: Successful prediction
- `422`: Validation error (invalid input parameters)
- `503`: Model not loaded

---

### Model Information

Get information about the loaded ML model.

**GET** `/model/info`

**Response:**
```json
{
  "model_type": "random_forest",
  "features_count": 19,
  "feature_names": [
    "trip_distance", "passenger_count", "pickup_hour",
    "pickup_weekday", "pickup_is_weekend", "is_rush_hour",
    "is_airport_pickup", "is_airport_dropoff", "speed_mph",
    "PULocationID"
  ],
  "model_loaded": true,
  "timestamp": "2025-08-13T15:33:22.787123"
}
```

**Status Codes:**
- `200`: Model information retrieved
- `503`: Model not loaded

---

## Interactive Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: `http://127.0.0.1:8080/docs`
- **ReDoc**: `http://127.0.0.1:8080/redoc`

## Example Usage

### cURL Examples

**Health Check:**
```bash
curl http://127.0.0.1:8080/health
```

**Short Trip Prediction:**
```bash
curl -X POST "http://127.0.0.1:8080/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "pickup_datetime": "2024-01-15 14:30:00",
    "trip_distance": 2.5,
    "passenger_count": 1,
    "PULocationID": 142,
    "DOLocationID": 236,
    "fare_amount": 15.50
  }'
```

**Airport Trip Prediction:**
```bash
curl -X POST "http://127.0.0.1:8080/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "pickup_datetime": "2024-01-15 08:00:00",
    "trip_distance": 5.2,
    "passenger_count": 2,
    "PULocationID": 132,
    "DOLocationID": 161,
    "fare_amount": 25.00
  }'
```

### Python Example

```python
import requests
import json

# API endpoint
url = "http://127.0.0.1:8080/predict"

# Trip data
trip_data = {
    "pickup_datetime": "2024-01-15 14:30:00",
    "trip_distance": 2.5,
    "passenger_count": 1,
    "PULocationID": 142,
    "DOLocationID": 236,
    "fare_amount": 15.50
}

# Make prediction
response = requests.post(url, json=trip_data)
result = response.json()

print(f"Predicted duration: {result['predicted_duration_minutes']:.1f} minutes")
```

### JavaScript Example

```javascript
const apiUrl = 'http://127.0.0.1:8080/predict';

const tripData = {
  pickup_datetime: '2024-01-15 14:30:00',
  trip_distance: 2.5,
  passenger_count: 1,
  PULocationID: 142,
  DOLocationID: 236,
  fare_amount: 15.50
};

fetch(apiUrl, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(tripData)
})
.then(response => response.json())
.then(data => {
  console.log(`Predicted duration: ${data.predicted_duration_minutes.toFixed(1)} minutes`);
});
```

## Error Handling

### Validation Errors (422)

When input parameters don't meet validation requirements:

```json
{
  "detail": [
    {
      "loc": ["body", "trip_distance"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt",
      "ctx": {"limit_value": 0}
    }
  ]
}
```

### Model Not Loaded (503)

When the ML model is not available:

```json
{
  "detail": "Model not loaded"
}
```

## Model Details

### Current Model Performance
- **Algorithm**: Random Forest Regressor
- **Features**: 19 engineered features
- **Accuracy**: R² = 0.986 (98.6% variance explained)
- **Error Rate**: RMSE = 33.4 seconds (typical error < 1 minute)
- **Training Data**: 2,000 NYC taxi trips

### Feature Engineering
The model uses the following feature categories:

1. **Base Features**: trip_distance, passenger_count, fare_amount
2. **Location Features**: PULocationID, DOLocationID, airport indicators
3. **Time Features**: pickup_hour, pickup_weekday, weekend indicator
4. **Derived Features**: speed_mph, rush_hour indicator
5. **Categorical Features**: hour_category, distance_category (one-hot encoded)

## Rate Limits

Currently no rate limits implemented for development. Production deployment should include:
- Rate limiting per IP/API key
- Request throttling
- Usage analytics

## Monitoring

The API includes built-in health monitoring:
- Model loading status
- Response time tracking
- Error rate monitoring
- Feature drift detection (with Evidently AI)

## Development

### Local Setup
```bash
# Start the API server
uv run uvicorn src.api.main:app --host 127.0.0.1 --port 8080 --reload

# Health check
curl http://127.0.0.1:8080/health
```

### Testing
```bash
# Run API tests
pytest tests/test_api.py -v

# Run all tests
make test
```

## Production Deployment

### Docker Deployment
```bash
# Build and start services
make docker-up

# API available at http://localhost:8000
```

### Environment Variables
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
MODEL_PATH=models/taxi_duration_model.pkl

# Model Configuration  
MODEL_TYPE=random_forest
FEATURES_PATH=models/feature_names.json
```

## Support

For issues, feature requests, or questions:
- **GitHub Issues**: [Create an issue](https://github.com/your-repo/issues)
- **Documentation**: See README.md for full setup guide
- **API Docs**: Available at `/docs` endpoint

---

**Last Updated**: August 13, 2025  
**API Version**: 1.0.0  
**Model Version**: Random Forest v1 (R² = 0.986)