"""
RoboCo CLI Commands

This package provides command-line interface tools for RoboCo.
"""

import argparse
import sys
from typing import List, Optional

def cli(args: Optional[List[str]] = None) -> int:
    """Main entry point for roboco CLI."""
    if args is None:
        args = sys.argv[1:]
        
    parser = argparse.ArgumentParser(description="RoboCo Command Line Interface")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Start the RoboCo API server")
    server_parser.add_argument("--host", default="127.0.0.1", help="Host to bind the server to")
    server_parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    server_parser.add_argument("--reload", action="store_true", help="Enable auto-reload on code changes")
    server_parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    
    # Parse args
    parsed_args = parser.parse_args(args)
    
    if parsed_args.command == "server":
        from roboco.cli.server import main as server_main
        return server_main(
            host=parsed_args.host,
            port=parsed_args.port,
            reload=parsed_args.reload,
            workers=parsed_args.workers
        )
    else:
        parser.print_help()
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(cli())
