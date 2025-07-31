#!/usr/bin/env python3
"""Validate all test file imports work correctly."""

import sys
import importlib.util
from pathlib import Path


def validate_test_file_imports():
    """Check all test files can be imported without errors."""
    project_root = Path(__file__).parent.parent
    
    # Find all test files
    test_files = []
    for test_pattern in ["tests/**/test_*.py", "test_*.py"]:
        test_files.extend(project_root.glob(test_pattern))
    
    failed_imports = []
    successful_imports = []
    
    print("Validating test file imports...")
    print("=" * 50)
    
    for test_file in sorted(test_files):
        # Skip the add_timeouts.py script itself
        if "add_timeouts.py" in str(test_file):
            continue
            
        try:
            # Try to import the test file
            spec = importlib.util.spec_from_file_location("test_module", test_file)
            if spec is None:
                failed_imports.append((test_file, "Could not create module spec"))
                print(f"❌ {test_file.relative_to(project_root)}: Could not create module spec")
                continue
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            successful_imports.append(test_file)
            print(f"✅ {test_file.relative_to(project_root)}")
            
        except Exception as e:
            failed_imports.append((test_file, str(e)))
            print(f"❌ {test_file.relative_to(project_root)}: {e}")
    
    print("=" * 50)
    print(f"Results: {len(successful_imports)} successful, {len(failed_imports)} failed")
    
    if failed_imports:
        print("\nFailed imports:")
        for test_file, error in failed_imports:
            print(f"  {test_file.relative_to(project_root)}: {error}")
    
    return len(failed_imports) == 0


if __name__ == "__main__":
    success = validate_test_file_imports()
    sys.exit(0 if success else 1)