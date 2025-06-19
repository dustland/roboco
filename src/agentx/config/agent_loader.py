"""
Agent configuration loading with tool validation and discovery.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# AgentConfig imported locally to avoid circular imports
from ..tool.registry import validate_agent_tools, suggest_tools_for_agent, list_tools
from .models import ConfigurationError
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AgentConfigFile:
    """Agent configuration loaded from YAML file."""
    name: str
    role: str = "assistant"
    system_message: Optional[str] = None
    description: str = ""
    prompt_file: Optional[str] = None
    tools: List[str] = None
    enable_code_execution: bool = False
    enable_human_interaction: bool = False
    enable_memory: bool = True
    max_consecutive_replies: int = 10
    auto_reply: bool = True
    
    def __post_init__(self):
        if self.tools is None:
            self.tools = []


def load_agents_config(config_path: str, validate_tools: bool = True) -> List[tuple[Any, List[str]]]:
    """
    Load multiple agent configurations from YAML file with tool validation.
    
    Args:
        config_path: Path to YAML config file
        validate_tools: Whether to validate tool names against registry
        
    Returns:
        List of (AgentConfig, tools) tuples
        
    Raises:
        ConfigurationError: If config is invalid or tools are not found
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise ConfigurationError(f"Config file not found: {config_path}")
    
    try:
        with open(config_file, 'r') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML in {config_path}: {e}")
    
    # Handle both single agent and multiple agents formats
    if 'agents' in data:
        # Multiple agents format: { agents: [...] }
        agents_data = data['agents']
    elif 'name' in data:
        # Single agent format: { name: ..., role: ... }
        agents_data = [data]
    else:
        raise ConfigurationError(f"Invalid config format. Expected 'agents' list or single agent config")
    
    results = []
    for i, agent_data in enumerate(agents_data):
        try:
            config_data = AgentConfigFile(**agent_data)
        except TypeError as e:
            raise ConfigurationError(f"Invalid agent config structure at index {i}: {e}")
        
        # Validate tools if requested
        if validate_tools and config_data.tools:
            valid_tools, invalid_tools = validate_agent_tools(config_data.tools)
            
            if invalid_tools:
                available_tools = list_tools()
                error_msg = f"Invalid tools for agent '{config_data.name}': {invalid_tools}\n"
                error_msg += f"Available tools: {available_tools}\n"
                error_msg += f"Run 'agentx tools list' for detailed descriptions"
                
                # Suggest alternatives
                suggestions = suggest_tools_for_agent(config_data.name, config_data.description)
                if suggestions:
                    error_msg += f"\nSuggested tools for '{config_data.name}': {suggestions}"
                
                raise ConfigurationError(error_msg)
            
            logger.info(f"Validated tools for {config_data.name}: {valid_tools}")
        
        # Convert to AgentConfig
        from .models import AgentConfig
        
        # Handle prompt_template - use prompt_file if available, otherwise create from system_message
        prompt_template = config_data.prompt_file
        if not prompt_template and config_data.system_message:
            # For backward compatibility, create a simple template from system_message
            prompt_template = config_data.system_message
        elif not prompt_template:
            # Default template if neither is provided
            prompt_template = f"You are a helpful AI assistant named {config_data.name}."
        
        agent_config = AgentConfig(
            name=config_data.name,
            description=config_data.description or f"AI assistant named {config_data.name}",
            prompt_template=prompt_template,
            tools=config_data.tools
        )
        
        results.append((agent_config, config_data.tools))
    
    return results


def load_single_agent_config(config_path: str, agent_name: Optional[str] = None, 
                           validate_tools: bool = True) -> tuple[Any, List[str]]:
    """
    Load a single agent configuration from YAML file.
    
    Args:
        config_path: Path to YAML config file
        agent_name: Specific agent name to load (if file contains multiple agents)
        validate_tools: Whether to validate tool names against registry
        
    Returns:
        Tuple of (AgentConfig, tools)
        
    Raises:
        ConfigurationError: If config is invalid or agent not found
    """
    agents = load_agents_config(config_path, validate_tools)
    
    if agent_name:
        # Find specific agent
        for agent_config, tools in agents:
            if agent_config.name == agent_name:
                return agent_config, tools
        raise ConfigurationError(f"Agent '{agent_name}' not found in {config_path}")
    else:
        # Return first agent if no name specified
        if not agents:
            raise ConfigurationError(f"No agents found in {config_path}")
        return agents[0]


