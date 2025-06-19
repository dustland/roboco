"""
Team configuration loading system.
Implements the load_team_config function from the design document.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from pydantic import BaseModel, Field


from .agent_loader import load_agents_config
from .prompt_loader import PromptLoader, create_prompt_loader
from .models import ConfigurationError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class LLMProviderConfig(BaseModel):
    """Simple LLM provider configuration for team loading."""
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None


class TeamConfig(BaseModel):
    """Simple team configuration for YAML loading."""
    name: str
    description: Optional[str] = None
    llm_provider: Optional[LLMProviderConfig] = None
    agents: List[Dict[str, Any]]  # Raw agent data from YAML
    speaker_selection_method: str = "auto"
    max_rounds: int = 10
    termination_condition: str = "TERMINATE"
    timeout_minutes: Optional[int] = None
    auto_terminate_keywords: Optional[List[str]] = None
    speaker_order: Optional[List[str]] = None
    tools: Optional[Dict[str, Any]] = None
    memory: Optional[Dict[str, Any]] = None  # Simple dict for YAML
    execution: Optional[Dict[str, Any]] = None
    orchestrator: Optional[Dict[str, Any]] = None


class TeamLoader:
    """
    Loads team configurations from YAML files with prompt files.
    Implements the design document's vision of team loading.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize team loader.
        
        Args:
            config_dir: Directory containing team.yaml and prompts/ folder
        """
        self.config_dir = Path(config_dir) if config_dir else Path.cwd()
        self.prompt_loader = None
        
        # Try to initialize prompt loader if prompts directory exists
        prompts_dir = self.config_dir / "prompts"
        if prompts_dir.exists():
            try:
                self.prompt_loader = PromptLoader(str(prompts_dir))
            except Exception as e:
                logger.warning(f"Could not initialize prompt loader: {e}")
    
    def load_team_config(self, config_path: str) -> TeamConfig:
        """
        Load team configuration from YAML file.
        
        Args:
            config_path: Path to team.yaml file
            
        Returns:
            TeamConfig object
            
        Raises:
            ConfigurationError: If config is invalid
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise ConfigurationError(f"Team config file not found: {config_path}")
        
        # Load YAML data
        try:
            with open(config_file, 'r') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in {config_path}: {e}")
        
        if not isinstance(data, dict):
            raise ConfigurationError(f"Invalid team config format in {config_path}")
        
        # Set config directory for prompt loading
        self.config_dir = config_file.parent
        prompts_dir = self.config_dir / "prompts"
        if prompts_dir.exists() and not self.prompt_loader:
            self.prompt_loader = PromptLoader(str(prompts_dir))
        
        # Validate required fields
        if 'name' not in data:
            raise ConfigurationError("Team config must have a 'name' field")
        
        if 'agents' not in data or not data['agents']:
            raise ConfigurationError("Team config must have at least one agent")
        
        # Parse team config
        try:
            team_config = TeamConfig(**data)
        except Exception as e:
            raise ConfigurationError(f"Invalid team config structure: {e}")
        
        # Validate agent configurations
        self._validate_agent_configs(team_config.agents, config_file.parent)
        
        return team_config
    
    def create_agents(self, team_config: TeamConfig) -> List[Tuple[Any, List[str]]]:
        """
        Create agent configurations from team config.
        
        Args:
            team_config: Team configuration
            
        Returns:
            List of (AgentConfig, tools) tuples
        """
        # Store team config for access in _create_agent_config
        self.team_config = team_config
        
        results = []
        
        for agent_data in team_config.agents:
            try:
                # Convert agent data to AgentConfig
                agent_config = self._create_agent_config(agent_data)
                tools = agent_data.get('tools', [])
                results.append((agent_config, tools))
            except Exception as e:
                raise ConfigurationError(f"Error creating agent config for {agent_data.get('name', 'unknown')}: {e}")
        
        return results
    
    def create_team_from_config(self, team_config: TeamConfig):
        """
        Create a Team object from team configuration.
        This would integrate with the core Team class.
        
        Args:
            team_config: Team configuration
            
        Returns:
            Team object (placeholder for now)
        """
        # This would create the actual Team object
        # For now, just return the config
        logger.info(f"Creating team '{team_config.name}' with {len(team_config.agents)} agents")
        return team_config
    
    def _create_agent_config(self, agent_data: Dict[str, Any]) -> Any:
        """Create AgentConfig from raw agent data."""
        from .models import AgentConfig, BrainConfig
        
        # Required fields
        name = agent_data.get('name')
        if not name:
            raise ConfigurationError("Agent must have a 'name' field")
        
        # System message - handle prompt_file vs system_message
        prompt_template = None
        prompt_file = agent_data.get('prompt_file')
        
        if prompt_file:
            # Try to initialize prompt loader for this config dir if not already done
            if not self.prompt_loader:
                prompts_dir = self.config_dir / "prompts"
                if prompts_dir.exists():
                    try:
                        self.prompt_loader = PromptLoader(str(prompts_dir))
                    except Exception as e:
                        logger.debug(f"Could not initialize prompt loader: {e}")
            
            # Load from prompt file
            if self.prompt_loader:
                try:
                    # Strip "prompts/" prefix if present since PromptLoader expects just the filename
                    prompt_filename = prompt_file
                    if prompt_filename.startswith("prompts/"):
                        prompt_filename = prompt_filename[8:]  # Remove "prompts/" prefix
                    
                    prompt_template = self.prompt_loader.load_prompt(prompt_filename)
                except Exception as e:
                    logger.warning(f"Could not load prompt file {prompt_file}: {e}")
                    prompt_template = agent_data.get('system_message')
            else:
                # Try to load directly
                prompt_path = self.config_dir / prompt_file
                if prompt_path.exists():
                    try:
                        prompt_template = prompt_path.read_text(encoding='utf-8')
                    except Exception as e:
                        logger.warning(f"Could not read prompt file {prompt_path}: {e}")
        
        if not prompt_template:
            prompt_template = agent_data.get('system_message')
        
        # Ensure we have some prompt template
        if not prompt_template:
            prompt_template = f"You are a helpful AI assistant named {name}."
        
        # Create brain config from agent-level llm_config or team-level llm_provider
        brain_config = None
        
        # First check for agent-level llm_config
        if 'llm_config' in agent_data:
            llm_config = agent_data['llm_config']
            brain_config = BrainConfig(
                provider=llm_config.get('provider', 'deepseek'),
                model=llm_config.get('model', 'deepseek-chat'),
                temperature=llm_config.get('temperature', 0.7),
                max_tokens=llm_config.get('max_tokens', 4000),
                api_key=llm_config.get('api_key'),
                base_url=llm_config.get('base_url'),
                timeout=llm_config.get('timeout', 30),
                supports_function_calls=llm_config.get('supports_function_calls', True)
            )
        # Fallback to team-level llm_provider
        elif hasattr(self, 'team_config') and self.team_config and hasattr(self.team_config, 'llm_provider') and self.team_config.llm_provider:
            llm_provider = self.team_config.llm_provider
            brain_config = BrainConfig(
                model=llm_provider.model or "deepseek-chat",
                api_key=llm_provider.api_key,
                base_url=llm_provider.base_url or "https://api.deepseek.com"
            )
        
        # Create AgentConfig
        agent_config = AgentConfig(
            name=name,
            description=agent_data.get('description', f"AI assistant named {name}"),
            prompt_template=prompt_template,
            brain_config=brain_config,
            tools=agent_data.get('tools', [])
        )
        
        return agent_config
    
    def _validate_agent_configs(self, agents_data: List[Dict[str, Any]], config_dir: Path):
        """Validate agent configurations."""
        agent_names = set()
        
        for agent_data in agents_data:
            # Check for duplicate names
            name = agent_data.get('name')
            if not name:
                raise ConfigurationError("All agents must have a 'name' field")
            
            if name in agent_names:
                raise ConfigurationError(f"Duplicate agent name: {name}")
            agent_names.add(name)
            
            # Check prompt file exists if specified
            prompt_file = agent_data.get('prompt_file')
            if prompt_file:
                prompt_path = config_dir / prompt_file
                if not prompt_path.exists():
                    logger.warning(f"Prompt file not found: {prompt_path}")
                    # Don't fail, just warn - agent will use fallback
        
        logger.info(f"Validated {len(agents_data)} agent configurations")


