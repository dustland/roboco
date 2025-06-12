"""
Team Builder Implementation

Implements the configuration-based team creation system as described in the design documents.
Supports Jinja2 template rendering, role definitions, and dynamic team composition.
"""

import os
import yaml
import importlib
from typing import Dict, Any, List, Optional, Type
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from .team_manager import TeamManager
from ..config import create_prompt_loader
from ..config.models import MemoryConfig, EventConfig
from ..core.exceptions import ConfigurationError
from ..memory.manager import MemoryManager
from ..event import InMemoryEventBus


class TeamBuilder:
    """
    Utility for building teams from configuration files using Jinja2 templates.
    Implements the configuration-based design pattern described in the documentation.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the TeamBuilder.
        
        Args:
            config_dir: Base configuration directory. Defaults to './config'
        """
        self.config_dir = Path(config_dir or "./config")
        
        # Look for templates in multiple possible directories
        template_dirs = [
            self.config_dir / "roles",
            self.config_dir / "prompts", 
            self.config_dir / "templates"
        ]
        
        self.template_dir = None
        for template_dir in template_dirs:
            if template_dir.exists():
                self.template_dir = template_dir
                break
        
        # Set up Jinja2 environment for template rendering
        if self.template_dir:
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=False  # We're generating prompts, not HTML
            )
        else:
            self.jinja_env = None
    
    @staticmethod
    def create_team(config_path: Optional[str] = None, 
                   template_variables: Optional[Dict[str, Any]] = None,
                   memory_config: Optional[MemoryConfig] = None,
                   event_config: Optional[EventConfig] = None,
                   event_bus=None) -> TeamManager:
        """
        Create a team from configuration files.
        
        Args:
            config_path: Path to team configuration YAML file. Defaults to './config/team.yaml'
            template_variables: Variables to use in Jinja2 template rendering
            memory_config: Memory system configuration
            event_config: Event system configuration
            event_bus: Optional event bus instance to use
            
        Returns:
            Configured TeamManager instance
        """
        if config_path is None:
            config_path = "./config/team.yaml"
        
        config_dir = Path(config_path).parent
        builder = TeamBuilder(str(config_dir))
        
        return builder.build_team(
            config_path=config_path,
            template_variables=template_variables,
            memory_config=memory_config,
            event_config=event_config,
            event_bus=event_bus
        )
    
    @staticmethod
    def create_team_from_preset(preset_name: str,
                               template_variables: Optional[Dict[str, Any]] = None,
                               **kwargs) -> TeamManager:
        """
        Create a team from a preset configuration.
        
        Args:
            preset_name: Name of the preset (e.g., "research_writing", "planning")
            template_variables: Variables for template rendering
            **kwargs: Additional arguments passed to create_team
            
        Returns:
            Configured TeamManager instance
        """
        # Try to find preset in multiple locations
        preset_paths = [
            f"./config/presets/{preset_name}.yaml",
            f"./examples/{preset_name}/config/team.yaml",
            f"./presets/{preset_name}/team.yaml"
        ]
        
        config_path = None
        for path in preset_paths:
            if Path(path).exists():
                config_path = path
                break
        
        if not config_path:
            raise ConfigurationError(
                f"Preset '{preset_name}' not found. Searched in: {preset_paths}"
            )
        
        return TeamBuilder.create_team(
            config_path=config_path,
            template_variables=template_variables,
            **kwargs
        )
    
    def build_team(self, config_path: str,
                   template_variables: Optional[Dict[str, Any]] = None,
                   memory_config: Optional[MemoryConfig] = None,
                   event_config: Optional[EventConfig] = None,
                   event_bus=None) -> TeamManager:
        """
        Build a team from configuration with template rendering support.
        
        Args:
            config_path: Path to team configuration file
            template_variables: Variables for template rendering
            memory_config: Memory system configuration
            event_config: Event system configuration
            event_bus: Optional event bus instance to use
            
        Returns:
            Configured TeamManager instance
        """
        # Load and process team configuration
        team_config = self._load_team_config(config_path)
        
        # Load role configurations if they exist
        roles_config = self._load_roles_config()
        
        # Create enhanced team configuration with rendered templates
        enhanced_config = self._create_enhanced_config(
            team_config=team_config,
            roles_config=roles_config,
            template_variables=template_variables or {}
        )
        
        # Save the enhanced config to a temporary file
        temp_config_path = self._save_temp_config(enhanced_config)
        
        # Initialize system components
        memory_manager = None
        
        # Use provided event_bus or create from config
        if event_bus is None:
            event_bus = None  # Will be set below based on config
        
        # Handle memory configuration from team config or provided config
        if memory_config:
            memory_manager = MemoryManager(memory_config)
        elif "memory" in enhanced_config:
            # Create MemoryConfig from team configuration
            try:
                team_memory_config = enhanced_config["memory"]
                memory_config = MemoryConfig(
                    vector_store=team_memory_config.get("vector_store"),
                    llm=team_memory_config.get("llm"),
                    embedder=team_memory_config.get("embedder"),
                    graph_store=team_memory_config.get("graph_store"),
                    version=team_memory_config.get("version", "v1.1"),
                    custom_fact_extraction_prompt=team_memory_config.get("custom_fact_extraction_prompt"),
                    history_db_path=team_memory_config.get("history_db_path")
                )
                memory_manager = MemoryManager(memory_config)
            except Exception as e:
                print(f"Warning: Could not initialize memory system from team config: {e}")
        
        # Only create event_bus if not provided
        if event_bus is None:
            if event_config:
                if event_config.bus_type == "memory":
                    event_bus = InMemoryEventBus()
            elif "events" in enhanced_config and enhanced_config["events"].get("bus_type") == "memory":
                event_bus = InMemoryEventBus()
        
        # Create TeamManager with the enhanced configuration
        team_manager = TeamManager(
            config_path=temp_config_path,
            event_bus=event_bus
        )
        
        # Attach memory manager if provided
        if memory_manager:
            team_manager.memory_manager = memory_manager
        
        return team_manager
    
    def _load_team_config(self, config_path: str) -> Dict[str, Any]:
        """Load team configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise ConfigurationError(f"Team configuration file not found: {config_path}")
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Error parsing team configuration: {e}")
    
    def _load_roles_config(self) -> Optional[Dict[str, Any]]:
        """Load roles configuration if it exists."""
        roles_config_path = self.config_dir / "roles.yaml"
        
        if not roles_config_path.exists():
            return None
        
        try:
            with open(roles_config_path, 'r') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Error parsing roles configuration: {e}")
    
    def _create_enhanced_config(self, team_config: Dict[str, Any],
                               roles_config: Optional[Dict[str, Any]],
                               template_variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create enhanced team configuration with rendered templates.
        
        Args:
            team_config: Base team configuration
            roles_config: Role-specific configurations
            template_variables: Variables for template rendering
            
        Returns:
            Enhanced configuration with rendered prompts
        """
        enhanced_config = team_config.copy()
        
        # Process agents and render their prompts
        if "agents" in enhanced_config:
            enhanced_agents = []
            
            for agent_config in enhanced_config["agents"]:
                enhanced_agent = agent_config.copy()
                
                # Get role-specific configuration if available
                agent_name = agent_config.get("name", "")
                role_config = None
                
                if roles_config and "roles" in roles_config:
                    role_config = roles_config["roles"].get(agent_name)
                
                # Render the agent's prompt template
                if role_config and "template_file" in role_config:
                    if not self.jinja_env:
                        print(f"Warning: Template directory not found. Searched in: "
                              f"{[str(d) for d in [self.config_dir / 'roles', self.config_dir / 'prompts', self.config_dir / 'templates']]}. "
                              f"Skipping template rendering for {agent_name}.")
                    else:
                        # Merge template variables
                        merged_variables = template_variables.copy()
                        if "template_variables" in role_config:
                            merged_variables.update(role_config["template_variables"])
                        
                        # Add global context variables
                        merged_variables.update({
                            "agent_name": agent_name,
                            "team_name": team_config.get("name", "UnnamedTeam"),
                            "workspace_path": os.getcwd(),
                            "config_dir": str(self.config_dir)
                        })
                        
                        # Render the template
                        system_message = self._render_template(
                            role_config["template_file"],
                            merged_variables
                        )
                        
                        enhanced_agent["system_message"] = system_message
                    
                    # Apply role-specific LLM configuration
                    if "temperature" in role_config:
                        if "llm_config" not in enhanced_agent:
                            enhanced_agent["llm_config"] = {"config_list": [{}]}
                        enhanced_agent["llm_config"]["temperature"] = role_config["temperature"]
                    
                    if "max_tokens" in role_config:
                        if "llm_config" not in enhanced_agent:
                            enhanced_agent["llm_config"] = {"config_list": [{}]}
                        enhanced_agent["llm_config"]["max_tokens"] = role_config["max_tokens"]
                
                enhanced_agents.append(enhanced_agent)
            
            enhanced_config["agents"] = enhanced_agents
        
        return enhanced_config
    
    def _render_template(self, template_file: str, variables: Dict[str, Any]) -> str:
        """
        Render a Jinja2 template with the provided variables.
        
        Args:
            template_file: Template file name
            variables: Variables for rendering
            
        Returns:
            Rendered template content
        """
        if not self.jinja_env:
            return f"# Template rendering not available\nRole: {template_file.replace('.md', '')}\nTemplate file: {template_file}"
        
        try:
            template = self.jinja_env.get_template(template_file)
            return template.render(**variables)
        except TemplateNotFound:
            raise ConfigurationError(
                f"Template file not found: {template_file} in {self.template_dir}"
            )
        except Exception as e:
            raise ConfigurationError(
                f"Error rendering template {template_file}: {e}"
            )
    
    def _save_temp_config(self, config: Dict[str, Any]) -> str:
        """
        Save enhanced configuration to a temporary file.
        
        Args:
            config: Configuration to save
            
        Returns:
            Path to the temporary configuration file
        """
        import tempfile
        
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.yaml',
            delete=False,
            prefix='roboco_team_'
        )
        
        try:
            yaml.dump(config, temp_file, default_flow_style=False)
            temp_file.flush()
            return temp_file.name
        finally:
            temp_file.close()


# Convenience functions for preset teams
def create_planning_team(template_variables: Optional[Dict[str, Any]] = None,
                        **kwargs) -> TeamManager:
    """Create a planning-focused team."""
    return TeamBuilder.create_team_from_preset(
        "planning",
        template_variables=template_variables,
        **kwargs
    )


def create_research_writing_team(template_variables: Optional[Dict[str, Any]] = None,
                                **kwargs) -> TeamManager:
    """Create a research and writing team.""" 
    return TeamBuilder.create_team_from_preset(
        "research_writing",
        template_variables=template_variables,
        **kwargs
    )


def create_software_development_team(template_variables: Optional[Dict[str, Any]] = None,
                                   **kwargs) -> TeamManager:
    """Create a software development team."""
    return TeamBuilder.create_team_from_preset(
        "software_development", 
        template_variables=template_variables,
        **kwargs
    ) 