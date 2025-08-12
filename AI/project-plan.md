# MLOps NYTaxi Project - Technical Plan

## Problem Statement
Build an end-to-end MLOps pipeline to predict NYC taxi trip duration using historical trip data. This demonstrates modern ML engineering practices including automated training, deployment, and monitoring.

## Dataset
- **Source**: NYC TLC Trip Record Data (PARQUET format)
- **Features**: pickup/dropoff times, locations, distances, fares, passenger count
- **Target**: Trip duration (derived from pickup/dropoff times)
- **Size**: ~2-3M records per month, using 3-6 months for training

## ML Approach
1. **Baseline**: Linear regression with basic features
2. **Advanced**: Gradient boosting with engineered features
3. **Features**: Time-based, location-based, distance, weather (optional)
4. **Validation**: Time-based split (avoid data leakage)

## Architecture Decisions (Simplest Options)

### Data Stack
- **DuckDB**: Local analytics database, excellent for data exploration
- **Pandas**: Data manipulation and feature engineering
- **PostgreSQL**: Model metadata and experiment results storage

### ML Stack
- **scikit-learn**: Simple, reliable, good for tabular data
- **MLflow**: Experiment tracking, model registry, deployment
- **Dagster**: Modern orchestration with asset lineage

### Infrastructure
- **Docker Compose**: Local development environment
- **GitHub Actions**: CI/CD pipelines
- **Terraform**: Infrastructure as code for cloud deployment

### Monitoring
- **Evidently**: Data drift and model performance monitoring
- **Grafana**: Dashboards (if needed)

## Success Metrics
- **Model Performance**: RMSE < 300 seconds, R² > 0.7
- **Pipeline Reliability**: 99% successful runs
- **Deployment Speed**: < 30 minutes from commit to production
- **Data Freshness**: Daily model retraining capability

## Risk Mitigation
- Start with small dataset (1 month) for rapid prototyping
- Use local development first, then containerize
- Implement comprehensive testing at each stage
- Monitor data quality and model drift

## Timeline
- **Week 1**: Data pipeline + baseline model
- **Week 2**: Orchestration + MLflow integration  
- **Week 3**: Deployment + monitoring
- **Week 4**: Testing + production readiness