def load_team_config(config_path: str) -> TeamConfig:
    """
    Load team configuration from YAML file.
    This is the main function shown in the design document.
    
    Args:
        config_path: Path to team.yaml file
        
    Returns:
        TeamConfig object
        
    Example:
        config = load_team_config("research_task/team.yaml")
        team = Team.from_config(config)
    """
    loader = TeamLoader()
    return loader.load_team_config(config_path)


def create_team_from_config(team_config: TeamConfig):
    """
    Create a Team object from team configuration.
    This would be the Team.from_config() method.
    
    Args:
        team_config: Team configuration
        
    Returns:
        Team object
    """
    loader = TeamLoader()
    return loader.create_team_from_config(team_config)


def validate_team_config(config_path: str) -> Dict[str, Any]:
    """
    Validate a team configuration file.
    
    Args:
        config_path: Path to team.yaml file
        
    Returns:
        Dictionary with validation results
    """
    try:
        team_config = load_team_config(config_path)
        loader = TeamLoader()
        agents = loader.create_agents(team_config)
        
        return {
            "valid": True,
            "team_name": team_config.name,
            "agents": [config.name for config, _ in agents],
            "total_agents": len(agents),
            "message": f"Team configuration is valid ({len(agents)} agents)"
        }
    except ConfigurationError as e:
        return {
            "valid": False,
            "error": str(e),
            "message": "Team configuration validation failed"
        }
    except Exception as e:
        return {
            "valid": False,
            "error": f"Unexpected error: {str(e)}",
            "message": "Team configuration validation failed"
        } 