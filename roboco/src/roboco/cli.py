"""RoboCo CLI interface."""

import os
import sys
from pathlib import Path
import click
from loguru import logger
import uvicorn

from .config import load_config, RoboCoConfig
from . import __version__

# Configure logging
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/roboco_cli.log",
    rotation="100 MB",
    retention="7 days",
    level="DEBUG"
)

@click.group()
@click.version_option(version=__version__)
def cli():
    """RoboCo - Multi-Agent System for Humanoid Robot Development."""
    pass

@cli.command()
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
    "--config",
    type=click.Path(exists=True),
    help="Path to configuration file"
)
@click.option(
    "--reload",
    is_flag=True,
    help="Enable auto-reload for development"
)
def serve(host: str, port: int, config: str, reload: bool):
    """Start the RoboCo backend service."""
    try:
        if config:
            logger.info(f"Loading configuration from {config}")
            load_config(config)
        
        logger.info(f"Starting RoboCo service on {host}:{port}")
        uvicorn.run(
            "roboco.service:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start service: {str(e)}")
        sys.exit(1)

@cli.command()
@click.option(
    "--config",
    type=click.Path(exists=True),
    help="Path to configuration file"
)
def validate(config: str):
    """Validate configuration file."""
    try:
        if not config:
            logger.error("No configuration file specified")
            sys.exit(1)
            
        logger.info(f"Validating configuration file: {config}")
        config_obj = load_config(config)
        logger.info("Configuration file is valid")
        
        # Print configuration details
        click.echo("\nConfiguration Summary:")
        for agent_name, agent_config in config_obj.dict().items():
            click.echo(f"\n{agent_name}:")
            click.echo(f"  Model: {agent_config['llm']['model']}")
            click.echo(f"  Temperature: {agent_config['llm']['temperature']}")
            if agent_config['additional_config']:
                click.echo("  Additional Config:")
                for k, v in agent_config['additional_config'].items():
                    click.echo(f"    {k}: {v}")
                    
    except Exception as e:
        logger.error(f"Configuration validation failed: {str(e)}")
        sys.exit(1)

def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 