import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from jinja2 import Environment, FileSystemLoader

from .config import TeamConfig, AgentConfig, ToolConfig
from ..event import initialize_event_bus

if TYPE_CHECKING:
    from .orchestrator import Orchestrator

class Team:
    """
    Represents a loaded team configuration with all agents, tools, and collaboration patterns.
    This is a data structure, not an execution engine.
    """
    
    def __init__(self, config: TeamConfig, config_dir: Path):
        self.config = config
        self.config_dir = config_dir
        self.agents: Dict[str, AgentConfig] = {agent.name: agent for agent in config.agents}
        self.tools: Dict[str, ToolConfig] = {tool.name: tool for tool in config.tools}
        self._jinja_env = Environment(
            loader=FileSystemLoader(config_dir),
            autoescape=False
        )
        self._orchestrator: Optional["Orchestrator"] = None
    
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
        return self.config.handoff_rules
    
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
    
    def get_agent(self, name: str) -> Optional[AgentConfig]:
        """Get agent configuration by name."""
        return self.agents.get(name)
    
    def get_tool(self, name: str) -> Optional[ToolConfig]:
        """Get tool configuration by name."""
        return self.tools.get(name)
    
    def get_agent_tools(self, agent_name: str) -> List[ToolConfig]:
        """Get all tools available to a specific agent."""
        agent = self.get_agent(agent_name)
        if not agent:
            return []
        
        return [self.tools[tool_name] for tool_name in agent.tools if tool_name in self.tools]
    
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
        agent = self.get_agent(agent_name)
        if not agent:
            raise ValueError(f"Agent not found: {agent_name}")
        
        try:
            template = self._jinja_env.get_template(agent.prompt_template)
            return template.render(**context)
        except Exception as e:
            raise ValueError(f"Error rendering prompt for agent {agent_name}: {e}")
    
    def get_handoff_targets(self, from_agent: str) -> List[str]:
        """Get possible handoff targets for an agent."""
        targets = []
        for rule in self.config.handoff_rules:
            if rule.from_agent == from_agent:
                targets.append(rule.to_agent)
        return targets
    
    def validate_handoff(self, from_agent: str, to_agent: str) -> bool:
        """Check if a handoff is allowed by the configuration."""
        # Check if both agents exist
        if from_agent not in self.agents or to_agent not in self.agents:
            return False
        
        # Check handoff rules
        for rule in self.config.handoff_rules:
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
        agent = self.get_agent(agent_name)
        if not agent:
            return []
        
        policies = []
        for policy_name in agent.guardrail_policies:
            for policy in self.config.guardrail_policies:
                if policy.name == policy_name:
                    policies.append(policy.model_dump())
        
        return policies
    
    def get_agent_names(self) -> List[str]:
        """Get list of agent names in the team."""
        return list(self.agents.keys())
    
    async def _get_orchestrator(self) -> "Orchestrator":
        """Get or create the orchestrator for this team."""
        if self._orchestrator is None:
            # Initialize event bus if not already done
            await initialize_event_bus()
            # Import here to avoid circular import
            from .orchestrator import Orchestrator
            self._orchestrator = Orchestrator(self)
        return self._orchestrator
    
    async def run(self, initial_message: str, initial_agent: Optional[str] = None) -> "ChatHistory":
        """
        Run a conversation with the team.
        
        Args:
            initial_message: The initial message to start the conversation
            initial_agent: Optional agent to start with (defaults to first agent)
            
        Returns:
            ChatHistory object with the conversation results
        """
        # Get orchestrator
        orchestrator = await self._get_orchestrator()
        
        # Start the task
        task_id = await orchestrator.start_task(
            prompt=initial_message,
            initial_agent=initial_agent
        )
        
        # Execute the task
        task_state = await orchestrator.execute_task(task_id)
        
        # Convert task state to chat history
        return ChatHistory.from_task_state(task_state)
    
    async def start_conversation(self, initial_message: str) -> "ChatHistory":
        """
        Start a conversation (alias for run for backward compatibility).
        
        Args:
            initial_message: The initial message to start the conversation
            
        Returns:
            ChatHistory object with the conversation results
        """
        return await self.run(initial_message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert team configuration to dictionary."""
        return self.config.model_dump()
    
    def __repr__(self) -> str:
        return f"Team(name='{self.config.name}', agents={len(self.agents)}, tools={len(self.tools)})"


class ChatHistory:
    """Represents the history of a chat conversation."""
    
    def __init__(self, task_id: str, messages: List[Dict[str, Any]], metadata: Dict[str, Any] = None):
        self.task_id = task_id
        self.messages = messages
        self.metadata = metadata or {}
    
    @classmethod
    def from_task_state(cls, task_state) -> "ChatHistory":
        """Create ChatHistory from a TaskState."""
        messages = []
        
        # Convert task steps to messages
        for step in task_state.history:
            for part in step.parts:
                if hasattr(part, 'text'):  # TextPart
                    messages.append({
                        'role': 'assistant' if step.agent_name != 'user' else 'user',
                        'content': part.text,
                        'agent': step.agent_name,
                        'timestamp': step.timestamp.isoformat() if step.timestamp else None,
                        'step_id': step.step_id
                    })
        
        metadata = {
            'task_id': task_state.task_id,
            'total_steps': len(task_state.history),
            'is_complete': task_state.is_complete,
            'created_at': task_state.created_at.isoformat(),
            'artifacts': task_state.artifacts
        }
        
        return cls(task_state.task_id, messages, metadata)
    
    def __len__(self) -> int:
        """Return the number of messages."""
        return len(self.messages)
    
    def __repr__(self) -> str:
        return f"ChatHistory(task_id='{self.task_id}', messages={len(self.messages)})" 