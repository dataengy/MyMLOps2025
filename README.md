# NYC Taxi Duration Prediction - MLOps Project

**🎉 Production-Ready MLOps Pipeline** for predicting NYC taxi trip duration using modern ML engineering practices.

> **Status**: ✅ **Architecture Complete** | 🧪 **Ready for Functional Testing** | 🚀 **Deployment Ready**

## 🎯 Project Overview

This project demonstrates an end-to-end MLOps pipeline that:
- **Predicts taxi trip duration** using NYC TLC trip record data
- **Tracks experiments** with MLflow
- **Orchestrates workflows** with Dagster
- **Monitors data drift** with Evidently AI
- **Serves predictions** via FastAPI
- **Ensures quality** with comprehensive testing and CI/CD

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   Orchestration │    │   ML Pipeline   │
│                 │    │                 │    │                 │
│ • NYC TLC Data  │───▶│ • Dagster       │───▶│ • scikit-learn  │
│ • PARQUET files │    │ • Asset lineage │    │ • Feature eng.  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐           │
│   Monitoring    │    │   Deployment    │           │
│                 │    │                 │           │
│ • Evidently AI  │◀───│ • FastAPI       │◀──────────┘
│ • Data drift    │    │ • Docker        │
│ • Model perf.   │    │ • REST API      │
└─────────────────┘    └─────────────────┘
                                │
┌─────────────────┐    ┌─────────────────┐
│   Experiment    │    │   Infrastructure│
│   Tracking      │    │                 │
│                 │    │                 │
│ • MLflow        │    │ • PostgreSQL    │
│ • Model registry│    │ • Docker Compose│
│ • Metrics       │    │ • GitHub Actions│
└─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

**⚡ Fast Track**: The complete pipeline is implemented and validated - jump straight to testing!

### Prerequisites
- Python 3.11+
- Docker & Docker Compose  
- Git

### 1. Setup Environment
```bash
# Clone repository
git clone <your-repo-url>
cd MyMLOps2025

# Initialize project
make setup

# Install dependencies  
make install-dev
```

### 2. Download Sample Data
```bash
# Download one month of data for testing
make data-sample
```

### 3. Train Baseline Model
```bash
# Train a simple linear regression model
make train-baseline
```

### 4. Start Services
```bash
# Start all services with Docker Compose
make docker-up

# OR start individual services:
make mlflow    # MLflow UI at http://localhost:5000
make dagster   # Dagster UI at http://localhost:3001  
make api       # FastAPI at http://localhost:8000
```

### 5. Make Predictions
```bash
# Test the API
curl -X POST "http://localhost:8000/predict" \
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

## 📊 Data Pipeline

### Data Source
- **NYC TLC Trip Record Data** (Yellow taxi trips)
- **Format**: Parquet files from official TLC website
- **Features**: Pickup/dropoff times, locations, distances, fares
- **Target**: Trip duration (derived from timestamps)

### Feature Engineering
- **Time features**: Hour, day, weekday, is_weekend
- **Location features**: Airport indicators, location IDs
- **Trip features**: Distance categories, speed, rush hour
- **Categorical encoding**: One-hot encoding for categories

## 🤖 ML Models

### Baseline Model
- **Algorithm**: Linear Regression with StandardScaler
- **Features**: 15+ engineered features
- **Target**: Trip duration in seconds
- **Metrics**: RMSE, MAE, R²

### Advanced Model
- **Algorithm**: Random Forest Regressor
- **Hyperparameters**: 100 estimators, max_depth=10
- **Features**: Same as baseline + feature importance
- **Evaluation**: Cross-validation + holdout test

## 🔄 MLOps Components

### Experiment Tracking (MLflow)
- **Metrics**: RMSE, MAE, R² score
- **Parameters**: Model type, hyperparameters
- **Artifacts**: Trained models, feature importance
- **Model Registry**: Versioned model storage

### Workflow Orchestration (Dagster)
- **Asset-based**: Data assets with lineage tracking
- **Incremental**: Only recompute changed dependencies
- **Scheduling**: Configurable pipeline runs
- **Monitoring**: Built-in asset health checks

### Model Serving (FastAPI)
- **REST API**: JSON request/response
- **Validation**: Pydantic models with constraints
- **Health checks**: Model status monitoring
- **Batch prediction**: Multiple trips at once

### Data Monitoring (Evidently)
- **Data drift**: Statistical tests for feature drift
- **Data quality**: Missing values, duplicates, ranges
- **Model performance**: Accuracy degradation detection
- **Reports**: HTML reports + JSON metrics

## 🧪 Testing & Quality

### Testing Strategy
```bash
# Run all tests
make test

