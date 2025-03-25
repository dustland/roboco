#!/usr/bin/env python3
"""
Logger Standardization Script

This script finds and transforms files in the roboco project to
standardize the usage of the logger according to project guidelines.
"""

import os
import re
import sys
from pathlib import Path


def find_python_files(base_dir, exclude_dirs=None):
    """Find all Python files in the given directory."""
    if exclude_dirs is None:
        exclude_dirs = []
    
    python_files = []
    for root, dirs, files in os.walk(base_dir):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files


def analyze_file(file_path):
    """Analyze a Python file to check its logger usage."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if file already imports get_logger
    uses_get_logger = re.search(r'from\s+roboco\.core\.logger\s+import\s+get_logger', content) is not None
    
    # Check if file uses loguru.logger directly
    uses_loguru_direct = re.search(r'from\s+loguru\s+import\s+logger', content) is not None
    
    # Check if logger is initialized
    logger_initialized = re.search(r'logger\s*=\s*get_logger\(\s*__name__\s*\)', content) is not None
    
    # Count logger usages
    logger_usages = len(re.findall(r'logger\.(debug|info|warning|error|critical|exception)', content))
    
    return {
        'path': file_path,
        'uses_get_logger': uses_get_logger,
        'uses_loguru_direct': uses_loguru_direct,
        'logger_initialized': logger_initialized,
        'logger_usages': logger_usages
    }


def transform_file(file_path, dry_run=True):
    """Transform a file to use the standardized logger."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace direct loguru import with get_logger import
    if re.search(r'from\s+loguru\s+import\s+logger', content) is not None:
        content = re.sub(
            r'from\s+loguru\s+import\s+logger',
            'from roboco.core.logger import get_logger',
            content
        )
        
        # Add logger initialization if it doesn't exist and there are logger usages
        if (not re.search(r'logger\s*=\s*get_logger\(\s*__name__\s*\)', content) and 
            re.search(r'logger\.(debug|info|warning|error|critical|exception)', content)):
            
            # Find the last import statement
            import_matches = list(re.finditer(r'^.*import.*$', content, re.MULTILINE))
            if import_matches:
                last_import_pos = import_matches[-1].end()
                
                # Add two blank lines after the imports if there aren't any
                if content[last_import_pos:last_import_pos+2] != '\n\n':
                    if content[last_import_pos:last_import_pos+1] != '\n':
                        content = content[:last_import_pos] + '\n\n' + content[last_import_pos:]
                    else:
                        content = content[:last_import_pos] + '\n' + content[last_import_pos:]
                
                # Add logger initialization
                insert_pos = last_import_pos + 2
                logger_init = '# Initialize logger\nlogger = get_logger(__name__)\n\n'
                content = content[:insert_pos] + logger_init + content[insert_pos:]
    
    if not dry_run:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return content


def main():
    """Main function to run the script."""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <source_dir> [--apply]")
        sys.exit(1)
    
    source_dir = sys.argv[1]
    dry_run = '--apply' not in sys.argv
    
    if dry_run:
        print("Running in dry-run mode. Use --apply to actually modify files.")
    else:
        print("CAUTION: Files will be modified. Make sure you have a backup or clean git working tree.")
        response = input("Continue? (y/N): ")
        if response.lower() != 'y':
            print("Aborting.")
            sys.exit(0)
    
    # Find all Python files
    exclude_dirs = ['.git', 'venv', 'env', '.venv', '__pycache__', 'dist', 'build']
    python_files = find_python_files(source_dir, exclude_dirs)
    
    # Analyze files
    stats = {
        'total': 0,
        'needs_import_change': 0,
        'needs_initialization': 0,
        'already_standardized': 0,
        'transformed': 0
    }
    
    for file_path in python_files:
        stats['total'] += 1
        analysis = analyze_file(file_path)
        
        # Skip files that don't use logger at all
        if analysis['logger_usages'] == 0 and not analysis['uses_loguru_direct'] and not analysis['uses_get_logger']:
            continue
        
        # Determine if file needs changes
        needs_changes = analysis['uses_loguru_direct'] or (
            analysis['uses_get_logger'] and not analysis['logger_initialized'] and analysis['logger_usages'] > 0
        )
        
        if needs_changes:
            print(f"Transforming: {file_path}")
            if analysis['uses_loguru_direct']:
                stats['needs_import_change'] += 1
            if not analysis['logger_initialized'] and analysis['logger_usages'] > 0:
                stats['needs_initialization'] += 1
            
            transform_file(file_path, dry_run)
            stats['transformed'] += 1
        else:
            if analysis['uses_get_logger'] and analysis['logger_initialized']:
                stats['already_standardized'] += 1
    
    # Print summary
    print("\nSummary:")
    print(f"Total Python files: {stats['total']}")
    print(f"Files needing import change: {stats['needs_import_change']}")
    print(f"Files needing logger initialization: {stats['needs_initialization']}")
    print(f"Files already standardized: {stats['already_standardized']}")
    print(f"Files transformed: {stats['transformed']}")
    
    if dry_run:
        print("\nThis was a dry run. Use --apply to actually modify files.")


if __name__ == "__main__":
    main() 