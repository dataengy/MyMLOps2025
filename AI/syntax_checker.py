#!/usr/bin/env python3
"""
Syntax checker for MLOps pipeline - tests Python syntax without dependencies.
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Tuple, Dict


def check_python_syntax(file_path: Path) -> Tuple[bool, str]:
    """Check if a Python file has valid syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Parse the source code
        ast.parse(source, filename=str(file_path))
        return True, "Valid Python syntax"
    
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error reading file: {e}"


def find_python_files(directory: Path) -> List[Path]:
    """Find all Python files in a directory."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip certain directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    return python_files


def check_project_syntax() -> Dict[str, List[Tuple[Path, bool, str]]]:
    """Check syntax for all Python files in the project."""
    results = {}
    
    # Define directories to check
    directories = {
        'src': Path('src'),
        'tests': Path('tests'), 
        'scripts': Path('scripts'),
        'AI': Path('AI')
    }
    
    for dir_name, dir_path in directories.items():
        if dir_path.exists():
            results[dir_name] = []
            python_files = find_python_files(dir_path)
            
            for file_path in python_files:
                is_valid, message = check_python_syntax(file_path)
                results[dir_name].append((file_path, is_valid, message))
    
    return results


def main():
    """Main function to run syntax checks."""
    print("🔍 MLOps Pipeline Syntax Checker")
    print("=" * 50)
    
    results = check_project_syntax()
    
    total_files = 0
    valid_files = 0
    invalid_files = []
    
    for dir_name, file_results in results.items():
        if not file_results:
            continue
            
        print(f"\n📁 {dir_name}/ directory:")
        print("-" * 30)
        
        for file_path, is_valid, message in file_results:
            total_files += 1
            status = "✅" if is_valid else "❌"
            print(f"{status} {file_path.relative_to(Path.cwd())}")
            
            if is_valid:
                valid_files += 1
            else:
                invalid_files.append((file_path, message))
                print(f"   Error: {message}")
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"Total files checked: {total_files}")
    print(f"Valid files: {valid_files}")
    print(f"Invalid files: {total_files - valid_files}")
    
    if invalid_files:
        print(f"\n❌ Files with syntax errors:")
        for file_path, message in invalid_files:
            print(f"  - {file_path}: {message}")
        return 1
    else:
        print(f"\n✅ All Python files have valid syntax!")
        return 0


if __name__ == "__main__":
    sys.exit(main())