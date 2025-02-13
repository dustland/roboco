"""Command to serve the RoboCo API."""

import click
import uvicorn
from loguru import logger

from roboco.core.logging import setup_logging

@click.command()
@click.option(
    "--host",
    default="127.0.0.1",
    help="Host to bind the service to"
)
@click.option(
    "--port",
    default=8000,
    help="Port to bind the service to"
)
@click.option(
    "--reload",
    is_flag=True,
    help="Enable auto-reload for development"
)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(["debug", "info", "warning", "error", "critical"]),
    help="Logging level"
)
def serve(host: str, port: int, reload: bool, log_level: str):
    """Start the RoboCo API server."""
    try:
        # Configure logging
        setup_logging(log_level=log_level.upper())
        logger.info(f"Starting RoboCo service on {host}:{port}")
        
        # Start uvicorn server
        uvicorn.run(
            "roboco.api.app:app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level
        )
    except Exception as e:
        logger.error(f"Failed to start service: {str(e)}")
        raise click.ClickException(str(e)) 