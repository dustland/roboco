"""
Prompt loading and templating system for Roboco.
Handles loading prompts from markdown files with Jinja2 variable substitution.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import re

try:
    from jinja2 import Template, Environment, FileSystemLoader, TemplateNotFound
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False

from roboco.core.exceptions import ConfigurationError


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
        if not HAS_JINJA2:
            raise ConfigurationError("Jinja2 is required for prompt templating. Install with: pip install jinja2")
        
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
    
    def validate_prompt_variables(self, prompt_file: str, variables: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate that all required variables are provided for a prompt.
        Note: This is a basic validation for Jinja2 templates.
        
        Args:
            prompt_file: Name of the prompt file
            variables: Dictionary of provided variables
            
        Returns:
            Tuple of (is_valid, missing_variables)
        """
        try:
            template = self.jinja_env.get_template(prompt_file)
            
            # Get template source to find variables
            source = template.source
            
            # Use regex to find Jinja2 variables (basic detection)
            pattern = r'\{\{\s*([^}|\s]+)(?:\s*\|[^}]*)?\s*\}\}'
            required_vars = set()
            
            for match in re.finditer(pattern, source):
                var_name = match.group(1).strip()
                # Skip Jinja2 built-ins and filters
                if '.' not in var_name and not var_name.startswith('_'):
                    required_vars.add(var_name)
            
            provided_vars = set(variables.keys())
            missing_vars = list(required_vars - provided_vars)
            
            return len(missing_vars) == 0, missing_vars
            
        except TemplateNotFound:
            return False, [f"Prompt file not found: {prompt_file}"]
        except Exception as e:
            return False, [f"Error validating prompt file {prompt_file}: {e}"]
    
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