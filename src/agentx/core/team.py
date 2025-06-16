import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from jinja2 import Environment, FileSystemLoader

from .config import TeamConfig, AgentConfig, ToolConfig
from .agent import Agent
from ..utils.logger import get_logger


logger = get_logger(__name__)

class Team:
    """
    Pure agent container and configuration manager.
    
    Responsibilities:
    - Load and validate team configuration
    - Initialize agent instances from configuration
    - Provide access to agents, tools, and collaboration patterns
    - Render agent prompts with context
    - Validate handoff rules
    
    Does NOT handle execution - that's the Orchestrator's job.
    """
    
    def __init__(self, config: TeamConfig, config_dir: Path):
        self.config = config
        self.config_dir = config_dir
        
        # Store both config and active agent instances
        self.agent_configs: Dict[str, AgentConfig] = {agent.name: agent for agent in config.agents}
        self.agents: Dict[str, Agent] = {}
        self.tools: Dict[str, ToolConfig] = {tool.name: tool for tool in config.tools}
        
        # Initialize Jinja environment for prompt rendering
        self._jinja_env = Environment(
            loader=FileSystemLoader(config_dir),
            autoescape=False
        )
        
        # Create agent instances from configurations
        self._initialize_agents()
    
    def _initialize_agents(self) -> None:
        """Initialize Agent instances from AgentConfig objects."""
        self.agents = {}
        
        for agent_config in self.config.agents:
            # Create Agent instance
            agent = Agent(agent_config)
            self.agents[agent_config.name] = agent
            logger.info(f"✅ Initialized agent: {agent_config.name}")
        
        logger.info(f"🎯 Team '{self.config.name}' initialized with {len(self.agents)} agents")
    
    @property
    def name(self) -> str:
        """Team name."""
        return self.config.name
    
    @property
    def max_rounds(self) -> int:
        """Maximum conversation rounds."""
        return self.config.execution.max_rounds
    
    @property
    def handoff_rules(self) -> List[Any]:
        """Handoff rules."""
        return self.config.handoffs
    
    @classmethod
    def from_config(cls, config_path: str | Path) -> "Team":
        """
        Load a team from a YAML configuration file.
        
        Args:
            config_path: Path to the team.yaml file
            
        Returns:
            Team instance with loaded configuration
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML is invalid
            ValidationError: If configuration is invalid
        """
        config_path = Path(config_path)
        config_dir = config_path.parent
        
        if not config_path.exists():
            raise FileNotFoundError(f"Team configuration not found: {config_path}")
        
        # Load and parse YAML
        with open(config_path, 'r', encoding='utf-8') as f:
            raw_config = yaml.safe_load(f)
        
        # Validate and create TeamConfig
        team_config = TeamConfig(**raw_config)
        
        return cls(team_config, config_dir)
    
    def get_agent(self, name: str) -> Optional[Agent]:
        """Get agent instance by name."""
        return self.agents.get(name)
    
    def get_agent_config(self, name: str) -> Optional[AgentConfig]:
        """Get agent configuration by name."""
        return self.agent_configs.get(name)
    
    def get_tool(self, name: str) -> Optional[ToolConfig]:
        """Get tool configuration by name."""
        return self.tools.get(name)
    
    def get_agent_tools(self, agent_name: str) -> List[ToolConfig]:
        """Get all tools available to a specific agent."""
        agent_config = self.get_agent_config(agent_name)
        if not agent_config:
            return []
        
        return [self.tools[tool_name] for tool_name in agent_config.tools if tool_name in self.tools]
    
    def render_agent_prompt(self, agent_name: str, context: Dict[str, Any]) -> str:
        """
        Render an agent's prompt template with the given context.
        
        Args:
            agent_name: Name of the agent
            context: Template context variables
            
        Returns:
            Rendered prompt string
            
        Raises:
            ValueError: If agent not found or template error
        """
        agent_config = self.get_agent_config(agent_name)
        if not agent_config:
            raise ValueError(f"Agent not found: {agent_name}")
        
        try:
            template = self._jinja_env.get_template(agent_config.prompt_template)
            return template.render(**context)
        except Exception as e:
            raise ValueError(f"Error rendering prompt for agent {agent_name}: {e}")
    
    def get_handoff_targets(self, from_agent: str) -> List[str]:
        """Get possible handoff targets for an agent."""
        targets = []
        for rule in self.config.handoffs:
            if rule.from_agent == from_agent:
                targets.append(rule.to_agent)
        return targets
    
    def validate_handoff(self, from_agent: str, to_agent: str) -> bool:
        """Check if a handoff is allowed by the configuration."""
        # Check if both agents exist
        if from_agent not in self.agents or to_agent not in self.agents:
            return False
        
        # Check handoff rules
        for rule in self.config.handoffs:
            if rule.from_agent == from_agent and rule.to_agent == to_agent:
                return True
        
        return False
    
    def get_collaboration_pattern(self, pattern_name: str) -> Optional[Dict[str, Any]]:
        """Get collaboration pattern configuration by name."""
        for pattern in self.config.collaboration_patterns:
            if pattern.name == pattern_name:
                return pattern.model_dump()
        return None
    
    def get_guardrail_policies(self, agent_name: str) -> List[Dict[str, Any]]:
        """Get guardrail policies for a specific agent."""
        agent_config = self.get_agent_config(agent_name)
        if not agent_config:
            return []
        
        policies = []
        for policy_name in agent_config.guardrail_policies:
            for policy in self.config.guardrail_policies:
                if policy.name == policy_name:
                    policies.append(policy.model_dump())
        
        return policies
    
    def get_agent_names(self) -> List[str]:
        """Get list of agent names in the team."""
        return list(self.agents.keys())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert team configuration to dictionary."""
        return self.config.model_dump()
    
    def __repr__(self) -> str:
        return f"Team(name='{self.config.name}', agents={len(self.agents)}, tools={len(self.tools)})"