-- Initialize database for MLflow and project metadata

-- Create MLflow database if it doesn't exist
SELECT 'CREATE DATABASE mlflow_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'mlflow_db')\gexec

-- Create schemas for different components
CREATE SCHEMA IF NOT EXISTS mlflow;
CREATE SCHEMA IF NOT EXISTS dagster;
CREATE SCHEMA IF NOT EXISTS monitoring;

-- Create monitoring table for storing drift reports
CREATE TABLE IF NOT EXISTS monitoring.data_drift_reports (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dataset_drift BOOLEAN,
    drift_share FLOAT,
    number_of_drifted_columns INTEGER,
    drifted_features JSONB,
    report_path TEXT
);

-- Create table for model performance metrics
CREATE TABLE IF NOT EXISTS monitoring.model_performance (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model_version TEXT,
    rmse FLOAT,
    mae FLOAT,
    r2_score FLOAT,
    data_samples INTEGER
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_drift_reports_timestamp ON monitoring.data_drift_reports(timestamp);
CREATE INDEX IF NOT EXISTS idx_model_performance_timestamp ON monitoring.model_performance(timestamp);
CREATE INDEX IF NOT EXISTS idx_model_performance_version ON monitoring.model_performance(model_version);

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA mlflow TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA dagster TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA monitoring TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA monitoring TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA monitoring TO postgres;