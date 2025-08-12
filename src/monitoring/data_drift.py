"""
Data drift monitoring using Evidently AI.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any
from evidently import ColumnMapping
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, DataQualityPreset
from evidently.metrics import *
import json
from datetime import datetime


class DataDriftMonitor:
    """Monitor data drift and data quality using Evidently."""
    
    def __init__(self, reference_data: pd.DataFrame, feature_columns: list):
        self.reference_data = reference_data
        self.feature_columns = feature_columns
        self.target_column = "trip_duration"
        
        # Define column mapping for Evidently
        self.column_mapping = ColumnMapping(
            target=self.target_column,
            prediction=None,  # Will be set when we have predictions
            numerical_features=[
                col for col in feature_columns 
                if col in reference_data.columns and 
                reference_data[col].dtype in ['int64', 'float64']
            ],
            categorical_features=[
                col for col in feature_columns 
                if col in reference_data.columns and 
                reference_data[col].dtype == 'object'
            ]
        )
    
    def detect_data_drift(
        self, 
        current_data: pd.DataFrame,
        report_path: Path = None
    ) -> Dict[str, Any]:
        """Detect data drift between reference and current data."""
        
        # Create data drift report
        data_drift_report = Report(metrics=[
            DataDriftPreset(),
        ])
        
        data_drift_report.run(
            reference_data=self.reference_data,
            current_data=current_data,
            column_mapping=self.column_mapping
        )
        
        # Save report if path provided
        if report_path:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            data_drift_report.save_html(str(report_path))
        
        # Extract drift metrics
        report_dict = data_drift_report.as_dict()
        
        drift_results = {
            "timestamp": datetime.now().isoformat(),
            "dataset_drift": report_dict["metrics"][0]["result"]["dataset_drift"],
            "drift_share": report_dict["metrics"][0]["result"]["drift_share"],
            "number_of_drifted_columns": report_dict["metrics"][0]["result"]["number_of_drifted_columns"],
            "drifted_features": [],
        }
        
        # Get individual feature drift
        for feature_result in report_dict["metrics"][0]["result"]["drift_by_columns"].values():
            if feature_result["drift_detected"]:
                drift_results["drifted_features"].append({
                    "feature": feature_result["column_name"],
                    "drift_score": feature_result["drift_score"],
                    "stattest_name": feature_result["stattest_name"]
                })
        
        return drift_results
    
    def generate_data_quality_report(
        self, 
        current_data: pd.DataFrame,
        report_path: Path = None
    ) -> Dict[str, Any]:
        """Generate data quality report."""
        
        data_quality_report = Report(metrics=[
            DataQualityPreset(),
        ])
        
        data_quality_report.run(
            reference_data=self.reference_data,
            current_data=current_data,
            column_mapping=self.column_mapping
        )
        
        # Save report if path provided
        if report_path:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            data_quality_report.save_html(str(report_path))
        
        # Extract quality metrics
        report_dict = data_quality_report.as_dict()
        
        quality_results = {
            "timestamp": datetime.now().isoformat(),
            "n_rows": len(current_data),
            "n_features": len(self.feature_columns),
            "missing_values": current_data[self.feature_columns].isnull().sum().sum(),
            "duplicated_rows": current_data.duplicated().sum(),
        }
        
        return quality_results
    
    def check_model_performance_drift(
        self,
        current_data: pd.DataFrame,
        predictions: np.ndarray,
        report_path: Path = None
    ) -> Dict[str, Any]:
        """Check for model performance drift."""
        
        # Add predictions to current data
        current_data_with_pred = current_data.copy()
        current_data_with_pred['prediction'] = predictions
        
        # Update column mapping to include predictions
        column_mapping_with_pred = ColumnMapping(
            target=self.target_column,
            prediction='prediction',
            numerical_features=self.column_mapping.numerical_features,
            categorical_features=self.column_mapping.categorical_features
        )
        
        # Create model performance report
        performance_report = Report(metrics=[
            RegressionPerformanceMetrics(),
        ])
        
        # Reference data should also have predictions for comparison
        # For now, we'll just analyze current data
        performance_report.run(
            reference_data=None,  # Skip reference for now
            current_data=current_data_with_pred,
            column_mapping=column_mapping_with_pred
        )
        
        # Save report if path provided
        if report_path:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            performance_report.save_html(str(report_path))
        
        # Extract performance metrics
        report_dict = performance_report.as_dict()
        
        performance_results = {
            "timestamp": datetime.now().isoformat(),
            "mean_error": report_dict["metrics"][0]["result"]["current"]["mean_error"],
            "mean_abs_error": report_dict["metrics"][0]["result"]["current"]["mean_abs_error"],
            "mean_abs_perc_error": report_dict["metrics"][0]["result"]["current"]["mean_abs_perc_error"],
        }
        
        return performance_results


def create_monitoring_dashboard(
    reference_data: pd.DataFrame,
    current_data: pd.DataFrame,
    feature_columns: list,
    predictions: np.ndarray = None,
    output_dir: Path = Path("monitoring_reports")
) -> Dict[str, str]:
    """Create comprehensive monitoring dashboard."""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    monitor = DataDriftMonitor(reference_data, feature_columns)
    
    reports = {}
    
    # Data drift report
    drift_report_path = output_dir / f"data_drift_report_{timestamp}.html"
    drift_results = monitor.detect_data_drift(current_data, drift_report_path)
    reports["data_drift"] = str(drift_report_path)
    
    # Data quality report
    quality_report_path = output_dir / f"data_quality_report_{timestamp}.html"
    quality_results = monitor.generate_data_quality_report(current_data, quality_report_path)
    reports["data_quality"] = str(quality_report_path)
    
    # Model performance report (if predictions provided)
    if predictions is not None:
        perf_report_path = output_dir / f"model_performance_report_{timestamp}.html"
        perf_results = monitor.check_model_performance_drift(
            current_data, predictions, perf_report_path
        )
        reports["model_performance"] = str(perf_report_path)
    
    # Save summary metrics
    summary = {
        "timestamp": timestamp,
        "data_drift": drift_results,
        "data_quality": quality_results,
    }
    
    if predictions is not None:
        summary["model_performance"] = perf_results
    
    summary_path = output_dir / f"monitoring_summary_{timestamp}.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    reports["summary"] = str(summary_path)
    
    return reports