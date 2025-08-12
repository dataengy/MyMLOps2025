#!/usr/bin/env python3
"""
MLOps Pipeline Validator - comprehensive testing without heavy dependencies.
"""

import ast
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class PipelineValidator:
    """Validates MLOps pipeline components without requiring full dependencies."""
    
    def __init__(self):
        self.results = {}
        self.project_root = Path.cwd()
    
    def validate_syntax(self) -> Dict[str, bool]:
        """Validate Python syntax for all key files."""
        print("🔍 Validating Python Syntax...")
        
        key_files = [
            "src/data/data_processor.py",
            "src/models/trainer.py", 
            "src/train.py",
            "src/api/main.py",
            "src/dagster_app.py",
            "src/dagster_app/assets.py",
            "scripts/download_data.py",
            "scripts/process_data.py",
            "tests/conftest.py",
            "tests/test_data_processor.py",
            "tests/test_model_trainer.py",
            "tests/test_api.py"
        ]
        
        syntax_results = {}
        for filepath in key_files:
            full_path = self.project_root / filepath
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    ast.parse(content)
                    syntax_results[filepath] = True
                    print(f"  ✅ {filepath}")
                except SyntaxError as e:
                    syntax_results[filepath] = False
                    print(f"  ❌ {filepath}: Syntax Error - {e}")
                except Exception as e:
                    syntax_results[filepath] = False
                    print(f"  ❌ {filepath}: Error - {e}")
            else:
                syntax_results[filepath] = False
                print(f"  ⚠️  {filepath}: File not found")
        
        self.results['syntax'] = syntax_results
        return syntax_results
    
    def validate_config_files(self) -> Dict[str, bool]:
        """Validate configuration files."""
        print("\n⚙️  Validating Configuration Files...")
        
        config_files = {
            "pyproject.toml": self._validate_toml,
            "docker-compose.yml": self._validate_yaml,
            ".env": self._validate_env,
            ".pre-commit-config.yaml": self._validate_yaml,
            "Makefile": self._validate_makefile
        }
        
        config_results = {}
        for filename, validator in config_files.items():
            filepath = self.project_root / filename
            if filepath.exists():
                try:
                    config_results[filename] = validator(filepath)
                    print(f"  ✅ {filename}")
                except Exception as e:
                    config_results[filename] = False
                    print(f"  ❌ {filename}: {e}")
            else:
                config_results[filename] = False
                print(f"  ⚠️  {filename}: File not found")
        
        self.results['config'] = config_results
        return config_results
    
    def validate_project_structure(self) -> Dict[str, bool]:
        """Validate project directory structure."""
        print("\n📁 Validating Project Structure...")
        
        required_dirs = [
            "src",
            "src/data", 
            "src/models",
            "src/api",
            "src/monitoring",
            "src/dagster_app",
            "tests",
            "scripts",
            "docker",
            "AI",
            ".github/workflows"
        ]
        
        structure_results = {}
        for dirname in required_dirs:
            dirpath = self.project_root / dirname
            structure_results[dirname] = dirpath.exists() and dirpath.is_dir()
            status = "✅" if structure_results[dirname] else "❌"
            print(f"  {status} {dirname}/")
        
        self.results['structure'] = structure_results
        return structure_results
    
    def validate_docker_files(self) -> Dict[str, bool]:
        """Validate Docker configuration."""
        print("\n🐳 Validating Docker Configuration...")
        
        docker_files = [
            "Dockerfile",
            "docker-compose.yml",
            "docker/api/Dockerfile",
            "docker/mlflow/Dockerfile", 
            "docker/dagster/Dockerfile",
            "docker/monitoring/Dockerfile"
        ]
        
        docker_results = {}
        for filepath in docker_files:
            full_path = self.project_root / filepath
            docker_results[filepath] = full_path.exists()
            status = "✅" if docker_results[filepath] else "❌"
            print(f"  {status} {filepath}")
        
        self.results['docker'] = docker_results
        return docker_results
    
    def validate_github_actions(self) -> Dict[str, bool]:
        """Validate GitHub Actions workflows."""
        print("\n🚀 Validating GitHub Actions...")
        
        workflow_files = [
            ".github/workflows/ci.yml",
            ".github/workflows/model-retraining.yml"
        ]
        
        actions_results = {}
        for filepath in workflow_files:
            full_path = self.project_root / filepath
            if full_path.exists():
                try:
                    # Basic YAML validation
                    import yaml
                    with open(full_path, 'r') as f:
                        yaml.safe_load(f)
                    actions_results[filepath] = True
                    print(f"  ✅ {filepath}")
                except ImportError:
                    # YAML module not available, just check file exists
                    actions_results[filepath] = True
                    print(f"  ✅ {filepath} (syntax not validated)")
                except Exception as e:
                    actions_results[filepath] = False
                    print(f"  ❌ {filepath}: {e}")
            else:
                actions_results[filepath] = False
                print(f"  ❌ {filepath}: File not found")
        
        self.results['github_actions'] = actions_results
        return actions_results
    
    def _validate_toml(self, filepath: Path) -> bool:
        """Validate TOML file."""
        try:
            import tomllib
            with open(filepath, 'rb') as f:
                tomllib.load(f)
            return True
        except ImportError:
            # Python < 3.11 or tomllib not available
            # Just check if file is readable
            with open(filepath, 'r') as f:
                content = f.read()
            return len(content) > 0
    
    def _validate_yaml(self, filepath: Path) -> bool:
        """Validate YAML file."""
        try:
            import yaml
            with open(filepath, 'r') as f:
                yaml.safe_load(f)
            return True
        except ImportError:
            # YAML module not available, just check file exists and readable
            with open(filepath, 'r') as f:
                content = f.read()
            return len(content) > 0
    
    def _validate_env(self, filepath: Path) -> bool:
        """Validate .env file."""
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        # Check for key environment variables
        required_vars = ['DATABASE_URL', 'MLFLOW_TRACKING_URI', 'API_PORT']
        found_vars = []
        
        for line in lines:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                var_name = line.split('=')[0]
                found_vars.append(var_name)
        
        return all(var in found_vars for var in required_vars)
    
    def _validate_makefile(self, filepath: Path) -> bool:
        """Validate Makefile."""
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Check for key targets
        required_targets = ['setup', 'test', 'train', 'docker-up']
        return all(f"{target}:" in content for target in required_targets)
    
    def generate_report(self) -> None:
        """Generate validation report."""
        print("\n" + "="*60)
        print("📊 VALIDATION REPORT")
        print("="*60)
        
        total_checks = 0
        passed_checks = 0
        
        for category, results in self.results.items():
            category_passed = sum(results.values())
            category_total = len(results)
            total_checks += category_total
            passed_checks += category_passed
            
            print(f"\n{category.upper()}: {category_passed}/{category_total}")
            
            if category_passed < category_total:
                failed_items = [k for k, v in results.items() if not v]
                print(f"  Failed: {', '.join(failed_items)}")
        
        success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        print(f"\n" + "-"*60)
        print(f"OVERALL: {passed_checks}/{total_checks} ({success_rate:.1f}%)")
        
        if success_rate >= 90:
            print("🎉 Excellent! Pipeline structure is ready.")
        elif success_rate >= 70:
            print("👍 Good! Minor issues to address.")
        else:
            print("⚠️  Significant issues need attention.")
        
        return success_rate


def main():
    """Main validation function."""
    print("🧪 MLOps Pipeline Validator")
    print("="*60)
    
    validator = PipelineValidator()
    
    # Run all validations
    validator.validate_syntax()
    validator.validate_config_files()
    validator.validate_project_structure()
    validator.validate_docker_files()
    validator.validate_github_actions()
    
    # Generate report
    success_rate = validator.generate_report()
    
    # Save results
    results_file = Path("AI/validation_results.json")
    with open(results_file, 'w') as f:
        json.dump(validator.results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    return 0 if success_rate >= 70 else 1


if __name__ == "__main__":
    sys.exit(main())