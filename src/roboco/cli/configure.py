#!/usr/bin/env python
"""
Configuration Utility

This module provides a command-line utility for creating and managing Roboco configuration files.
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

from roboco.core.config import load_config, get_workspace


def print_header(text: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"{text:^80}")
    print("=" * 80 + "\n")


def prompt(prompt_text: str, default: str = "") -> str:
    """Prompt for user input with a default value."""
    if default:
        user_input = input(f"{prompt_text} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt_text}: ").strip()


def prompt_bool(prompt_text: str, default: bool = False) -> bool:
    """Prompt for a boolean value."""
    while True:
        response = prompt(prompt_text, "Y" if default else "N").lower()
        if response in ["y", "yes", "true", "1"]:
            return True
        if response in ["n", "no", "false", "0"]:
            return False
        print("Please enter Y or N")


def interpolate_env_vars(config_content: str) -> str:
    """
    Replace placeholders with actual environment variables.
    
    Args:
        config_content: The configuration file content
        
    Returns:
        The configuration with environment variables interpolated
    """
    env_var_pattern = re.compile(r'\${([A-Za-z0-9_]+)}')
    
    def replace_env_var(match):
        var_name = match.group(1)
        env_value = os.environ.get(var_name)
        if env_value:
            return env_value
        return match.group(0)  # Keep the placeholder if not found
    
    return env_var_pattern.sub(replace_env_var, config_content)


def main() -> None:
    """Run the configuration utility."""
    print_header("Roboco Configuration Utility")
    print("This utility will help you create a configuration file for the Roboco system.")
    print("Press Enter to accept the default values shown in brackets.")
    
    # Check if config.example.yaml exists
    example_config_path = Path("config/config.example.yaml")
    if not example_config_path.exists():
        example_config_path = Path("./config.example.yaml")
        if not example_config_path.exists():
            print("Error: config.example.yaml not found. Please run this script from the project root directory.")
            sys.exit(1)
    
    # Determine the output path
    config_dir = Path("config")
    if not config_dir.exists():
        config_dir.mkdir(exist_ok=True)
    
    output_path = config_dir / "config.yaml"
    
    if output_path.exists():
        overwrite = prompt_bool(f"Configuration file already exists at {output_path}. Overwrite?", False)
        if not overwrite:
            print("Configuration cancelled. Existing file will not be modified.")
            sys.exit(0)
    
    # Read the example configuration
    with open(example_config_path, "r") as f:
        config_content = f.read()
    
    # Collect configuration values
    print_header("LLM Configuration")
    
    # Determine which LLM provider to use
    print("Which LLM provider would you like to use as the default?")
    print("1. Anthropic (Claude)")
    print("2. OpenAI (GPT)")
    print("3. DeepSeek")
    print("4. Ollama (local)")
    
    provider_choice = prompt("Enter your choice (1-4)", "1")
    
    # Configure the selected provider
    if provider_choice == "1":  # Anthropic
        api_key = prompt("Enter your Anthropic API key", os.environ.get("ANTHROPIC_API_KEY", ""))
        model = prompt("Enter the model name", "claude-3-opus-20240229")
        
        # Update the config content
        config_content = re.sub(
            r'  model: ".*?"', 
            f'  model: "{model}"', 
            config_content
        )
        
        if api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key
            
    elif provider_choice == "2":  # OpenAI
        api_key = prompt("Enter your OpenAI API key", os.environ.get("OPENAI_API_KEY", ""))
        model = prompt("Enter the model name", "gpt-4o")
        
        # Update the config content to use OpenAI as default
        config_content = re.sub(
            r'  model: ".*?"', 
            f'  model: "{model}"', 
            config_content
        )
        
        config_content = re.sub(
            r'  base_url: ".*?"', 
            f'  base_url: "https://api.openai.com/v1"', 
            config_content
        )
        
        config_content = re.sub(
            r'  api_key: ".*?"', 
            f'  api_key: "${{"OPENAI_API_KEY"}}"', 
            config_content
        )
        
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            
    elif provider_choice == "3":  # DeepSeek
        api_key = prompt("Enter your DeepSeek API key", os.environ.get("DEEPSEEK_API_KEY", ""))
        model = prompt("Enter the model name", "deepseek-coder")
        
        # Update the config content to use DeepSeek as default
        config_content = re.sub(
            r'  model: ".*?"', 
            f'  model: "{model}"', 
            config_content
        )
        
        config_content = re.sub(
            r'  base_url: ".*?"', 
            f'  base_url: "https://api.deepseek.com/v1"', 
            config_content
        )
        
        config_content = re.sub(
            r'  api_key: ".*?"', 
            f'  api_key: "${{"DEEPSEEK_API_KEY"}}"', 
            config_content
        )
        
        if api_key:
            os.environ["DEEPSEEK_API_KEY"] = api_key
            
    elif provider_choice == "4":  # Ollama
        model = prompt("Enter the Ollama model name", "llama3")
        
        # Update the config content to use Ollama as default
        config_content = re.sub(
            r'  model: ".*?"', 
            f'  model: "{model}"', 
            config_content
        )
        
        config_content = re.sub(
            r'  base_url: ".*?"', 
            f'  base_url: "http://localhost:11434/v1"', 
            config_content
        )
        
        config_content = re.sub(
            r'  api_key: ".*?"', 
            f'  api_key: "ollama"', 
            config_content
        )
    
    # Configure directories
    print_header("Directory Configuration")
    
    workspace_dir = prompt("Enter the workspace directory path", "./workspace")
    research_output_dir = prompt("Enter the research output directory path", "./research_output")
    cache_dir = prompt("Enter the cache directory path", "./cache")
    
    # Update directory paths in config
    config_content = re.sub(
        r'  workspace_base: ".*?"',
        f'  workspace_base: "{workspace_dir}"',
        config_content
    )
    
    config_content = re.sub(
        r'  research_output_dir: ".*?"',
        f'  research_output_dir: "{research_output_dir}"',
        config_content
    )
    
    config_content = re.sub(
        r'  cache_dir: ".*?"',
        f'  cache_dir: "{cache_dir}"',
        config_content
    )
    
    # Configure UI settings
    print_header("UI Configuration")
    
    ui_enabled = prompt_bool("Enable the web UI?", False)
    ui_port = prompt("Enter the UI port", "8000")
    ui_host = prompt("Enter the UI host", "127.0.0.1")
    ui_theme = prompt("Enter the UI theme (light/dark/system)", "system")
    
    # Update UI settings in config
    config_content = re.sub(
        r'  enabled: .*?',
        f'  enabled: {str(ui_enabled).lower()}',
        config_content
    )
    
    config_content = re.sub(
        r'  port: .*?',
        f'  port: {ui_port}',
        config_content
    )
    
    config_content = re.sub(
        r'  host: ".*?"',
        f'  host: "{ui_host}"',
        config_content
    )
    
    config_content = re.sub(
        r'  theme: ".*?"',
        f'  theme: "{ui_theme}"',
        config_content
    )
    
    # Interpolate environment variables
    config_content = interpolate_env_vars(config_content)
    
    # Write the configuration file
    with open(output_path, "w") as f:
        f.write(config_content)
    
    print(f"\nConfiguration saved to {output_path}")
    print("\nNext steps:")
    print("1. Review the configuration file")
    print("2. Set up your environment variables in a .env file")
    print("3. Run roboco to start using the system")


if __name__ == "__main__":
    main() 