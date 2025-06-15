#!/usr/bin/env python3
"""
Universal AgentX CLI

Provides a unified command-line interface for all AgentX operations.
"""

import sys
import argparse
from typing import Optional, List
from pathlib import Path

from ..run import start, monitor, web, run_example


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
            prog="agentx",
    description="🤖 AgentX - Multi-Agent Framework with Observability",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  agentx start                    # Start API server with observability
agentx monitor                  # Start observability monitor (CLI)
agentx monitor --web            # Start web dashboard
agentx status                   # Show system status
agentx example superwriter      # Run specific example

For more information, visit: https://github.com/dustland/agentx
        """
    )
    
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        metavar="COMMAND"
    )
    
    # Start command (API server)
    start_parser = subparsers.add_parser(
        "start",
        help="Start API server with integrated observability",
        description="Start the AgentX API server with full observability features"
    )
    start_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the server on (default: 8000)"
    )
    start_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)"
    )
    

    
    # Monitor command (merged with web)
    monitor_parser = subparsers.add_parser(
        "monitor",
        help="Start observability monitor (CLI or web interface)",
        description="Start the observability monitor for analysis and debugging"
    )
    monitor_parser.add_argument(
        "--web",
        action="store_true",
        help="Start web interface instead of CLI (default: CLI)"
    )
    monitor_parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Port for web interface (default: 8501, only used with --web)"
    )
    monitor_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for web interface (default: 0.0.0.0, only used with --web)"
    )
    monitor_parser.add_argument(
        "--data-dir",
        help="Path to agentx data directory (default: auto-detect)"
    )
    
    # Status command
    status_parser = subparsers.add_parser(
        "status",
        help="Show system status and health",
        description="Display current status of AgentX components"
    )
    
    # Example command
    example_parser = subparsers.add_parser(
        "example",
        help="Run a specific example",
        description="Run a specific AgentX example by name"
    )
    example_parser.add_argument(
        "name",
        help="Name of the example to run (e.g., superwriter)"
    )
    
    # Version command
    version_parser = subparsers.add_parser(
        "version",
        help="Show version information",
        description="Display AgentX version and component information"
    )
    
    # Config command
    config_parser = subparsers.add_parser(
        "config",
        help="Configuration management",
        description="Manage AgentX configuration"
    )
    config_subparsers = config_parser.add_subparsers(
        dest="config_action",
        help="Configuration actions"
    )
    config_subparsers.add_parser("show", help="Show current configuration")
    config_subparsers.add_parser("init", help="Initialize default configuration")
    
    # Debug command
    debug_parser = subparsers.add_parser(
        "debug",
        help="Start debugging session for a task",
        description="Start interactive debugging session with breakpoints and state inspection"
    )
    debug_parser.add_argument(
        "team_config",
        help="Path to team configuration file"
    )
    debug_parser.add_argument(
        "task_id",
        help="Task ID to debug"
    )
    
    return parser


def show_status():
    """Show system status."""
    print("🤖 AgentX System Status")
    print("=" * 30)
    
    try:
        # Check if observability monitor is available
        from ..observability.monitor import get_monitor
        monitor = get_monitor()
        dashboard_data = monitor.get_dashboard_data()
        
        print(f"📊 Observability: {'🟢 Available' if monitor else '🔴 Unavailable'}")
        print(f"   Mode: {'Integrated' if dashboard_data['is_integrated'] else 'Independent'}")
        print(f"   Running: {'Yes' if dashboard_data['is_running'] else 'No'}")
        print(f"   Tasks: {dashboard_data['total_tasks']}")
        print(f"   Memory Items: {dashboard_data['total_memory_items']}")
        print(f"   Data Directory: {dashboard_data['data_dir']}")
        
    except Exception as e:
        print(f"📊 Observability: 🔴 Error - {e}")
    
    try:
        # Check if server is running
        import requests
        response = requests.get("http://localhost:8000/health", timeout=2)
        print(f"🌐 API Server: {'🟢 Running' if response.status_code == 200 else '🔴 Error'}")
        print(f"   URL: http://localhost:8000")
        print(f"   Start with: agentx start")
    except:
        print("🌐 API Server: 🔴 Not running")
        print("   Start with: agentx start")
    
    try:
        # Check if web dashboard is running
        import requests
        response = requests.get("http://localhost:8501", timeout=2)
        print(f"📱 Web Dashboard: {'🟢 Running' if response.status_code == 200 else '🔴 Error'}")
        print(f"   URL: http://localhost:8501")
        print(f"   Tech: FastAPI + HTMX + TailwindCSS + Preline UI v3.10")
        print(f"   Theme: Professional SaaS dashboard styling")
    except:
        print("📱 Web Dashboard: 🔴 Not running")
        print("   Run 'agentx monitor --web' to start the modern dashboard")
    
    # Check examples
    examples_dir = Path("examples")
    if examples_dir.exists():
        examples = [d.name for d in examples_dir.iterdir() if d.is_dir()]
        print(f"📚 Examples: {len(examples)} available")
        for example in examples[:3]:  # Show first 3
            print(f"   • {example}")
        if len(examples) > 3:
            print(f"   ... and {len(examples) - 3} more")
    else:
        print("📚 Examples: 🔴 Not found")


def show_version():
    """Show version information."""
    print("🤖 AgentX Version Information")
    print("=" * 35)
    
    try:
        # Try to get version from package
        import importlib.metadata
        version = importlib.metadata.version("agentx")
        print(f"Version: {version}")
    except:
        print("Version: Development")
    
    print("Components:")
    
    # Check core components
    try:
        from .. import core
        print("  ✅ Core Framework")
    except:
        print("  ❌ Core Framework")
    
    try:
        from .. import observability
        print("  ✅ Observability System")
    except:
        print("  ❌ Observability System")
    
    try:
        from .. import server
        print("  ✅ API Server")
    except:
        print("  ❌ API Server")
    
    # Check key dependencies
    print("\nKey Dependencies:")
    dependencies = [
        ("fastapi", "FastAPI"),
        ("streamlit", "Streamlit"),
        ("openai", "OpenAI"),
        ("mem0ai", "Mem0"),
        ("pandas", "Pandas"),
        ("plotly", "Plotly")
    ]
    
    for module, name in dependencies:
        try:
            __import__(module)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ❌ {name}")


def show_config():
    """Show current configuration."""
    print("🤖 AgentX Configuration")
    print("=" * 28)
    
    # Check environment variables
    import os
    env_vars = [
        "OPENAI_API_KEY",
        "DEEPSEEK_API_KEY",
        "TAVILY_API_KEY",
        "SERP_API_KEY"
    ]
    
    print("Environment Variables:")
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mask the key for security
            masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            print(f"  ✅ {var}: {masked}")
        else:
            print(f"  ❌ {var}: Not set")
    
    # Check data directory
    print("\nData Storage:")
    data_dir = Path("agentx_data")
    if data_dir.exists():
        files = list(data_dir.glob("*.json"))
        print(f"  📁 Data Directory: {data_dir} ({len(files)} files)")
        for file in files:
            size = file.stat().st_size
            print(f"     • {file.name}: {size} bytes")
    else:
        print(f"  📁 Data Directory: {data_dir} (not created yet)")


def init_config():
    """Initialize default configuration."""
    print("🤖 Initializing AgentX Configuration")
    print("=" * 40)
    
    # Create data directory
    data_dir = Path("agentx_data")
    data_dir.mkdir(exist_ok=True)
    print(f"✅ Created data directory: {data_dir}")
    
    # Create example .env file
    env_file = Path(".env.example")
    if not env_file.exists():
        env_content = """# AgentX Environment Variables
