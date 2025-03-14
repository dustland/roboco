#!/usr/bin/env python
"""
Roboco Configuration Utility

This script helps users create a configuration file for the Roboco system.
It prompts for necessary configuration values and generates a config.toml file.
"""

import os
import shutil
from pathlib import Path
import re
import sys
from typing import Dict, Any, Optional

def print_header(text: str) -> None:
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f" {text}")
    print("=" * 80)

def prompt(message: str, default: Optional[str] = None) -> str:
    """
    Prompt the user for input with an optional default value.
    
    Args:
        message: The prompt message
        default: Default value if the user enters nothing
        
    Returns:
        The user's input or the default value
    """
    if default:
        result = input(f"{message} [{default}]: ").strip()
        return result if result else default
    else:
        return input(f"{message}: ").strip()

def prompt_bool(message: str, default: bool = False) -> bool:
    """
    Prompt the user for a yes/no response.
    
    Args:
        message: The prompt message
        default: Default value if the user enters nothing
        
    Returns:
        True for yes, False for no
    """
    default_str = "Y/n" if default else "y/N"
    result = input(f"{message} [{default_str}]: ").strip().lower()
    
    if not result:
        return default
    
    return result.startswith('y')

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
    
    # Check if config.example.toml exists
    example_config_path = Path("config/config.example.toml")
    if not example_config_path.exists():
        example_config_path = Path("./config.example.toml")
        if not example_config_path.exists():
            print("Error: config.example.toml not found. Please run this script from the project root directory.")
            sys.exit(1)
    
    # Determine the output path
    config_dir = Path("config")
    if not config_dir.exists():
        config_dir.mkdir(exist_ok=True)
    
    output_path = config_dir / "config.toml"
    
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
            r'\[llm\].*?model = ".*?"', 
            f'[llm]\n# Model to use\nmodel = "{model}"', 
            config_content, 
            flags=re.DOTALL
        )
        
        if api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key
            
    elif provider_choice == "2":  # OpenAI
        api_key = prompt("Enter your OpenAI API key", os.environ.get("OPENAI_API_KEY", ""))
        model = prompt("Enter the model name", "gpt-4o")
        
        # Update the config content to use OpenAI as default
        config_content = re.sub(
            r'\[llm\].*?base_url = ".*?"', 
            f'[llm]\n# Model to use\nmodel = "{model}"\n# API base URL\nbase_url = "https://api.openai.com/v1"', 
            config_content, 
            flags=re.DOTALL
        )
        
        config_content = re.sub(
            r'\[llm\].*?api_key = ".*?"', 
            f'[llm]\n# Model to use\nmodel = "{model}"\n# API base URL\nbase_url = "https://api.openai.com/v1"\n# Your API key\napi_key = "${{"OPENAI_API_KEY"}}"', 
            config_content, 
            flags=re.DOTALL
        )
        
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            
    elif provider_choice == "3":  # DeepSeek
        api_key = prompt("Enter your DeepSeek API key", os.environ.get("DEEPSEEK_API_KEY", ""))
        model = prompt("Enter the model name", "deepseek-coder")
        
        # Update the config content to use DeepSeek as default
        config_content = re.sub(
            r'\[llm\].*?base_url = ".*?"', 
            f'[llm]\n# Model to use\nmodel = "{model}"\n# API base URL\nbase_url = "https://api.deepseek.com/v1"', 
            config_content, 
            flags=re.DOTALL
        )
        
        config_content = re.sub(
            r'\[llm\].*?api_key = ".*?"', 
            f'[llm]\n# Model to use\nmodel = "{model}"\n# API base URL\nbase_url = "https://api.deepseek.com/v1"\n# Your API key\napi_key = "${{"DEEPSEEK_API_KEY"}}"', 
            config_content, 
            flags=re.DOTALL
        )
        
        if api_key:
            os.environ["DEEPSEEK_API_KEY"] = api_key
            
    elif provider_choice == "4":  # Ollama
        model = prompt("Enter the Ollama model name", "llama3")
        
        # Update the config content to use Ollama as default
        config_content = re.sub(
            r'\[llm\].*?base_url = ".*?"', 
            f'[llm]\n# Model to use\nmodel = "{model}"\n# API base URL\nbase_url = "http://localhost:11434/v1"', 
            config_content, 
            flags=re.DOTALL
        )
        
        config_content = re.sub(
            r'\[llm\].*?api_key = ".*?"', 
            f'[llm]\n# Model to use\nmodel = "{model}"\n# API base URL\nbase_url = "http://localhost:11434/v1"\n# Your API key\napi_key = "ollama"', 
            config_content, 
            flags=re.DOTALL
        )
    
    # Configure directories
    print_header("Directory Configuration")
    
    workspace_dir = prompt("Enter the workspace directory path", "./workspace")
    research_output_dir = prompt("Enter the research output directory path", "./research_output")
    
    # Update directory paths in the config
    config_content = re.sub(
        r'workspace_base = ".*?"', 
        f'workspace_base = "{workspace_dir}"', 
        config_content
    )
    
    config_content = re.sub(
        r'research_output_dir = ".*?"', 
        f'research_output_dir = "{research_output_dir}"', 
        config_content
    )
    
    # Configure UI settings
    print_header("UI Configuration")
    
    enable_ui = prompt_bool("Enable the web UI?", False)
    
    # Update UI settings in the config
    config_content = re.sub(
        r'enabled = (true|false)', 
        f'enabled = {"true" if enable_ui else "false"}', 
        config_content
    )
    
    if enable_ui:
        ui_port = prompt("Enter the UI port", "8000")
        config_content = re.sub(
            r'port = \d+', 
            f'port = {ui_port}', 
            config_content
        )
    
    # Write the configuration file
    with open(output_path, "w") as f:
        f.write(config_content)
    
    print_header("Configuration Complete")
    print(f"Configuration file has been written to {output_path}")
    print("You can edit this file directly to make further changes.")
    print("To use the configuration, run your Roboco commands from the project root directory.")

if __name__ == "__main__":
    main() 