"""
Team Manager - Collaborative Team Management

This module provides a high-level API for managing collaborative teams
of agents with flexible configuration and tool integration.
"""

import yaml
from typing import Dict, Any, List, Optional
from datetime import datetime

from autogen import ConversableAgent
from autogen.agentchat import initiate_group_chat

from autogen.agentchat.group.patterns import AutoPattern
from .task_manager import TaskManager
from .models import CollaborationResult
from roboco.core.exceptions import ConfigurationError
from roboco.event.bus import InMemoryEventBus
from roboco.event.events import Event

from dotenv import load_dotenv

# Load environment variables from .env file, which should contain OPENAI_API_KEY
load_dotenv()

class CollaborationStartedEvent(Event):
    """Event emitted when collaboration starts."""
    def __init__(self, team_name: str, task: str, participants: List[str]):
        super().__init__(
            event_type="collaboration.started",
            data={
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
            data={
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
        """Initialize the team manager with configuration.
        
        Args:
            config_path: Path to team configuration file
            event_bus: Optional event bus for monitoring
            task_id: Optional task ID for memory context
        """
        # Load configuration
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize components
        self.agents = {}
        self.pattern = None
        self.memory_manager = None
        self.tool_registry = None
        self.task_id = task_id
        
        # Set up event bus
        self.event_bus = event_bus or InMemoryEventBus()
        
        # Set up task manager
        self.task_manager = TaskManager()
        
        # Initialize team components
        self._initialize_memory()
        self._initialize_tools()
        self._initialize_agents()
        self._setup_group_chat()
        
        # Set up memory tools context if task_id is provided
        if task_id:
            self._reinitialize_memory_tools()

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
        """Load agent prompt from file or configuration."""
        # Get merged variables (global + agent-specific)
        variables = self._get_merged_variables(agent_config)
        
        # Add task_id to variables if available
        if self.task_id:
            variables['task_id'] = self.task_id
        
        # Check if prompt is specified as a file
        if "prompt_file" in agent_config:
            prompt_file = agent_config["prompt_file"]
            try:
                prompt_content = self.prompt_loader.load_prompt(prompt_file, variables)
                
                # Add task_id instruction if available
                if self.task_id:
                    prompt_content += f"\n\nIMPORTANT: Your current task ID is '{self.task_id}'. Use this task_id when calling memory tools."
                
                return prompt_content
            except Exception as e:
                raise ConfigurationError(f"Error loading prompt file '{prompt_file}': {e}")
        
        # Use system_message directly
        system_message = agent_config.get("system_message", "You are a helpful AI assistant.")
        
        # Add task_id instruction if available
        if self.task_id:
            system_message += f"\n\nIMPORTANT: Your current task ID is '{self.task_id}'. Use this task_id when calling memory tools."
        
        return system_message

    def _initialize_team(self):
        """Initialize all team components from configuration."""
        self._initialize_memory()  # Initialize memory first
        self._initialize_tools()
        self._initialize_agents()
        self._setup_group_chat()

    def _initialize_tools(self):
        """Initialize tool registry and register all tools."""
        from roboco.tool.base import ToolRegistry
        from roboco.builtin_tools import MemoryTool, BasicTool, SearchTool
        
        # Create tool registry
        self.tool_registry = ToolRegistry()
        
        # Register memory tools (required for all agents)
        if self.memory_manager:
            memory_tool = MemoryTool(memory_manager=self.memory_manager)
            self.tool_registry.register("memory", memory_tool)
        
        # Register basic tools
        workspace_path = self.config.get("workspace_path", "./workspace")
        basic_tool = BasicTool(workspace_path=workspace_path)
        self.tool_registry.register("basic", basic_tool)
        
        # Register search tools if available
        search_manager = self._create_search_manager()
        if search_manager:
            search_tool = SearchTool(search_manager=search_manager)
            self.tool_registry.register("search", search_tool)
        
        print(f"🧰 Initialized tool registry with {len(self.tool_registry.list())} tools")

    def _initialize_agents(self):
        """Initialize agents from configuration."""
        agents_config = self.config.get("agents", [])
        if not agents_config:
            raise ConfigurationError("No agents configured")
        
        # Initialize agents
        self.agents = {}
        
        # Create each agent
        for agent_config in agents_config:
            try:
                # Get agent name
                agent_name = agent_config.get("name")
                if not agent_name:
                    raise ConfigurationError("Agent configuration missing 'name'")
                
                # Get agent role
                agent_role = agent_config.get("role")
                if not agent_role:
                    raise ConfigurationError(f"Agent {agent_name} configuration missing 'role'")
                
                # Get agent class
                agent_class = agent_config.get("class", "ConversableAgent")
                
                # Get agent system message
                system_message = self._load_agent_prompt(agent_config)
                
                # Create agent based on class
                if agent_class == "ConversableAgent":
                    from autogen import ConversableAgent
                    llm_config = agent_config.get("llm_config", {})
                    agent = ConversableAgent(
                        name=agent_name,
                        system_message=system_message,
                        llm_config=llm_config,
                        human_input_mode="NEVER"
                    )
                
                elif agent_class == "AssistantAgent":
                    from autogen import AssistantAgent
                    llm_config = agent_config.get("llm_config", {})
                    agent = AssistantAgent(
                        name=agent_name,
                        system_message=system_message,
                        llm_config=llm_config,
                        human_input_mode="NEVER"
                    )
                
                elif agent_class == "UserProxyAgent":
                    from autogen import UserProxyAgent
                    agent = UserProxyAgent(
                        name=agent_name,
                        system_message=system_message,
                        human_input_mode="NEVER",
                        max_consecutive_auto_reply=10
                    )
                
                elif agent_class == "UserAgent":
                    from roboco.core.agents import UserAgent
                    agent = UserAgent(
                        name=agent_name,
                        system_message=system_message,
                        human_input_mode="NEVER"
                    )
                
                else:
                    raise ConfigurationError(f"Unknown agent class: {agent_class}")
                
                # Store agent
                self.agents[agent_name] = agent
                
                print(f"🤖 Created agent '{agent_name}' with role '{agent_role}'")
            
            except Exception as e:
                raise ConfigurationError(f"Error initializing agent {agent_config.get('name', 'unknown')}: {e}")
        
        # ENFORCE: Must have a UserAgent
        executor = self._get_tool_executor()
        if executor is None:
            raise ConfigurationError("No UserAgent found in team configuration. Every team must have a UserAgent to act as the user proxy and tool executor.")
        
        print(f"🔧 Using {executor.name} as tool executor for all agents")
        
        # Register tools for each agent
        for agent_config in agents_config:
            agent_name = agent_config["name"]
            agent = self.agents[agent_name]
            
            # Skip tool registration for the executor itself
            if agent == executor:
                continue
            
            # Always include memory tools for all agents
            tools_to_register = ["memory"]
            
            # Add any additional tools specified in config
            agent_tools = agent_config.get("tools", [])
            tools_to_register.extend(agent_tools)
            
            # Get functions for all tools
            ag2_functions = self.tool_registry.get_functions_for_tools(tools_to_register)
            
            # Register each function with AG2
            from autogen import register_function
            for func_name, func in ag2_functions.items():
                register_function(
                    func,
                    caller=agent,
                    executor=executor,
                    description=f"Tool: {func_name}"
                )
            
            print(f"🛠️ Registered {len(ag2_functions)} tools for agent '{agent_name}': {tools_to_register}")

    def _get_tool_executor(self):
        """Find the UserAgent to use as executor for tool functions."""
        for agent in self.agents.values():
            if hasattr(agent, '__class__') and 'UserAgent' in agent.__class__.__name__:
                return agent
        return None

    def _create_search_manager(self):
        """Create a search manager instance."""
        try:
            from roboco.search import SearchManager
            import os
            
            api_key = os.getenv("SERPAPI_API_KEY")
            if api_key:
                search_manager = SearchManager(
                    default_backend="serpapi",
                    serpapi={"api_key": api_key}
                )
                return search_manager
            else:
                print(f"⚠️ No SERPAPI_API_KEY found - search tools may not work")
                return None
        except ImportError:
            print(f"⚠️ Search module not available - search tools disabled")
            return None

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

    def _reinitialize_memory_tools(self):
        """Memory tools context is already updated with task_id during initialization."""
        # Task_id is already included in system messages during agent creation
        # and memory tools receive it through prompt instructions
        if self.task_id:
            print(f"🧠 Memory tools context ready with task_id: {self.task_id}")

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
        
        # Memory tools context is already ready with task_id
        self._reinitialize_memory_tools()
        
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
                        task_id=self.task_id,
                        limit=5
                    )
                    if previous_memories:
                        task = f"Continue working on: {task}\n\nPrevious work found in memory. Please search memory to understand current progress and continue from where we left off."
            
            # Start the collaboration using modern AG2 approach with defensive handling
            try:
                result, context, last_agent = initiate_group_chat(
                    pattern=self.pattern,
                    messages=task,
                    max_rounds=max_rounds or team_config.get("max_rounds", 10)
                )
            except AttributeError as ae:
                # Handle the specific AG2 bug where message content is None and .strip() fails
                if "'NoneType' object has no attribute 'strip'" in str(ae):
                    print(f"🐛 Detected AG2 bug with None message content. Attempting workaround...")
                    
                    try:
                        # Use a different approach - start with the first agent directly
                        first_agent = list(self.agents.values())[0]
                        result = first_agent.initiate_chat(
                            self.pattern,
                            message=task if task else "Please begin the task.",
                            max_rounds=max_rounds or team_config.get("max_rounds", 10)
                        )
                        context = result
                        last_agent = first_agent
                        print(f"✅ AG2 bug workaround successful")
                    except Exception as retry_error:
                        print(f"❌ AG2 bug workaround failed: {retry_error}")
                        raise ae  # Re-raise original error
                else:
                    raise ae  # Re-raise if it's a different AttributeError
            
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
            
            # Final save of conversation context and status - with proper error handling
            try:
                update_success = self.task_manager.update_task(
                    self.task_id,
                    status=final_status,
                    current_round=len(chat_history),
                    conversation_context=chat_history,
                    metadata=metadata_update
                )
                if update_success:
                    print(f"✅ Task {self.task_id} status updated to '{final_status}'")
                else:
                    print(f"❌ Failed to update task {self.task_id} status")
            except Exception as update_error:
                print(f"❌ Error updating task status: {update_error}")
                # Force save the task session even if update fails
                try:
                    self.task_manager._save_sessions()
                    print(f"🔄 Force saved task sessions after update error")
                except Exception as save_error:
                    print(f"❌ Critical: Could not save task sessions: {save_error}")
        
        except Exception as e:
            print(f"DEBUG: Exception during chat: {e}")
            import traceback
            traceback.print_exc()
            
            success = False
            summary = f"Collaboration failed: {str(e)}"
            chat_history = []  # No group_chat.messages in new approach
            error_message = str(e)
            
            # Update task status - with proper error handling
            if self.task_id:
                try:
                    update_success = self.task_manager.update_task(
                        self.task_id,
                        status='failed',
                        current_round=0,  # No chat history available on error
                        metadata={"failed_at": str(datetime.now()), "error": str(e)}
                    )
                    if update_success:
                        print(f"✅ Task {self.task_id} status updated to 'failed'")
                    else:
                        print(f"❌ Failed to update task {self.task_id} status")
                except Exception as update_error:
                    print(f"❌ Error updating task status: {update_error}")
                    # Force save the task session even if update fails
                    try:
                        self.task_manager._save_sessions()
                        print(f"🔄 Force saved task sessions after update error")
                    except Exception as save_error:
                        print(f"❌ Critical: Could not save task sessions: {save_error}")
        
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