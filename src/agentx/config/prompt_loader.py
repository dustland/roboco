"""
Prompt loading and templating system for AgentX.
Handles loading prompts from markdown files with Jinja2 variable substitution.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import re

from jinja2 import Template, Environment, FileSystemLoader, TemplateNotFound

from .models import ConfigurationError


class PromptLoader:
    """
    Loads and processes prompt templates from markdown files.
    Supports Jinja2 templating with {{ variable_name }} syntax.
    """
    
    def __init__(self, prompts_dir: str):
        """
        Initialize the prompt loader.
        
        Args:
            prompts_dir: Directory containing prompt markdown files
        """
        self.prompts_dir = Path(prompts_dir)
        if not self.prompts_dir.exists():
            raise ConfigurationError(f"Prompts directory does not exist: {prompts_dir}")
        
        # Create Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.prompts_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )
        
        self._prompt_cache: Dict[str, str] = {}
    
    def load_prompt(self, prompt_file: str, variables: Optional[Dict[str, Any]] = None) -> str:
        """
        Load a prompt from a markdown file with Jinja2 variable substitution.
        
        Args:
            prompt_file: Name of the prompt file (e.g., "writer_agent.md")
            variables: Dictionary of variables for substitution
            
        Returns:
            Processed prompt text with variables substituted
            
        Raises:
            ConfigurationError: If prompt file not found or rendering fails
        """
        # Use cache to avoid re-processing files
        cache_key = f"{prompt_file}:{hash(str(sorted((variables or {}).items())))}"
        if cache_key in self._prompt_cache:
            return self._prompt_cache[cache_key]
        
        try:
            template = self.jinja_env.get_template(prompt_file)
        except TemplateNotFound:
            raise ConfigurationError(f"Prompt file not found: {prompt_file}")
        except Exception as e:
            raise ConfigurationError(f"Error loading prompt template {prompt_file}: {e}")
        
        # Render template with variables
        try:
            processed_prompt = template.render(variables or {})
        except Exception as e:
            raise ConfigurationError(f"Error rendering prompt template {prompt_file}: {e}")
        
        # Cache the result
        self._prompt_cache[cache_key] = processed_prompt
        return processed_prompt
    
    def list_available_prompts(self) -> list[str]:
        """
        List all available prompt files in the prompts directory.
        
        Returns:
            List of prompt file names
        """
        return [f.name for f in self.prompts_dir.glob("*.md")]
    
    def clear_cache(self) -> None:
        """Clear the prompt cache."""
        self._prompt_cache.clear()
    
    def get_template_variables(self, prompt_file: str) -> list[str]:
        """
        Extract template variables from a prompt file.
        
        Args:
            prompt_file: Name of the prompt file
            
        Returns:
            List of variable names found in the template
        """
        try:
            # Read the template source directly from file
            template_path = self.prompts_dir / prompt_file
            if not template_path.exists():
                raise ConfigurationError(f"Prompt file not found: {prompt_file}")
            
            template_source = template_path.read_text(encoding='utf-8')
            
            # Parse the template source to find variables
            from jinja2 import meta
            ast = self.jinja_env.parse(template_source)
            return list(meta.find_undeclared_variables(ast))
        except Exception as e:
            raise ConfigurationError(f"Error analyzing template {prompt_file}: {e}")
    
    def validate_template(self, prompt_file: str, variables: Dict[str, Any]) -> bool:
        """
        Validate that a template can be rendered with given variables.
        
        Args:
            prompt_file: Name of the prompt file
            variables: Variables to test with
            
        Returns:
            True if template renders successfully
            
        Raises:
            ConfigurationError: If template validation fails
        """
        try:
            self.load_prompt(prompt_file, variables)
            return True
        except Exception as e:
            raise ConfigurationError(f"Template validation failed for {prompt_file}: {e}")
    
    def render_prompt_with_fallbacks(self, prompt_file: str, variables: Dict[str, Any], 
                                   fallback_values: Optional[Dict[str, Any]] = None) -> str:
        """
        Render a prompt with fallback values for missing variables.
        
        Args:
            prompt_file: Name of the prompt file
            variables: Primary variables dictionary
            fallback_values: Fallback values for missing variables
            
        Returns:
            Rendered prompt text
        """
        # Merge variables with fallbacks
        merged_vars = (fallback_values or {}).copy()
        merged_vars.update(variables)
        
        return self.load_prompt(prompt_file, merged_vars)


def create_prompt_loader(config_dir: str) -> PromptLoader:
    """
    Factory function to create a PromptLoader instance.
    
    Args:
        config_dir: Configuration directory containing prompts/ subdirectory
        
    Returns:
        PromptLoader instance
    """
    prompts_dir = os.path.join(config_dir, "prompts")
    return PromptLoader(prompts_dir) 