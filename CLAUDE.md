# MLOps NYTaxi Project

## Project Overview
End-to-end MLOps pipeline for NYC Taxi trip duration prediction using modern ML infrastructure.

## Tech Stack Selection (Simplest Options)
- **Data Processing**: DuckDB + Pandas (local development)
- **Orchestration**: Dagster (simple, modern, great for ML workflows)
- **ML Framework**: scikit-learn + pandas
- **Experiment Tracking**: MLflow
- **Monitoring**: Evidently AI
- **Storage**: PostgreSQL (local) + S3 (cloud)
- **Containerization**: Docker Compose
- **CI/CD**: GitHub Actions
- **Infrastructure**: Terraform
- **Package Management**: uv
- **Code Quality**: ruff, pre-commit, pytest

## ML Task
Predict taxi trip duration based on pickup/dropoff locations, time, and trip characteristics using NYC TLC trip record data.

## Project Structure
```
.
├── AI/                 # R&D, experiments, analysis
├── src/               # Source code
├── tests/             # Tests
├── data/              # Data storage
├── docs/              # Documentation
├── scripts/           # Utility scripts
├── docker/            # Docker configurations
├── .github/workflows/ # CI/CD
└── infrastructure/    # Terraform configs
```

## Development Commands
- `make setup` - Initialize project
- `make data` - Download and prepare data
- `make train` - Train model
- `make deploy` - Deploy model
- `make test` - Run tests
- `make lint` - Code quality checks