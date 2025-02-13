"""CLI for running the RoboCo service."""

import click
import uvicorn
from dotenv import load_dotenv
import os

@click.group()
def cli():
    """RoboCo CLI tools."""
    pass

@cli.command()
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', default=8000, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
def serve(host: str, port: int, reload: bool):
    """Run the RoboCo backend service."""
    # Load environment variables
    load_dotenv()
    
    # Configure uvicorn
    uvicorn.run(
        "roboco.service:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

def main():
    """Main entry point."""
    cli() 