import yaml
import os
import importlib
from typing import Dict, Any, List, Optional
from pathlib import Path

from autogen import GroupChat, GroupChatManager, ConversableAgent

from .agents import Agent, ToolExecutorAgent
from roboco.tool import create_tool_function_for_ag2
from roboco.config import create_prompt_loader
from roboco.core.exceptions import ConfigurationError
from roboco.event import InMemoryEventBus, Event

from .models import CollaborationResult

from dotenv import load_dotenv

# Load environment variables from .env file, which should contain OPENAI_API_KEY
load_dotenv()

class CollaborationStartedEvent(Event):
    """Event emitted when collaboration starts."""
    def __init__(self, team_name: str, task: str, participants: List[str]):
        super().__init__(
            event_type="collaboration.started",
            payload={
                "team_name": team_name,
                "task": task,
                "participants": participants
            }
        )

class CollaborationCompletedEvent(Event):
    """Event emitted when collaboration completes."""
    def __init__(self, team_name: str, task: str, result: str, participants: List[str]):
        super().__init__(
            event_type="collaboration.completed", 
            payload={
                "team_name": team_name,
                "task": task,
                "result": result,
                "participants": participants
            }
        )

class TeamManager:
    """
    Manages and orchestrates collaborative teams of AI agents.
    Unlike workflows, teams operate through dynamic collaboration and conversation.
    """
    def __init__(self, config_path: str, event_bus: Optional[InMemoryEventBus] = None):
        """
        Initializes the TeamManager.

        Args:
            config_path: Path to the team configuration YAML file.
            event_bus: Optional event bus for system integration. Creates new one if not provided.
        """
        self.config_path = config_path
        self.config_dir = Path(config_path).parent
        self.config = self._load_config()
        
        # Initialize event system
        self.event_bus = event_bus or InMemoryEventBus()
        
        # Initialize prompt loader (optional)
        try:
            self.prompt_loader = create_prompt_loader(str(self.config_dir))
        except ConfigurationError:
            self.prompt_loader = None
        
        # Initialize components
        self.agents = {}
        self.tools = {}
        self.group_chat = None
        self.group_chat_manager = None
        
        self._initialize_team()

    def _load_config(self) -> Dict[str, Any]:
        """Load and validate team configuration."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            raise ConfigurationError(f"Team configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Error parsing team configuration: {e}")

    def _get_merged_variables(self, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge global variables with agent-specific variables.
        
        Args:
            agent_config: Agent configuration dictionary
            
        Returns:
            Merged variables dictionary
        """
        # Start with global variables
        merged_vars = self.config.get("variables", {}).copy()
        
        # Add agent-specific variables
        agent_vars = agent_config.get("prompt_variables", {})
        merged_vars.update(agent_vars)
        
        return merged_vars

    def _load_agent_prompt(self, agent_config: Dict[str, Any]) -> str:
        """
        Load and process agent prompt from file.
        
        Args:
            agent_config: Agent configuration dictionary
            
        Returns:
            Processed prompt text
        """
        prompt_file = agent_config.get("prompt_file")
        if not prompt_file:
            # Fallback to system_message if no prompt_file specified
            return agent_config.get("system_message", "You are a helpful AI Assistant.")
        
        # Get merged variables for this agent
        variables = self._get_merged_variables(agent_config)
        
        # Load and process the prompt if prompt loader is available
        if self.prompt_loader:
            try:
                return self.prompt_loader.load_prompt(prompt_file, variables)
            except Exception as e:
                raise ConfigurationError(f"Error loading prompt for agent {agent_config.get('name', 'unknown')}: {e}")
        else:
            raise ConfigurationError(f"Cannot load prompt file {prompt_file}: no prompts directory found")

    def _initialize_team(self):
        """Initialize all team components from configuration."""
        self._initialize_tools()
        self._initialize_agents()
        self._setup_group_chat()

    def _initialize_tools(self):
        """Initialize tools from configuration."""

        # Memory tools are initialized separately by agents that need them
        
        # Load configured tools
        tools_config = self.config.get("tools", [])
        
        for tool_config in tools_config:
            try:
                # Import the tool class
                module_path, class_name = tool_config["class"].rsplit(".", 1)
                module = importlib.import_module(module_path)
                tool_class = getattr(module, class_name)
                
                # Create tool instance
                tool_instance_config = tool_config.get("config", {})
                tool_instance = tool_class(**tool_instance_config)
                
                # Store tool and create AutoGen function
                tool_name = tool_config["name"]
                self.tools[tool_name] = tool_instance
                
            except Exception as e:
                raise ConfigurationError(f"Error initializing tool {tool_config.get('name', 'unknown')}: {e}")

    def _initialize_agents(self):
        """Initialize agents from configuration."""
        agents_config = self.config.get("agents", [])
        
        for agent_config in agents_config:
            try:
                # Get the agent class
                agent_class_path = agent_config["class"]
                module_path, class_name = agent_class_path.rsplit(".", 1)
                module = importlib.import_module(module_path)
                agent_class = getattr(module, class_name)
                
                # Load and process the prompt
                system_message = self._load_agent_prompt(agent_config)
                
                # Prepare agent arguments
                agent_args = {
                    "name": agent_config["name"],
                    "system_message": system_message,
                }
                
                # Add LLM config if provided
                if "llm_config" in agent_config:
                    llm_config = agent_config["llm_config"].copy()
                    
                    # Set API key from environment if not specified
                    if "config_list" in llm_config:
                        for config in llm_config["config_list"]:
                            if "api_key" not in config:
                                config["api_key"] = os.getenv("OPENAI_API_KEY")
                    
                    agent_args["llm_config"] = llm_config
                
                # Create agent
                agent = agent_class(**agent_args)
                
                # Register memory tools with all agents that have LLM config
                if hasattr(agent, 'llm_config') and agent.llm_config and hasattr(self, 'memory_manager'):
                    from roboco.builtin_tools.memory_tools import create_memory_tools
                    memory_tools = create_memory_tools(self.memory_manager)
                    
                    for memory_tool in memory_tools:
                        tool_function = create_tool_function_for_ag2(memory_tool)
                        agent.register_for_execution(name=memory_tool.name)(tool_function)
                        agent.register_for_llm(name=memory_tool.name, description=memory_tool.description)(tool_function)
                
                # Register configured tools with the agent if it's a ToolExecutorAgent
                if isinstance(agent, ToolExecutorAgent):
                    for tool_name, tool_instance in self.tools.items():
                        tool_function = create_tool_function_for_ag2(tool_instance)
                        agent.register_for_execution(name=tool_name)(tool_function)
                        
                        # Only register for LLM if the agent has LLM config
                        if hasattr(agent, 'llm_config') and agent.llm_config:
                            agent.register_for_llm(name=tool_name, description=f"Tool: {tool_name}")(tool_function)
                
                self.agents[agent_config["name"]] = agent
                
            except Exception as e:
                raise ConfigurationError(f"Error initializing agent {agent_config.get('name', 'unknown')}: {e}")

    def _setup_group_chat(self):
        """Setup the group chat for collaboration."""
        if not self.agents:
            raise ConfigurationError("No agents configured for the team")
        
        # Get group chat configuration
        group_chat_config = self.config.get("group_chat", {})
        collaboration_config = self.config.get("collaboration", {})
        
        # Create group chat
        agents_list = list(self.agents.values())
        self.group_chat = GroupChat(
            agents=agents_list,
            messages=[],
            max_round=group_chat_config.get("max_round", collaboration_config.get("max_rounds", 10)),
            speaker_selection_method=group_chat_config.get("speaker_selection_method", 
                                                         collaboration_config.get("speaker_selection_method", "auto")),
            allow_repeat_speaker=group_chat_config.get("allow_repeat_speaker", 
                                                     collaboration_config.get("allow_repeat_speaker", False))
        )
        
        # Create group chat manager
        # Use the first agent with LLM config as the manager
        manager_agent = None
        for agent in agents_list:
            if hasattr(agent, 'llm_config') and agent.llm_config:
                manager_agent = agent
                break
        
        if not manager_agent:
            raise ConfigurationError("No agent with LLM config found to serve as group chat manager")
        
        self.group_chat_manager = GroupChatManager(
            groupchat=self.group_chat,
            llm_config=manager_agent.llm_config
        )

    def get_team_info(self) -> Dict[str, Any]:
        """
        Get information about the current team.
        
        Returns:
            Dictionary containing team information
        """
        return {
            "project": self.config.get("project", {}),
            "agents": [{"name": name, "class": type(agent).__name__} for name, agent in self.agents.items()],
            "tools": [{"name": name, "class": type(tool).__name__} for name, tool in self.tools.items()],
            "variables": self.config.get("variables", {}),
            "collaboration_settings": self.config.get("collaboration", {}),
        }

    async def run(self, task: str, max_rounds: Optional[int] = None, 
                  human_input_mode: Optional[str] = None) -> CollaborationResult:
        """
        Start a collaborative session with the team.
        
        Args:
            task: The initial task or request to be processed by the team.
            max_rounds: Maximum number of collaboration rounds (overrides config if provided)
            human_input_mode: Human-in-the-loop mode (overrides config if provided):
                            - "ALWAYS": Request human input for every message
                            - "TERMINATE": Only request human input for termination decisions  
                            - "NEVER": Fully automated (good for demos)
        
        Returns:
            CollaborationResult: The result of the team collaboration.
        """
        if not self.group_chat_manager:
            raise ConfigurationError("Team not properly initialized")
        
        # Get collaboration config
        collaboration_config = self.config.get("collaboration", {})
        
        # Use provided max_rounds or fall back to config, then default
        if max_rounds is not None:
            self.group_chat.max_round = max_rounds
        elif "max_rounds" in collaboration_config:
            self.group_chat.max_round = collaboration_config["max_rounds"]
        
        # Use provided human_input_mode or fall back to config, then default
        if human_input_mode is None:
            human_input_mode = collaboration_config.get("human_input_mode", "NEVER")
        
        # Get team info for events
        team_name = self.config.get("project", {}).get("name", "Unknown Team")
        participants = list(self.agents.keys())
        
        # Start event bus if not already started
        if not self.event_bus._running:
            await self.event_bus.start()
        
        # Emit collaboration started event
        start_event = CollaborationStartedEvent(team_name, task, participants)
        await self.event_bus.publish(start_event)
        
        try:
            # Start the collaboration with human-in-the-loop mode
            result = self.group_chat_manager.initiate_chat(
                self.group_chat_manager,
                message=task,
                clear_history=True,
                human_input_mode=human_input_mode
            )
            
            # Extract information from the result
            chat_history = []
            if hasattr(self.group_chat, 'messages'):
                chat_history = [
                    {
                        "name": msg.get("name", "Unknown"),
                        "content": msg.get("content", ""),
                        "role": msg.get("role", "assistant")
                    }
                    for msg in self.group_chat.messages
                ]
            
            # Create summary
            if chat_history:
                last_message = chat_history[-1]["content"] if chat_history else "No messages"
                summary = f"Team collaboration completed. Final result: {last_message[:200]}..."
            else:
                summary = "Team collaboration completed with no recorded messages."
            
            # Get participant names
            participants = list(self.agents.keys())
            
            # Emit collaboration completed event
            completion_event = CollaborationCompletedEvent(team_name, task, summary, participants)
            await self.event_bus.publish(completion_event)
            
            return CollaborationResult(
                summary=summary,
                chat_history=chat_history,
                participants=participants,
                success=True
            )
            
        except Exception as e:
            error_msg = f"Collaboration failed: {str(e)}"
            
            # Emit collaboration completed event (with error)
            completion_event = CollaborationCompletedEvent(team_name, task, error_msg, participants)
            await self.event_bus.publish(completion_event)
            
            return CollaborationResult(
                summary=error_msg,
                chat_history=[],
                participants=list(self.agents.keys()),
                success=False,
                error_message=str(e)
            )

    async def collaborate(self, team_config_path: str, task: str) -> Dict[str, Any]:
        """
        Load a team configuration and start collaboration.
        
        Args:
            team_config_path: Path to team configuration file
            task: Task to execute
            
        Returns:
            Dictionary containing collaboration result
        """
        from roboco.config.loaders import ConfigLoader
        
        # Load the team configuration
        loader = ConfigLoader()
        config = loader.load_team_config(team_config_path)
        
        # Create a new team manager instance with the config
        temp_manager = TeamManager.__new__(TeamManager)
        temp_manager.config = config
        temp_manager.config_path = team_config_path
        temp_manager.prompt_loader = self.prompt_loader

        temp_manager.event_bus = self.event_bus
        temp_manager.agents = {}
        temp_manager.tools = {}
        temp_manager.group_chat = None
        temp_manager.group_chat_manager = None
        
        # Initialize the temporary team
        temp_manager._initialize_team()
        
        # Start collaboration
        result = await temp_manager.run(task)
        
        return {
            "success": result.success,
            "summary": result.summary,
            "chat_history": result.chat_history,
            "participants": result.participants,
            "error": result.error_message if not result.success else None
        }

    async def stream_collaborate(self, team_config_path: str, task: str):
        """
        Stream collaboration events.
        
        Args:
            team_config_path: Path to team configuration file
            task: Task to execute
            
        Yields:
            Collaboration events as they occur
        """
        # This is a simplified streaming implementation
        # In a full implementation, you'd want to stream actual conversation events
        
        yield {"type": "collaboration_started", "task": task, "config": team_config_path}
        
        try:
            result = await self.collaborate(team_config_path, task)
            yield {"type": "collaboration_result", "result": result}
        except Exception as e:
            yield {"type": "collaboration_error", "error": str(e)} 