"""Main CLI entry point for RoboCo."""

import click
from loguru import logger

from roboco import __version__
from roboco.core.logging import setup_logging
from .commands.serve import serve
from .commands.validate import validate

@click.group()
@click.version_option(version=__version__)
def cli():
    """RoboCo - Multi-Agent System for Humanoid Robot Development."""
    # Configure basic logging
    setup_logging()

# Add commands
cli.add_command(serve)
cli.add_command(validate)

def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise click.ClickException(str(e))

if __name__ == "__main__":
    main() 