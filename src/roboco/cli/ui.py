"""
CLI command to start the RoboCo UI application.

This module provides a command-line interface for starting the RoboCo Streamlit UI.
"""

import sys
import os
import subprocess
from typing import Optional, List

def launch_ui(
    host: str = "127.0.0.1", 
    port: int = 8501,
    server_host: str = "127.0.0.1",
    server_port: int = 8000,
) -> int:
    """
    Start the RoboCo Streamlit UI.
    
    Args:
        host: The host to bind the Streamlit server to
        port: The port to bind the Streamlit server to
        server_host: The host of the RoboCo API server
        server_port: The port of the RoboCo API server
        
    Returns:
        Exit code
    """
    try:
        # Set environment variables for the Streamlit app to connect to the API
        os.environ["HOST"] = server_host
        os.environ["PORT"] = str(server_port)
        
        print(f"Starting RoboCo UI on http://{host}:{port}")
        print(f"Connecting to RoboCo API at http://{server_host}:{server_port}")
        print("Press Ctrl+C to stop")
        
        # Recommend using multiple workers
        print("\n⚠️ IMPORTANT: Make sure your API server is running with multiple workers:")
        print(f"    roboco server --host {server_host} --port {server_port} --workers 4")
        print("This prevents the server from becoming unresponsive during chat operations.\n")
        
        # Construct the Streamlit command
        streamlit_cmd = [
            "streamlit", "run", 
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui", "app.py"),
            "--server.address", host,
            "--server.port", str(port),
        ]
        
        # Start the Streamlit server
        process = subprocess.run(streamlit_cmd)
        return process.returncode
    except Exception as e:
        print(f"Error starting UI: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(launch_ui()) 