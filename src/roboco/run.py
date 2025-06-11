"""
Development runner functions for Roboco

This module contains development functions that are referenced in pyproject.toml scripts.
"""

import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd: list[str], cwd: str = None) -> int:
    """Run a command and return the exit code."""
    print(f"🚀 Running: {' '.join(cmd)}")
    if cwd:
        print(f"📁 In directory: {cwd}")
    
    try:
        result = subprocess.run(cmd, cwd=cwd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n⚠️  Command interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return 1

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
    
    test_file = example_path / "test_collaboration.py"
    if test_file.exists():
        return run_command([sys.executable, "test_collaboration.py"], str(example_path))
    
    # Look for other runnable files
    main_file = example_path / "main.py"
    if main_file.exists():
        return run_command([sys.executable, "main.py"], str(example_path))
    
    print(f"❌ No runnable script found in {example_path}")
    return 1

def run_tests() -> int:
    """Run the test suite."""
    return run_command([sys.executable, "-m", "pytest", "tests/", "-v"])

def run_api_dev() -> int:
    """Run the API development server."""
    return run_command([sys.executable, "-c", "from roboco_v0.api.server import run_dev_server; run_dev_server()"])

def run_ui() -> int:
    """Run the Streamlit UI."""
    ui_file = Path("src/roboco_v0/ui/app.py")
    if ui_file.exists():
        return run_command(["streamlit", "run", str(ui_file)])
    else:
        print("❌ Streamlit UI not found")
        return 1

def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = True) -> int:
    """Run the RoboCo server."""
    from roboco.server.api import run_server
    try:
        print(f"🚀 Starting RoboCo server on {host}:{port}")
        run_server(host=host, port=port, reload=reload)
        return 0
    except KeyboardInterrupt:
        print("\n⚠️  Server stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return 1

def dev():
    """Main development function for 'uv run dev'."""
    parser = argparse.ArgumentParser(description="Roboco Development Script")
    parser.add_argument(
        "command",
        nargs="?",
        default="example",
        choices=["example", "test", "api", "ui", "server", "help"],
        help="Development command to run"
    )
    parser.add_argument(
        "--name",
        default="superwriter",
        help="Example name to run (default: superwriter)"
    )
    
    args = parser.parse_args()
    
    print("🤖 Roboco Development Script")
    print("=" * 40)
    
    if args.command == "help":
        parser.print_help()
        print("\n📖 Available commands:")
        print("  example  - Run an example (default: superwriter)")  
        print("  test     - Run the test suite")
        print("  api      - Start API development server")
        print("  ui       - Start Streamlit UI")
        print("  server   - Start RoboCo multi-user server")
        print("\n💡 Usage examples:")
        print("  uv run dev")
        print("  uv run dev example --name superwriter")
        print("  uv run dev test")
        return 0
    
    elif args.command == "example":
        return run_example(args.name)
    
    elif args.command == "test":
        return run_tests()
    
    elif args.command == "api":
        return run_api_dev()
    
    elif args.command == "ui":
        return run_ui()
    
    elif args.command == "server":
        return run_server()
    
    else:
        print(f"❌ Unknown command: {args.command}")
        return 1

def test():
    """Test function for 'uv run test'."""
    parser = argparse.ArgumentParser(description="Roboco Test Runner")
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run tests with coverage reporting"
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip slow tests"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="tests/",
        help="Test path to run (default: tests/)"
    )
    
    args = parser.parse_args()
    
    print("🧪 Roboco Test Runner")
    print("=" * 30)
    
    cmd = [sys.executable, "-m", "pytest"]
    
    if args.coverage:
        cmd.extend(["--cov=src/roboco", "--cov-report=html", "--cov-report=term"])
    
    if args.fast:
        cmd.extend(["-m", "not slow"])
    
    if args.verbose:
        cmd.append("-v")
    
    cmd.append(args.path)
    
    return run_command(cmd)

def start():
    """Start function for 'uv run start' - runs the superwriter example by default."""
    print("🤖 Starting Roboco SuperWriter Example")
    print("=" * 45)
    return run_example("superwriter") 