#!/usr/bin/env python3
"""
Test runner for AgentX framework.

Simple script to run all tests with proper configuration.
"""

import sys
import subprocess
from pathlib import Path


def run_tests():
    """Run the test suite."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    # Change to project root
    import os
    os.chdir(project_root)
    
    # Run pytest with configuration
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--strict-markers",  # Strict marker checking
        "-x",  # Stop on first failure
    ]
    
    print("🧪 Running AgentX Framework Tests...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


if __name__ == "__main__":
    exit_code = run_tests()
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code: {exit_code}")
    
    sys.exit(exit_code) 