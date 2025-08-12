#!/usr/bin/env python3
"""
Simple syntax test for key pipeline files.
"""

import ast
import os

def test_file_syntax(filepath):
    """Test if a file has valid Python syntax."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        ast.parse(content)
        return True, "OK"
    except SyntaxError as e:
        return False, f"Syntax Error: {e}"
    except FileNotFoundError:
        return False, "File not found"
    except Exception as e:
        return False, f"Error: {e}"

# Test key files
test_files = [
    "src/data/data_processor.py",
    "src/models/trainer.py", 
    "src/train.py",
    "src/api/main.py",
    "src/dagster_app.py",
    "scripts/download_data.py",
    "scripts/process_data.py"
]

print("Testing Python syntax:")
print("=" * 40)

all_valid = True
for filepath in test_files:
    if os.path.exists(filepath):
        valid, message = test_file_syntax(filepath)
        status = "✅" if valid else "❌"
        print(f"{status} {filepath}: {message}")
        if not valid:
            all_valid = False
    else:
        print(f"⚠️  {filepath}: File not found")
        all_valid = False

print("\n" + "=" * 40)
if all_valid:
    print("✅ All files have valid Python syntax!")
else:
    print("❌ Some files have syntax errors")