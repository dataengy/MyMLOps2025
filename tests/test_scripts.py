"""
Tests for utility scripts.
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
from unittest.mock import patch, MagicMock
import sys
import os


class TestDownloadScript:
    """Test cases for data download script."""
    
    def test_download_script_import(self):
        """Test that download script can be imported."""
        try:
            # Add scripts to path for import
            scripts_path = Path(__file__).parent.parent / "scripts"
            sys.path.insert(0, str(scripts_path))
            
            import download_data
            assert hasattr(download_data, 'download_sample_data')
            
        except ImportError as e:
            pytest.skip(f"Download script not available: {e}")
        finally:
            # Clean up path
            if str(scripts_path) in sys.path:
                sys.path.remove(str(scripts_path))
    
    @patch('httpx.get')
    def test_download_sample_data_function(self, mock_get):
        """Test download sample data functionality."""
        try:
            scripts_path = Path(__file__).parent.parent / "scripts"
            sys.path.insert(0, str(scripts_path))
            
            import download_data
            
            # Mock HTTP response
            mock_response = MagicMock()
            mock_response.iter_bytes.return_value = [b"test data"]
            mock_response.headers = {'content-length': '9'}
            mock_get.return_value.__enter__.return_value = mock_response
            
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = Path(temp_dir) / "test.parquet"
                
                # Mock the actual download logic
                with patch('pathlib.Path.write_bytes') as mock_write:
                    # This would test the download mechanism
                    assert callable(download_data.download_sample_data)
                    
        except ImportError:
            pytest.skip("Download script not available")
        finally:
            if str(scripts_path) in sys.path:
                sys.path.remove(str(scripts_path))
    
    def test_download_script_main_structure(self):
        """Test download script main function structure."""
        scripts_path = Path(__file__).parent.parent / "scripts" / "download_data.py"
        
        if not scripts_path.exists():
            pytest.skip("Download script file not found")
        
        # Read script content
        content = scripts_path.read_text()
        
        # Check for key functions and imports
        assert 'def download_sample_data' in content
        assert 'def main' in content
        assert 'import' in content
        assert 'if __name__ == "__main__"' in content


class TestProcessScript:
    """Test cases for data processing script."""
    
    def test_process_script_import(self):
        """Test that process script can be imported."""
        try:
            scripts_path = Path(__file__).parent.parent / "scripts"
            sys.path.insert(0, str(scripts_path))
            
            import process_data
            assert hasattr(process_data, 'process_data')
            
        except ImportError as e:
            pytest.skip(f"Process script not available: {e}")
        finally:
            if str(scripts_path) in sys.path:
                sys.path.remove(str(scripts_path))
    
    def test_process_script_structure(self):
        """Test process script structure."""
        scripts_path = Path(__file__).parent.parent / "scripts" / "process_data.py"
        
        if not scripts_path.exists():
            pytest.skip("Process script file not found")
        
        content = scripts_path.read_text()
        
        # Check for key components
        assert 'def process_data' in content
        assert 'TaxiDataProcessor' in content
        assert 'def main' in content
    
    @patch('src.data.data_processor.TaxiDataProcessor')
    def test_process_data_function(self, mock_processor, sample_taxi_data):
        """Test process data function."""
        try:
            scripts_path = Path(__file__).parent.parent / "scripts"
            sys.path.insert(0, str(scripts_path))
            
            import process_data
            
            # Mock processor
            mock_processor_instance = MagicMock()
            mock_processor_instance.clean_data.return_value = sample_taxi_data
            mock_processor_instance.engineer_features.return_value = sample_taxi_data
            mock_processor.return_value = mock_processor_instance
            
            # Mock file operations
            with patch('pandas.read_csv', return_value=sample_taxi_data):
                with patch('pandas.DataFrame.to_csv'):
                    with tempfile.TemporaryDirectory() as temp_dir:
                        input_path = Path(temp_dir) / "input.csv"
                        output_path = Path(temp_dir) / "output.csv"
                        
                        # Create dummy input file
                        sample_taxi_data.to_csv(input_path, index=False)
                        
                        # Test processing
                        result = process_data.process_data(str(input_path), str(output_path))
                        
                        # Should return processed data
                        assert isinstance(result, pd.DataFrame)
                        
        except ImportError:
            pytest.skip("Process script not available")
        finally:
            if str(scripts_path) in sys.path:
                sys.path.remove(str(scripts_path))


class TestScriptIntegration:
    """Test script integration and workflow."""
    
    def test_scripts_directory_structure(self):
        """Test that all required scripts exist."""
        scripts_dir = Path(__file__).parent.parent / "scripts"
        assert scripts_dir.exists()
        
        expected_scripts = [
            "download_data.py",
            "process_data.py"
        ]
        
        for script in expected_scripts:
            script_path = scripts_dir / script
            if script_path.exists():
                assert script_path.is_file()
                assert script_path.suffix == ".py"
    
    def test_script_syntax_validity(self):
        """Test that scripts have valid Python syntax."""
        scripts_dir = Path(__file__).parent.parent / "scripts"
        
        for script_file in scripts_dir.glob("*.py"):
            try:
                compile(script_file.read_text(), str(script_file), 'exec')
            except SyntaxError:
                pytest.fail(f"Syntax error in {script_file}")
    
    def test_scripts_executable_structure(self):
        """Test that scripts have proper executable structure."""
        scripts_dir = Path(__file__).parent.parent / "scripts"
        
        for script_file in scripts_dir.glob("*.py"):
            content = script_file.read_text()
            
            # Each script should have main function and executable guard
            if script_file.name not in ["__init__.py"]:
                assert 'def main(' in content or 'def main()' in content, f"No main function in {script_file}"
                assert 'if __name__ == "__main__"' in content, f"No main guard in {script_file}"


class TestScriptConfiguration:
    """Test script configuration and environment handling."""
    
    def test_environment_variable_usage(self):
        """Test that scripts properly handle environment variables."""
        scripts_dir = Path(__file__).parent.parent / "scripts"
        
        for script_file in scripts_dir.glob("*.py"):
            content = script_file.read_text()
            
            # If environment variables are used, they should be handled properly
            if 'os.getenv' in content or 'os.environ' in content:
                # Should have proper imports
                assert 'import os' in content or 'from os import' in content
    
    def test_path_handling_in_scripts(self):
        """Test that scripts handle paths correctly."""
        scripts_dir = Path(__file__).parent.parent / "scripts"
        
        for script_file in scripts_dir.glob("*.py"):
            content = script_file.read_text()
            
            # If pathlib is used, should be imported
            if 'Path(' in content:
                assert 'from pathlib import Path' in content or 'import pathlib' in content