def create_team_config_template(team_name: str, agent_names: List[str], 
                               output_path: str, include_suggestions: bool = True) -> str:
    """
    Create a YAML config template for a team with multiple agents.
    
    Args:
        team_name: Name of the team
        agent_names: List of agent names to include
        output_path: Where to save the template
        include_suggestions: Whether to include suggested tools
        
    Returns:
        Path to created template file
    """
    available_tools = list_tools()
    
    template = f"""# Team Configuration: {team_name}
# Multiple agents working together

agents:"""
    
    for agent_name in agent_names:
        suggestions = suggest_tools_for_agent(agent_name) if include_suggestions else []
        
        template += f"""
  - name: {agent_name}
    role: assistant  # assistant, user, or system
    # Either specify system_message OR prompt_file (not both)
    # system_message: "You are a helpful AI assistant named {agent_name}."
    prompt_file: "prompts/{agent_name}.md"  # Load system message from file
    description: "Describe what this agent does..."
    
    # Tools this agent can use
    tools:"""
        
        if suggestions:
            template += "\n      # Suggested tools based on agent name:"
            for tool in suggestions:
                template += f"\n      - {tool}"
        else:
            template += "\n      # Add tool names here, e.g.:"
            if available_tools:
                for tool in available_tools[:2]:  # Show first 2 as examples
                    template += f"\n      # - {tool}"
        
        template += """
    
    # Optional settings
    enable_code_execution: false
    enable_human_interaction: false  
    enable_memory: true
    max_consecutive_replies: 10
    auto_reply: true"""
    
    template += f"""

# Available tools: {available_tools}
# Run 'agentx tools list' for detailed descriptions

# Team settings (optional)
team:
  name: {team_name}
  max_rounds: 10
  speaker_selection: "auto"  # auto, round_robin, manual
"""
    
    # Write template
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write(template)
    
    logger.info(f"Created team config template: {output_path}")
    return str(output_file)


def create_single_agent_template(agent_name: str, output_path: str, 
                                include_suggestions: bool = True) -> str:
    """
    Create a YAML config template for a single agent.
    
    Args:
        agent_name: Name of the agent
        output_path: Where to save the template
        include_suggestions: Whether to include suggested tools
        
    Returns:
        Path to created template file
    """
    # Get tool suggestions
    suggestions = suggest_tools_for_agent(agent_name) if include_suggestions else []
    available_tools = list_tools()
    
    template = f"""# Single Agent Configuration: {agent_name}
name: {agent_name}
role: assistant  # assistant, user, or system
# Either specify system_message OR prompt_file (not both)
# system_message: "You are a helpful AI assistant named {agent_name}."
prompt_file: "prompts/{agent_name}.md"  # Load system message from file
description: "Describe what this agent does..."

# Tools this agent can use
tools:"""
    
    if suggestions:
        template += "\n  # Suggested tools based on agent name:"
        for tool in suggestions:
            template += f"\n  - {tool}"
    else:
        template += "\n  # Add tool names here, e.g.:"
        if available_tools:
            for tool in available_tools[:3]:  # Show first 3 as examples
                template += f"\n  # - {tool}"
    
    template += f"""

# Optional settings
enable_code_execution: false
enable_human_interaction: false  
enable_memory: true
max_consecutive_replies: 10
auto_reply: true

# Available tools: {available_tools}
# Run 'agentx tools list' for detailed descriptions
"""
    
    # Write template
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write(template)
    
    logger.info(f"Created single agent config template: {output_path}")
    return str(output_file)


def validate_config_file(config_path: str) -> Dict[str, Any]:
    """
    Validate a config file (single agent or team) and return validation results.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Dictionary with validation results
    """
    try:
        agents = load_agents_config(config_path, validate_tools=True)
        agent_names = [config.name for config, _ in agents]
        all_tools = []
        for _, tools in agents:
            all_tools.extend(tools)
        
        return {
            "valid": True,
            "agents": agent_names,
            "total_agents": len(agents),
            "tools_used": list(set(all_tools)),
            "message": f"Configuration is valid ({len(agents)} agents)"
        }
    except ConfigurationError as e:
        return {
            "valid": False,
            "error": str(e),
            "message": "Configuration validation failed"
        } 