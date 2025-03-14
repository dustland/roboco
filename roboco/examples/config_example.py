"""
Configuration System Example

This example demonstrates how to use the Roboco configuration system.
"""

import os
from pathlib import Path
from loguru import logger

# Import the configuration module
from roboco.config import config, ConfigurationError

def run_config_example():
    """Run the configuration system example."""
    print("\n" + "=" * 80)
    print(" Roboco Configuration System Example")
    print("=" * 80)
    
    # Try to load the configuration
    try:
        config.load()
        print(f"Configuration loaded from: {config.config_path}")
    except ConfigurationError as e:
        print(f"Error loading configuration: {e}")
        print("Please run 'python configure.py' to create a configuration file.")
        return
    
    # Display core settings
    print("\nCore Settings:")
    print(f"  Workspace Base: {config.get('core.workspace_base')}")
    print(f"  Debug Mode: {config.get('core.debug')}")
    print(f"  Research Output Directory: {config.get('core.research_output_dir')}")
    
    # Display LLM settings
    print("\nLLM Settings:")
    llm_config = config.get_section('llm')
    print(f"  Model: {llm_config.get('model')}")
    print(f"  Base URL: {llm_config.get('base_url')}")
    print(f"  Max Tokens: {llm_config.get('max_tokens')}")
    print(f"  Temperature: {llm_config.get('temperature')}")
    
    # Display agent settings
    print("\nAgent Settings:")
    for agent_type in ['research_team', 'robot_brain_team', 'embodied_app_team']:
        agent_config = config.get(f'agents.{agent_type}')
        if agent_config:
            print(f"  {agent_type.replace('_', ' ').title()}:")
            print(f"    Enabled: {agent_config.get('enabled')}")
            print(f"    LLM: {agent_config.get('llm')}")
    
    # Display tool settings
    print("\nTool Settings:")
    for tool_type in ['embodied', 'web_research', 'terminal']:
        tool_config = config.get(f'tools.{tool_type}')
        if tool_config:
            print(f"  {tool_type.replace('_', ' ').title()}:")
            print(f"    Enabled: {tool_config.get('enabled')}")
    
    # Example of accessing a specific configuration value with a default
    max_results = config.get('tools.web_research.max_results', 3)
    print(f"\nWeb Research Max Results: {max_results}")
    
    # Example of environment variable interpolation
    api_key = config.get('llm.api_key')
    if api_key and api_key.startswith('${') and api_key.endswith('}'):
        print("\nAPI Key is using environment variable interpolation.")
        env_var = api_key[2:-1]
        print(f"  Environment Variable: {env_var}")
        print(f"  Value Set: {'Yes' if os.environ.get(env_var) else 'No'}")
    
    print("\n" + "=" * 80)
    print(" Example Complete")
    print("=" * 80)

if __name__ == "__main__":
    run_config_example() 