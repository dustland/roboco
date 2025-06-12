"""
Simple runner functions for Roboco examples
"""

import sys
import subprocess
from pathlib import Path

def run_example(example_name: str = "superwriter") -> int:
    """Run an example."""
    examples_dir = Path("examples")
    example_path = examples_dir / example_name
    
    if not example_path.exists():
        print(f"❌ Example '{example_name}' not found in {examples_dir}")
        available = [d.name for d in examples_dir.iterdir() if d.is_dir()]
        if available:
            print(f"📋 Available examples: {', '.join(available)}")
        return 1
    
    # Look for demo.py first, then other runnable files
    demo_file = example_path / "demo.py"
    if demo_file.exists():
        print(f"🚀 Running {example_name} example...")
        result = subprocess.run([sys.executable, "demo.py"], cwd=str(example_path))
        return result.returncode
    
    main_file = example_path / "main.py"
    if main_file.exists():
        print(f"🚀 Running {example_name} example...")
        result = subprocess.run([sys.executable, "main.py"], cwd=str(example_path))
        return result.returncode
    
    print(f"❌ No demo.py or main.py found in {example_path}")
    return 1

def start():
    """Start function for 'uv run start' - runs the superwriter example."""
    print("🤖 Starting Roboco SuperWriter Example")
    print("=" * 45)
    return run_example("superwriter") 