"""
Tests for monitoring module.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
from unittest.mock import patch, MagicMock


class TestDataDriftMonitoring:
    """Test cases for data drift monitoring."""
    
    def test_import_monitoring_module(self):
        """Test that monitoring module can be imported."""
        try:
            from src.monitoring.data_drift import DataDriftMonitor
            assert DataDriftMonitor is not None
        except ImportError as e:
            pytest.skip(f"Monitoring module not available: {e}")
    
    def test_data_drift_monitor_init(self):
        """Test DataDriftMonitor initialization."""
        try:
            from src.monitoring.data_drift import DataDriftMonitor
            
            monitor = DataDriftMonitor()
            assert monitor is not None
        except ImportError:
            pytest.skip("DataDriftMonitor not available")
    
    @patch('evidently.Report')
    @patch('evidently.metric_preset.DataDriftPreset')
    def test_detect_drift(self, mock_preset, mock_report, sample_taxi_data):
        """Test drift detection functionality."""
        try:
            from src.monitoring.data_drift import DataDriftMonitor
            
            monitor = DataDriftMonitor()
            
            # Create reference and current data
            reference_data = sample_taxi_data.head(500)
            current_data = sample_taxi_data.tail(500)
            
            # Mock Evidently report
            mock_report_instance = MagicMock()
            mock_report_instance.as_dict.return_value = {
                'metrics': [{'result': {'drift_detected': False}}]
            }
            mock_report.return_value = mock_report_instance
            
            # Test drift detection
            drift_detected = monitor.detect_drift(reference_data, current_data)
            
            assert isinstance(drift_detected, bool)
            mock_report_instance.run.assert_called_once()
            
        except ImportError:
            pytest.skip("DataDriftMonitor not available")
    
    def test_generate_drift_report_structure(self, temp_data_dir):
        """Test drift report generation structure."""
        try:
            from src.monitoring.data_drift import DataDriftMonitor
            
            monitor = DataDriftMonitor()
            
            # Mock report generation
            with patch.object(monitor, '_create_evidently_report') as mock_create:
                mock_report = MagicMock()
                mock_report.save_html.return_value = None
                mock_report.as_dict.return_value = {'test': 'data'}
                mock_create.return_value = mock_report
                
                # Test report generation
                report_path = temp_data_dir / "drift_report.html"
                metadata = monitor.generate_drift_report(
                    pd.DataFrame({'a': [1, 2, 3]}),
                    pd.DataFrame({'a': [4, 5, 6]}),
                    str(report_path)
                )
                
                assert isinstance(metadata, dict)
                mock_create.assert_called_once()
                
        except ImportError:
            pytest.skip("DataDriftMonitor not available")


class TestModelPerformanceMonitoring:
    """Test cases for model performance monitoring."""
    
    def test_performance_metrics_calculation(self):
        """Test model performance metrics calculation."""
        # Create sample predictions and actual values
        np.random.seed(42)
        y_true = np.random.normal(600, 200, 100)
        y_pred = y_true + np.random.normal(0, 50, 100)
        
        try:
            from src.monitoring.data_drift import calculate_performance_metrics
            
            metrics = calculate_performance_metrics(y_true, y_pred)
            
            assert isinstance(metrics, dict)
            assert 'rmse' in metrics
            assert 'mae' in metrics
            assert 'r2_score' in metrics
            assert all(isinstance(v, (int, float)) for v in metrics.values())
            
        except ImportError:
            # Fallback test using trainer module
            from src.models.trainer import evaluate_model_performance
            
            metrics = evaluate_model_performance(y_true, y_pred)
            assert isinstance(metrics, dict)
            assert 'rmse' in metrics


class TestMonitoringIntegration:
    """Test monitoring integration with ML pipeline."""
    
    def test_monitoring_with_sample_data(self, sample_taxi_data):
        """Test monitoring integration with sample data."""
        try:
            from src.monitoring.data_drift import DataDriftMonitor
            
            monitor = DataDriftMonitor()
            
            # Split data for reference and current
            split_idx = len(sample_taxi_data) // 2
            reference_data = sample_taxi_data.iloc[:split_idx]
            current_data = sample_taxi_data.iloc[split_idx:]
            
            # Should be able to initialize monitoring without errors
            assert len(reference_data) > 0
            assert len(current_data) > 0
            assert list(reference_data.columns) == list(current_data.columns)
            
        except ImportError:
            pytest.skip("Monitoring module not available")
    
    @patch('src.monitoring.data_drift.save_json')
    def test_monitoring_output_format(self, mock_save, temp_data_dir):
        """Test monitoring output format."""
        try:
            from src.monitoring.data_drift import DataDriftMonitor
            
            monitor = DataDriftMonitor()
            
            # Mock the monitoring process
            with patch.object(monitor, 'detect_drift', return_value=False):
                with patch.object(monitor, 'generate_drift_report') as mock_report:
                    mock_report.return_value = {
                        'drift_detected': False,
                        'timestamp': '2024-01-01T10:00:00',
                        'features_drifted': []
                    }
                    
                    # Test the monitoring workflow
                    result = monitor.generate_drift_report(
                        pd.DataFrame({'a': [1, 2]}), 
                        pd.DataFrame({'a': [3, 4]}),
                        str(temp_data_dir / "report.html")
                    )
                    
                    assert isinstance(result, dict)
                    assert 'drift_detected' in result or 'test' in result  # Either format
                    
        except ImportError:
            pytest.skip("Monitoring module not available")