import yaml
import os
import importlib
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from autogen import ConversableAgent
from autogen.agentchat import initiate_group_chat
from autogen.agentchat.group.patterns import AutoPattern

from .agents import Agent, ToolExecutorAgent
from .task_manager import TaskManager
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
    def __init__(self, team_name: str, task: str, participants: List[str], success: bool, summary: str):
        super().__init__(
            event_type="collaboration.completed",
            payload={
                "team_name": team_name,
                "task": task,
                "participants": participants,
                "success": success,
                "summary": summary
            }
        )

class TeamManager:
    """
    Manages a team of agents and their collaboration.
    
    This class handles:
    - Loading team configuration
    - Initializing agents and tools
    - Managing group chat and conversation flow
    - Coordinating memory and event systems
    - Task session management and continuation
    """

    def __init__(self, config_path: str, event_bus: Optional[InMemoryEventBus] = None, task_id: Optional[str] = None):
        """
        Initialize the team manager.
        
        Args:
            config_path: Path to the team configuration file
            event_bus: Optional event bus for coordination
            task_id: Optional existing task ID to continue
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # Get config directory for prompt loader
        config_dir = Path(config_path).parent
        self.prompt_loader = create_prompt_loader(str(Path(config_path).parent))
        
        # Initialize task management
        workspace_path = Path(config_path).parent / "workspace"
        self.task_manager = TaskManager(str(workspace_path))
        self.task_id = task_id
        
        # Initialize event bus
        self.event_bus = event_bus or InMemoryEventBus()
        
        # Initialize components
        self.agents: Dict[str, ConversableAgent] = {}
        self.tools: Dict[str, Any] = {}
        self.memory_manager = None
        self.pattern = None  # Will hold the AutoPattern for group chat
        
        # Initialize the team
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
        self._initialize_memory()  # Initialize memory first
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
                
                # Store tool
                tool_name = tool_config["name"]
                self.tools[tool_name] = tool_instance
                
            except Exception as e:
                raise ConfigurationError(f"Error initializing tool {tool_config.get('name', 'unknown')}: {e}")

    def _initialize_agents(self):
        """Initialize agents from configuration."""
        agents_config = self.config.get("agents", [])
        
        if not agents_config:
            raise ConfigurationError("No agents configured in the team")
        
        for agent_config in agents_config:
            try:
                # Import the agent class
                module_path, class_name = agent_config["class"].rsplit(".", 1)
                module = importlib.import_module(module_path)
                agent_class = getattr(module, class_name)
                
                # Load agent prompt
                system_message = self._load_agent_prompt(agent_config)
                
                # Prepare agent tools as functions
                agent_tools = agent_config.get("tools", [])
                agent_functions = []
                
                # Add memory tools if memory manager is available
                # TEMPORARILY DISABLED for testing
                # if self.memory_manager:
                #     from roboco.builtin_tools.memory_tools import create_memory_tools
                #     memory_tools = create_memory_tools(self.memory_manager, run_id=self.task_id)
                #     
                #     for memory_tool in memory_tools:
                #         tool_function = create_tool_function_for_ag2(memory_tool)
                #         self.tools[memory_tool.name] = memory_tool
                #         agent_functions.append(tool_function)
                
                # Add agent-specific tools
                for tool_name in agent_tools:
                    if tool_name in self.tools:
                        tool_instance = self.tools[tool_name]
                        tool_function = create_tool_function_for_ag2(tool_instance)
                        agent_functions.append(tool_function)
                    else:
                        raise ConfigurationError(f"Tool '{tool_name}' not found for agent '{agent_config['name']}'")
                
                # Create agent with functions
                agent_name = agent_config["name"]
                llm_config = agent_config.get("llm_config")
                
                # Process LLM config if provided
                if llm_config:
                    llm_config = llm_config.copy()
                    
                    # Set API key from environment if not specified
                    if "config_list" in llm_config:
                        for config in llm_config["config_list"]:
                            if "api_key" not in config or config["api_key"] is None:
                                config["api_key"] = os.getenv("OPENAI_API_KEY")
                
                # Create agent instance
                agent = agent_class(
                    name=agent_name,
                    system_message=system_message,
                    llm_config=llm_config,
                    functions=agent_functions if agent_functions else None,  # Only pass functions if there are any
                    human_input_mode="NEVER"  # Set to NEVER by default, will be overridden later if needed
                )
                
                self.agents[agent_name] = agent
                
            except Exception as e:
                raise ConfigurationError(f"Error initializing agent {agent_config.get('name', 'unknown')}: {e}")

    def _setup_group_chat(self):
        """Setup the group chat for collaboration using modern AG2 AutoPattern."""
        if not self.agents:
            raise ConfigurationError("No agents configured for the team")
        
        # Get team configuration
        team_config = self.config.get("team", {})
        
        # Get agents list
        agents_list = list(self.agents.values())
        
        # Set up message interceptor for incremental saving
        self._setup_message_interceptor(agents_list)
        
        # Find the first agent to be the initial agent (typically planner)
        initial_agent = agents_list[0]
        
        # Find an agent with LLM config for the group manager
        manager_llm_config = None
        for agent in agents_list:
            if hasattr(agent, 'llm_config') and agent.llm_config:
                manager_llm_config = agent.llm_config
                break
        
        if not manager_llm_config:
            raise ConfigurationError("No agent with LLM config found to serve as group chat manager")
        
        # Create the AutoPattern for group chat
        self.pattern = AutoPattern(
            initial_agent=initial_agent,
            agents=agents_list,
            group_manager_args={"llm_config": manager_llm_config}
        )

    def _setup_message_interceptor(self, agents_list):
        """Set up message interceptor to save conversation progress incrementally."""
        def message_interceptor(recipient, messages, sender, config):
            """Intercept and save each message as it happens."""
            if self.task_id and messages:
                # Get the latest message
                latest_message = messages[-1]
                
                # Build current chat history from all messages
                chat_history = []
                for msg in messages:
                    chat_history.append({
                        'content': msg.get('content', ''),
                        'role': msg.get('role', 'user'),
                        'name': msg.get('name', sender.name if hasattr(sender, 'name') else 'unknown')
                    })
                
                # Save progress incrementally
                self.task_manager.save_conversation_progress(
                    task_id=self.task_id,
                    chat_history=chat_history,
                    current_round=len(chat_history)
                )
                
                print(f"💾 Saved message from {sender.name if hasattr(sender, 'name') else 'unknown'} (Round {len(chat_history)})")
            
            # Return False to continue normal conversation flow
            return False, None
        
        # Register the interceptor with all agents
        for agent in agents_list:
            if hasattr(agent, 'register_reply'):
                agent.register_reply(
                    trigger=[type(None)],  # Trigger on any message
                    reply_func=message_interceptor,
                    config={}
                )

    def _initialize_memory(self):
        """Initialize memory system if configured."""
        memory_config = self.config.get("memory")
        if not memory_config:
            return
        
        try:
            from roboco.memory.manager import MemoryManager
            self.memory_manager = MemoryManager(memory_config)
        except ImportError:
            raise ConfigurationError("Memory system not available. Install required dependencies.")
        except Exception as e:
            raise ConfigurationError(f"Error initializing memory system: {e}")

    async def run(
        self, 
        task: str, 
        max_rounds: Optional[int] = None,
        human_input_mode: Optional[str] = None,
        continue_task: bool = False
    ) -> CollaborationResult:
        """
        Execute a collaborative task with the team.
        
        Args:
            task: The task description for the team to work on
            max_rounds: Optional override for maximum conversation rounds
            human_input_mode: Optional override for human input mode
            continue_task: Whether to continue an existing task or create new one
            
        Returns:
            CollaborationResult containing the outcome and details
        """
        # Start event bus if not already started
        if not self.event_bus._running:
            await self.event_bus.start()
        
        # Handle task session management
        if not self.task_id or not continue_task:
            # Create new task session
            team_config = self.config.get("team", {})
            self.task_id = self.task_manager.create_task(
                task_description=task,
                config_path=self.config_path,
                max_rounds=max_rounds or team_config.get("max_rounds", 50),
                metadata={"human_input_mode": human_input_mode}
            )
            print(f"🆔 Created new task session: {self.task_id}")
        else:
            # Update existing task
            self.task_manager.update_task(
                self.task_id,
                status='active',
                metadata={"resumed_at": str(datetime.now())}
            )
            print(f"🔄 Continuing task session: {self.task_id}")
        
        # Get team configuration
        team_config = self.config.get("team", {})
        
        # Apply human input mode to all agents
        target_human_input_mode = human_input_mode or team_config.get("human_input_mode", "NEVER")
        
        for agent in self.agents.values():
            if hasattr(agent, 'human_input_mode'):
                agent.human_input_mode = target_human_input_mode
                print(f"🔧 Set {agent.name} human_input_mode to {target_human_input_mode}")
        
        print(f"🎯 All agents set to human_input_mode: {target_human_input_mode}")
        
        # Emit collaboration started event
        participants = list(self.agents.keys())
        team_name = self.config.get("name", "UnnamedTeam")
        
        start_event = CollaborationStartedEvent(team_name, task, participants)
        await self.event_bus.publish(start_event)
        
        try:
            # Prepare task message for continuation
            if continue_task and self.task_id:
                # Search for previous work in memory
                if self.memory_manager:
                    previous_memories = self.memory_manager.search_memory(
                        query="requirements plan execution",
                        run_id=self.task_id,
                        limit=5
                    )
                    if previous_memories:
                        task = f"Continue working on: {task}\n\nPrevious work found in memory. Please search memory to understand current progress and continue from where we left off."
            
            # Start the collaboration using modern AG2 approach
            result, context, last_agent = initiate_group_chat(
                pattern=self.pattern,
                messages=task,
                max_rounds=max_rounds or team_config.get("max_rounds", 10)
            )
            
            # Debug: Check what result contains
            print(f"DEBUG: result type: {type(result)}")
            print(f"DEBUG: result: {result}")
            print(f"DEBUG: context type: {type(context)}")
            print(f"DEBUG: last_agent: {last_agent}")
            
            # Extract results
            chat_history = result.chat_history if hasattr(result, 'chat_history') else []
            max_rounds_used = max_rounds or team_config.get("max_rounds", 10)
            
            # Determine if conversation completed naturally or hit max rounds
            if len(chat_history) >= max_rounds_used:
                # Hit max rounds - mark as paused for resumption
                success = True  # Not a failure, just needs continuation
                summary = f"Conversation paused after {len(chat_history)} rounds (max reached). Can be resumed."
                final_status = 'paused'
                metadata_update = {
                    "paused_at": str(datetime.now()),
                    "paused_reason": "max_rounds_reached",
                    "last_agent": str(last_agent) if last_agent else None
                }
            else:
                # Completed naturally
                success = True
                summary = "Collaboration completed successfully"
                final_status = 'completed'
                metadata_update = {"completed_at": str(datetime.now())}
            
            error_message = None
            
            # Final save of conversation context and status
            self.task_manager.update_task(
                self.task_id,
                status=final_status,
                current_round=len(chat_history),
                conversation_context=chat_history,
                metadata=metadata_update
            )
            
        except Exception as e:
            print(f"DEBUG: Exception during chat: {e}")
            import traceback
            traceback.print_exc()
            
            success = False
            summary = f"Collaboration failed: {str(e)}"
            chat_history = []  # No group_chat.messages in new approach
            error_message = str(e)
            
            # Update task status
            if self.task_id:
                self.task_manager.update_task(
                    self.task_id,
                    status='failed',
                    current_round=0,  # No chat history available on error
                    metadata={"failed_at": str(datetime.now()), "error": str(e)}
                )
        
        # Create result
        result = CollaborationResult(
            success=success,
            summary=summary,
            chat_history=chat_history,
            participants=participants,
            error_message=error_message,
            task_id=self.task_id  # Include task_id in result
        )
        
        # Emit collaboration completed event
        complete_event = CollaborationCompletedEvent(team_name, task, participants, success, summary)
        await self.event_bus.publish(complete_event)
        
        return result

    def get_agent(self, name: str) -> Optional[ConversableAgent]:
        """Get an agent by name."""
        return self.agents.get(name)

    def list_agents(self) -> List[str]:
        """List all agent names."""
        return list(self.agents.keys())

    def get_tool(self, name: str):
        """Get a tool by name."""
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        """List all tool names."""
        return list(self.tools.keys())

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
        temp_manager.pattern = None
        
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