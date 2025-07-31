#!/usr/bin/env python3
"""
Script to add @pytest.mark.timeout() decorators to all test methods.
Fixed version that only modifies project test files.
"""

import os
import re
from pathlib import Path

def add_timeout_decorators(file_path: Path, timeout_seconds: int = 30):
    """Add timeout decorators to test methods in a file."""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Skip if timeout decorators already exist
    if '@pytest.mark.timeout' in content:
        print(f"Skipping {file_path} - already has timeout decorators")
        return False
    
    lines = content.split('\n')
    modified_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Look for test method definitions
        if re.match(r'\s*def test_.*\(', line):
            # Add timeout decorator before the test method
            indent = len(line) - len(line.lstrip())
            decorator = ' ' * indent + f'@pytest.mark.timeout({timeout_seconds})'
            modified_lines.append(decorator)
            modified_lines.append(line)
        else:
            modified_lines.append(line)
        
        i += 1
    
    # Write back the modified content
    with open(file_path, 'w') as f:
        f.write('\n'.join(modified_lines))
    
    print(f"Added timeout decorators to {file_path}")
    return True

def main():
    """Main function to process only project test files."""
    project_root = Path('/home/ubuntu/projects/foxtrot')
    
    # Define timeout values for different test types
    timeout_configs = {
        'unit': 10,      # Unit tests should be fast
        'integration': 30,  # Integration tests can be slower
        'e2e': 60       # E2E tests may need more time
    }
    
    # Only look for test files in project directories, not .venv
    project_test_paths = [
        'tests',
        '.',  # Root level test files
    ]
    
    test_files = []
    
    # Find test files only in project directories
    for base_path in project_test_paths:
        search_path = project_root / base_path
        if search_path.exists():
            for pattern in ['**/test_*.py', '**/*_test.py']:
                found_files = list(search_path.glob(pattern))
                # Filter out .venv and other excluded directories
                project_files = [
                    f for f in found_files 
                    if '.venv' not in str(f) 
                    and '__pycache__' not in str(f)
                    and 'site-packages' not in str(f)
                ]
                test_files.extend(project_files)
    
    # Remove duplicates
    test_files = list(set(test_files))
    
    modified_count = 0
    
    for test_file in test_files:
        # Determine timeout based on file path
        file_str = str(test_file)
        if '/unit/' in file_str:
            timeout = timeout_configs['unit']
        elif '/integration/' in file_str:
            timeout = timeout_configs['integration']
        elif '/e2e/' in file_str:
            timeout = timeout_configs['e2e']
        else:
            # Default for other test files
            timeout = timeout_configs['unit']
        
        if add_timeout_decorators(test_file, timeout):
            modified_count += 1
    
    print(f"\nProcessed {len(test_files)} test files, modified {modified_count}")
    print("\nProject test files found:")
    for f in sorted(test_files):
        print(f"  {f}")

if __name__ == '__main__':
    main()