# Copy this file to .env and fill in your API keys

# OpenAI API Key (for GPT models)
OPENAI_API_KEY=your_openai_api_key_here

# DeepSeek API Key (alternative to OpenAI)
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Tavily API Key (for web search)
TAVILY_API_KEY=your_tavily_api_key_here

# SERP API Key (alternative web search)
SERP_API_KEY=your_serp_api_key_here
"""
        env_file.write_text(env_content)
        print(f"✅ Created example environment file: {env_file}")
    
    print("\n📋 Next steps:")
    print("1. Copy .env.example to .env")
    print("2. Fill in your API keys in the .env file")
    print("3. Run 'agentx status' to check configuration")


def main():
    """Main CLI entry point."""
    parser = create_parser()
    
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return 0
    
    args = parser.parse_args()
    
    try:
        if args.command == "start":
            # TODO: Use args.port and args.host when updating start function
            return start()
        

        
        elif args.command == "monitor":
            if args.web:
                return web(
                    project_path=getattr(args, 'project_path', None),
                    host=args.host,
                    port=args.port
                )
            else:
                return monitor(project_path=getattr(args, 'project_path', None))
        
        elif args.command == "status":
            show_status()
            return 0
        
        elif args.command == "example":
            return run_example(args.name)
        
        elif args.command == "version":
            show_version()
            return 0
        
        elif args.command == "config":
            if args.config_action == "show":
                show_config()
            elif args.config_action == "init":
                init_config()
            else:
                print("Available config actions: show, init")
                return 1
            return 0
        
        elif args.command == "debug":
            import asyncio
            from .debug import debug_task
            asyncio.run(debug_task(args.team_config, args.task_id))
            return 0
        
        else:
            parser.print_help()
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled")
        return 130
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 