# Run specific test categories
pytest tests/test_data_processor.py -v
pytest tests/test_model_trainer.py -v
pytest tests/test_api.py -v
```

### Code Quality
```bash
# Format code
make format

# Lint code
make lint

# Type checking
mypy src
```

### Pre-commit Hooks
```bash
# Install hooks
make pre-commit-install

# Run manually
make pre-commit
```

## 🚢 Deployment

### Local Development
```bash
# Start development environment
make dev-run

# Run full pipeline
make full-pipeline
```

### Production Deployment
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy with monitoring
make deploy-production
```

### CI/CD Pipeline
- **Testing**: Automated testing on PR/push
- **Security**: Bandit security scans
- **Data validation**: Sample data processing
- **Model training**: Automated retraining
- **Deployment**: Staging → Production

## 📈 Monitoring & Alerting

### Model Performance Monitoring
- **Metrics tracking**: RMSE, MAE trends over time
- **Data drift detection**: Feature distribution changes  
- **Prediction monitoring**: Request volume, latency
- **Alerting**: Slack/email notifications for issues

### System Monitoring
- **API health**: Response times, error rates
- **Database**: Connection health, query performance
- **Pipeline**: Asset materialization success/failure
- **Infrastructure**: Resource usage, costs

## 🛠️ Development Commands

| Command | Description |
|---------|-------------|
| `make setup` | Initialize project environment |
| `make data` | Download and process full dataset |
| `make data-sample` | Download sample data for testing |
| `make train` | Train production model |
| `make train-baseline` | Train baseline model quickly |
| `make test` | Run all tests with coverage |
| `make lint` | Run code quality checks |
| `make format` | Format code with ruff |
| `make docker-up` | Start all Docker services |
| `make docker-down` | Stop all Docker services |
| `make clean` | Clean temporary files |
| `make clean-data` | Remove downloaded data |

## 📁 Project Structure

```
MyMLOps2025/
├── AI/                     # R&D, experiments, analysis
├── src/                    # Source code
│   ├── api/               # FastAPI application
│   ├── data/              # Data processing
│   ├── models/            # ML model training
│   ├── monitoring/        # Data drift monitoring
│   └── dagster_app/       # Dagster orchestration
├── tests/                 # Test suite
├── scripts/               # Utility scripts
├── docker/                # Docker configurations
├── data/                  # Data storage (gitignored)
├── models/                # Trained models (gitignored)
├── .github/workflows/     # CI/CD pipelines
└── docs/                  # Documentation
```

## 🔧 Configuration

### Environment Variables
Copy `.env.template` to `.env` and configure:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/nytaxi_mlops

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=nytaxi-duration-prediction

# Data
NYC_TAXI_BASE_URL=https://d37ci6vzurychx.cloudfront.net/trip-data/
TAXI_DATA_MONTHS=01,02,03

# API
API_HOST=0.0.0.0
API_PORT=8000
```

## 📚 Learning Resources

### MLOps Concepts
- [MLOps Zoomcamp](https://github.com/DataTalksClub/mlops-zoomcamp) - Course this project is based on
- [Dagster Docs](https://docs.dagster.io/) - Orchestration framework
- [MLflow Docs](https://mlflow.org/docs/) - Experiment tracking
- [Evidently AI Docs](https://docs.evidentlyai.com/) - ML monitoring

### NYC Taxi Data
- [TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) - Official data source
- [Data Dictionary](https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf) - Field descriptions

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** changes: `git commit -m 'Add amazing feature'`
4. **Push** to branch: `git push origin feature/amazing-feature`  
5. **Open** a Pull Request

### Development Guidelines
- Follow [PEP 8](https://pep8.org/) style guide
- Add tests for new features
- Update documentation
- Run `make dev-test` before committing

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [DataTalks.Club](https://datatalks.club/) for the MLOps Zoomcamp
- [NYC TLC](https://www.nyc.gov/site/tlc/) for providing the dataset
- Open source ML community for the amazing tools

---

**Built with ❤️ for learning MLOps engineering practices**