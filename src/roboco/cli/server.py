"""
CLI command to start the RoboCo API server.

This module provides a command-line interface for starting the RoboCo API server.
"""

import sys
import uvicorn
from typing import Optional, Dict, Any

def main(
    host: str = "127.0.0.1", 
    port: int = 8000,
    reload: bool = False,
    workers: int = 4
) -> int:
    """
    Start the RoboCo API server.
    
    Args:
        host: The host to bind to
        port: The port to bind to
        reload: Whether to enable auto-reload on code changes
        workers: Number of worker processes
        
    Returns:
        Exit code
    """
    try:
        print(f"Starting RoboCo API server on http://{host}:{port}")
        
        # Effective worker count based on reload mode
        effective_workers = 1 if reload else workers
        
        if reload and workers > 1:
            print("\n⚠️ Warning: In reload mode, only a single worker can be used.")
            print("   To use multiple workers, disable reload mode.")
            print(f"   Proceeding with 1 worker instead of requested {workers}.\n")
        else:
            print(f"Using {effective_workers} worker{'s' if effective_workers > 1 else ''}")
        
        print("Press Ctrl+C to stop")
        
        # Configure Uvicorn options
        config: Dict[str, Any] = {
            "app": "roboco.api.server:app",
            "host": host,
            "port": port,
            "reload": reload,
            "workers": effective_workers,
            "log_level": "info",
        }
        
        # Start the server
        uvicorn.run(**config)
        return 0
    except Exception as e:
        print(f"Error starting server: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 