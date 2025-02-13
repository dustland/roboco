"""Command to validate RoboCo configuration."""

import click
from loguru import logger

from roboco.core.config import load_config

@click.command()
@click.option(
    "--config",
    type=click.Path(exists=True),
    help="Path to configuration file"
)
def validate(config: str):
    """Validate RoboCo configuration file."""
    try:
        if not config:
            raise click.UsageError("No configuration file specified")
            
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
        raise click.ClickException(str(e)) 