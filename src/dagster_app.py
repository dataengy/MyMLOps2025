"""
Main Dagster application module.
"""

from dagster import Definitions
from .dagster_app.assets import (
    raw_taxi_data,
    cleaned_taxi_data,
    feature_engineered_data,
    train_test_data,
    trained_model,
    model_evaluation,
    model_artifacts
)

# Define the Dagster definitions
defs = Definitions(
    assets=[
        raw_taxi_data,
        cleaned_taxi_data,
        feature_engineered_data,
        train_test_data,
        trained_model,
        model_evaluation,
        model_artifacts
    ]
)