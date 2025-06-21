"""
Task execution class - the primary interface for AgentX task execution.

Clean API:
    # One-shot execution
    await execute_task(prompt, config_path)
    
    # Step-by-step execution
    task = start_task(prompt, config_path)
    while not task.is_complete:
        await task.step()
"""

from typing import Dict, List, Optional, Any, AsyncGenerator
from pathlib import Path
from datetime import datetime
import asyncio
import json
import time

from .agent import Agent
from .orchestrator import Orchestrator
from .brain import Brain
from .message import TaskStep, TextPart, ToolCallPart, ToolResultPart, Artifact
from .tool import ToolCall
from .config import TeamConfig, AgentConfig, BrainConfig
from ..config.team_loader import load_team_config
from ..config.agent_loader import load_agents_config
from ..config.prompt_loader import PromptLoader
from ..utils.logger import get_logger, setup_clean_chat_logging
from ..utils.id import generate_short_id
from ..tool.manager import ToolManager

logger = get_logger(__name__)


class Task:
    """
    Pure data container for task state and context.
    No execution logic - just holds the task data.
    """
    
    def __init__(self, team_config: TeamConfig, config_dir: Path, task_id: str = None, workspace_dir: Path = None):
        # Core task identity
        self.task_id = task_id or self._generate_task_id()
        self.team_config = team_config
        self.config_dir = config_dir
        self.workspace_dir = workspace_dir or Path("./workspace") / self.task_id
        
        # Task execution state
        self.initial_prompt: Optional[str] = None
        self.round_count: int = 0
        self.max_rounds: int = team_config.max_rounds
        self.is_complete: bool = False
        self.is_paused: bool = False
        self.created_at: datetime = datetime.now()
        
        # Task data
        self.history: List[TaskStep] = []
        self.current_agent: Optional[str] = None
        self.artifacts: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}
        
        # Agent storage (will be populated by TaskExecutor)
        self.agents: Dict[str, Agent] = {}
        
        # Setup workspace
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self._setup_workspace()
        
        logger.info(f"🎯 Task {self.task_id} initialized")
    
    def get_agent(self, name: str):
        """Get agent by name with task context injected."""
        if name not in self.agents:
            raise ValueError(f"Agent '{name}' not found in task")
        
        agent = self.agents[name]
        # Inject task reference into agent for direct access
        agent._task = self
        return agent
    
    def get_context(self) -> Dict[str, Any]:
        """Get complete task context for routing decisions."""
        return {
            "task_id": self.task_id,
            "initial_prompt": self.initial_prompt,
            "round_count": self.round_count,
            "max_rounds": self.max_rounds,
            "is_complete": self.is_complete,
            "is_paused": self.is_paused,
            "created_at": self.created_at.isoformat(),
            "current_agent": self.current_agent,
            "workspace_dir": str(self.workspace_dir),
            "available_agents": list(self.agents.keys()),
            "history_length": len(self.history),
            "artifacts": list(self.artifacts.keys()),
            "metadata": self.metadata
        }
    
    def add_step(self, step: TaskStep) -> None:
        """Add step to task history."""
        self.history.append(step)
    
    def set_current_agent(self, agent_name: str) -> None:
        """Set current agent."""
        if agent_name not in self.agents:
            raise ValueError(f"Agent '{agent_name}' not found in task")
        self.current_agent = agent_name
        logger.info(f"🔄 Task {self.task_id} switched to agent '{agent_name}'")
    
    def complete_task(self) -> None:
        """Mark task as complete."""
        self.is_complete = True
        logger.info(f"✅ Task {self.task_id} completed")
    
    def add_artifact(self, name: str, content: Any, metadata: Dict[str, Any] = None) -> None:
        """Add artifact to task."""
        self.artifacts[name] = {
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.now()
        }
        logger.info(f"📄 Task {self.task_id} added artifact '{name}'")
    
    def _generate_task_id(self) -> str:
        """Generate unique task ID."""
        return generate_short_id()
    
    def _setup_workspace(self) -> None:
        """Setup task workspace directories."""
        (self.workspace_dir / "artifacts").mkdir(exist_ok=True)
        (self.workspace_dir / "logs").mkdir(exist_ok=True)
        (self.workspace_dir / "temp").mkdir(exist_ok=True)


class TaskExecutor:
    """
    TaskExecutor manages the complete lifecycle of task execution.
    
    Responsibilities:
    - System initialization (storage, memory, search, tools, orchestrator)
    - Task coordination and execution flow
    - Clean separation from task state (which lives in Task)
    """
    
    def __init__(self, config_path: str, task_id: str = None, workspace_dir: Path = None):
        """Initialize TaskExecutor with config path and setup all systems."""
        # Load team configuration
        self.config_path = Path(config_path)
        self.task = Task(
            team_config=load_team_config(self.config_path),
            config_dir=self.config_path.parent,
            task_id=task_id,
            workspace_dir=workspace_dir
        )
        
        # Create task-level tool manager (unified registry + executor)
        self.tool_manager = ToolManager(task_id=self.task.task_id)
        
        # Initialize all systems (except orchestrator)
        self._initialize_systems()
        
        # Register task-specific tools AFTER systems are initialized
        self._register_tools()
        
        # Create agents with task-level tool manager
        self._create_agents()
        
        # Initialize orchestrator AFTER agents are created
        self.orchestrator = Orchestrator(self.task, memory_system=self.memory)
        
        # Setup clean logging for better chat experience
        setup_clean_chat_logging()
        
        logger.info(f"✅ TaskExecutor initialized for task {self.task.task_id}")

    def _initialize_systems(self):
        """Initialize storage, search, memory systems."""
        # Initialize storage system first (needed for tools)
        self.storage = self._initialize_storage()
        
        # Initialize search system
        self.search = self._initialize_search()
        
        # Initialize memory system
        self.memory = self._initialize_memory()
        
        logger.debug("✅ TaskExecutor systems initialized")

    def _initialize_storage(self):
        """Initialize the storage system for the task."""
        try:
            from ..storage.factory import StorageFactory
            
            # Create workspace storage for the task
            workspace_storage = StorageFactory.create_workspace_storage(
                workspace_path=self.task.workspace_dir,
                use_git_artifacts=True
            )
            
            logger.info(f"Storage system initialized: {self.task.workspace_dir}")
            return workspace_storage
            
        except Exception as e:
            logger.warning(f"Failed to initialize storage system: {e}")
            return None
    
    def _initialize_search(self):
        """Initialize the search system for the task."""
        try:
            from ..search.search_manager import SearchManager
            
            # Get search config from team if available
            # For now, create a basic search manager
            search_manager = SearchManager()
            
            logger.info("Search system initialized")
            return search_manager
            
        except Exception as e:
            logger.warning(f"Failed to initialize search system: {e}")
            return None
    
    def _initialize_memory(self):
        """Initialize the memory system for the task."""
        try:
            from ..memory.factory import create_memory_backend
            
            # Get memory config from team if available
            memory_config = getattr(self.task.team_config, 'memory', None)
            
            if memory_config:
                # Handle simple memory config format (from YAML)
                if isinstance(memory_config, dict) and memory_config.get('enabled', False):
                    # Create default MemoryConfig for simple YAML format
                    from .config import MemoryConfig
                    backend = create_memory_backend(MemoryConfig())
                    logger.info("Memory system initialized with default configuration")
                    return backend
                # Handle full MemoryConfig object
                elif hasattr(memory_config, 'enabled') and memory_config.enabled:
                    backend = create_memory_backend(memory_config)
                    logger.info("Memory system initialized")
                    return backend
                else:
                    logger.debug("Memory system disabled in team config")
                    return None
            else:
                logger.debug("No memory configuration found")
                return None
                
        except Exception as e:
            logger.warning(f"Failed to initialize memory system: {e}")
            return None
    
    def _create_agents(self):
        """Create agent instances from team config with task-level tool manager."""
        # Initialize prompt loader if prompts directory exists
        prompt_loader = None
        prompts_dir = self.config_path.parent / "prompts"
        if prompts_dir.exists():
            try:
                prompt_loader = PromptLoader(str(prompts_dir))
            except Exception as e:
                logger.warning(f"Could not initialize prompt loader: {e}")
        
        for agent_data in self.task.team_config.agents:
            # Convert raw agent data to AgentConfig
            name = agent_data.get('name')
            if not name:
                raise ValueError("Agent must have a 'name' field")
            
            # Load prompt template
            prompt_template = None
            prompt_file = agent_data.get('prompt_template')
            
            if prompt_file and prompt_loader:
                try:
                    # Strip "prompts/" prefix if present
                    prompt_filename = prompt_file
                    if prompt_filename.startswith("prompts/"):
                        prompt_filename = prompt_filename[8:]
                    
                    prompt_template = prompt_loader.load_prompt(prompt_filename)
                except Exception as e:
                    logger.warning(f"Could not load prompt file {prompt_file}: {e}")
            
            if not prompt_template:
                prompt_template = agent_data.get('system_message', f"You are a helpful AI assistant named {name}.")
            
            # Create brain config from llm_config
            brain_config = None
            if 'llm_config' in agent_data:
                llm_config = agent_data['llm_config']
                brain_config = BrainConfig(
                    provider=llm_config.get('provider', 'deepseek'),
                    model=llm_config.get('model', 'deepseek-chat'),
                    temperature=llm_config.get('temperature', 0.7),
                    max_tokens=llm_config.get('max_tokens', 4000),
                    api_key=llm_config.get('api_key'),
                    base_url=llm_config.get('base_url'),
                    supports_function_calls=llm_config.get('supports_function_calls', True)
                )
            
            # Create AgentConfig
            agent_config = AgentConfig(
                name=name,
                description=agent_data.get('description', f"AI assistant named {name}"),
                prompt_template=prompt_template,
                tools=agent_data.get('tools', []),
                brain_config=brain_config
            )
            
            # Create agent with tool manager
            agent = Agent(agent_config, tool_manager=self.tool_manager)
            self.task.agents[agent_config.name] = agent
            logger.info(f"✅ Created agent: {agent_config.name}")
        
        logger.info(f"🎯 Created {len(self.task.agents)} agents")
    
    # Properties to access task state (clean interface)
    @property
    def is_complete(self) -> bool:
        return self.task.is_complete
    
    @property 
    def is_paused(self) -> bool:
        return self.task.is_paused
    
    @property
    def round_count(self) -> int:
        return self.task.round_count
    
    # Properties to access initialized systems
    @property
    def workspace_storage(self):
        """Access the workspace storage system."""
        return self.storage
    
    @property
    def search_manager(self):
        """Access the search manager."""
        return self.search
    
    @property
    def memory_backend(self):
        """Access the memory backend."""
        return self.memory
    
    def _register_tools(self) -> None:
        """Register task-specific tools with workspace context using task-level tool manager."""
        try:
            # Register storage tools using the initialized storage system
            if self.storage:
                from ..builtin_tools.storage_tools import create_storage_tools
                
                # Create and register storage tools using the initialized storage system
                storage_tools = create_storage_tools(str(self.task.workspace_dir))
                for tool in storage_tools:
                    self.tool_manager.register_tool(tool)
            
            # Register all built-in tools with initialized systems using task-level tool manager
            from ..builtin_tools import register_builtin_tools
            register_builtin_tools(
                registry=self.tool_manager.registry,  # Pass the underlying registry
                workspace_path=str(self.task.workspace_dir),
                memory_system=self.memory
            )
            
            logger.debug(f"🔧 TaskExecutor registered {len(self.tool_manager.list_tools())} tools for workspace {self.task.workspace_dir}")
            
        except Exception as e:
            logger.warning(f"Failed to register task tools: {e}")

    def register_tool(self, tool) -> None:
        """Register a tool with this task's registry."""
        self.tool_manager.register_tool(tool)
        logger.debug(f"Registered tool {tool.__class__.__name__} with task {self.task.task_id}")
    
    @property
    def _orchestrator(self):
        """Access orchestrator - kept for backward compatibility."""
        return self.orchestrator
    
    def start_task(self, prompt: str, initial_agent: str = None) -> None:
        """Start task for step-by-step execution."""
        self.task.initial_prompt = prompt
        self.task.is_paused = False
        self.task.is_complete = False
        
        # Set initial agent
        if initial_agent:
            self.task.set_current_agent(initial_agent)
        elif (hasattr(self.task.team_config, 'execution') and 
              self.task.team_config.execution and 
              hasattr(self.task.team_config.execution, 'initial_agent') and 
              self.task.team_config.execution.initial_agent):
            self.task.set_current_agent(self.task.team_config.execution.initial_agent)
        else:
            # Use first agent as default
            initial_agent_name = list(self.task.agents.keys())[0]
            self.task.set_current_agent(initial_agent_name)
        
        # Add the initial prompt as a user message to the conversation history
        if prompt:
            from datetime import datetime
            user_step = TaskStep(
                step_id=self._generate_step_id(),
                agent_name="user",
                parts=[TextPart(text=prompt)],
                timestamp=datetime.now()
            )
            self.task.add_step(user_step)
        
        logger.info(f"🚀 Task started for step-by-step execution")
    
    async def execute_task(self, prompt: str, initial_agent: str = None, stream: bool = False):
        """Execute task to completion (one-shot)."""
        self.start_task(prompt, initial_agent)
        logger.info(f"🚀 Task started for one-shot execution")
        
        if stream:
            async for chunk in self._stream_execute():
                yield chunk
        else:
            await self._execute()
    
    async def step(self, user_input: str = None, stream: bool = False):
        """Execute one step (for step-by-step execution)."""
        if not self.task.initial_prompt:
            raise ValueError("Task not started. Call start_task() first.")
        
        if stream:
            async for chunk in self._stream_step(user_input):
                yield chunk
        else:
            result = await self._step(user_input)
            yield result
    
    async def _execute(self) -> None:
        """Simple execution loop - flow control only."""
        while not self.task.is_complete and self.task.round_count < self.task.max_rounds:
            if self.task.is_paused:
                break
                
            self.task.round_count += 1
            response = await self._execute_agent_turn()
            
            # Get routing decision
            context = self.task.get_context()
            routing_decision = await self.orchestrator.decide_next_step(context, response)
            
            if routing_decision["action"] == "COMPLETE":
                self.task.complete_task()
                break
            elif routing_decision["action"] == "HANDOFF":
                self.task.set_current_agent(routing_decision["next_agent"])
    
    async def _stream_execute(self):
        """Execute the task with streaming."""
        while not self.task.is_complete and self.task.round_count < self.task.max_rounds:
            if self.task.is_paused:
                break
                
            self.task.round_count += 1
            
            # Stream current agent turn
            response_chunks = []
            async for chunk in self._stream_agent_turn():
                response_chunks.append(chunk)
                yield chunk
            
            # Orchestrator makes routing decisions
            full_response = "".join(chunk.get("content", "") for chunk in response_chunks if chunk.get("type") == "content")
            context = self.task.get_context()
            routing_decision = await self._orchestrator.decide_next_step(context, full_response)
            
            # Yield routing decision
            yield {
                "type": "routing_decision",
                "action": routing_decision["action"],
                "current_agent": self.task.current_agent,
                "next_agent": routing_decision.get("next_agent"),
                "reason": routing_decision.get("reason", "")
            }
            
            if routing_decision["action"] == "COMPLETE":
                self.task.complete_task()
                break
            elif routing_decision["action"] == "HANDOFF":
                old_agent = self.task.current_agent
                self.task.set_current_agent(routing_decision["next_agent"])
                yield {
                    "type": "handoff",
                    "from_agent": old_agent,
                    "to_agent": routing_decision["next_agent"]
                }

    async def _step(self, user_input: str = None) -> Dict[str, Any]:
        """Execute one step - simple flow control."""
        if self.task.is_complete:
            return {"status": "complete", "message": "Task already complete"}
        
        if self.task.round_count >= self.task.max_rounds:
            self.task.complete_task()
            return {"status": "complete", "message": "Max rounds reached"}
        
        self.task.round_count += 1
        
        # Add user input to history if provided
        if user_input:
            user_step = TaskStep(
                step_id=self._generate_step_id(),
                agent_name="user",
                parts=[TextPart(text=user_input)],
                timestamp=datetime.now()
            )
            self.task.add_step(user_step)
        
        # Execute agent turn
        response = await self._execute_agent_turn()
        
        # Get routing decision
        context = self.task.get_context()
        routing_decision = await self.orchestrator.decide_next_step(context, response)
        
        result = {
            "status": "continue",
            "agent": self.task.current_agent,
            "response": response,
            "routing_action": routing_decision["action"],
            "next_agent": routing_decision.get("next_agent"),
            "reason": routing_decision.get("reason", ""),
            "round": self.task.round_count
        }
        
        if routing_decision["action"] == "COMPLETE":
            self.task.complete_task()
            result["status"] = "complete"
        elif routing_decision["action"] == "HANDOFF":
            old_agent = self.task.current_agent
            self.task.set_current_agent(routing_decision["next_agent"])
            result["handoff"] = {"from": old_agent, "to": routing_decision["next_agent"]}
        
        return result
    
    async def _stream_step(self, user_input: str = None):
        """Execute one step with streaming - simple flow control."""
        if self.task.is_complete:
            yield {"status": "complete", "message": "Task already complete"}
            return
        
        if self.task.round_count >= self.task.max_rounds:
            self.task.complete_task()
            yield {"status": "complete", "message": "Max rounds reached"}
            return
        
        self.task.round_count += 1
        
        # Add user input to history if provided
        if user_input:
            user_step = TaskStep(
                step_id=self._generate_step_id(),
                agent_name="user",
                parts=[TextPart(text=user_input)],
                timestamp=datetime.now()
            )
            self.task.add_step(user_step)
        
        # Stream the agent turn
        response_chunks = []
        async for chunk in self._stream_agent_turn():
            response_chunks.append(chunk)
            yield chunk
        
        # Get routing decision
        full_response = "".join(chunk.get("content", "") for chunk in response_chunks if chunk.get("type") == "content")
        context = self.task.get_context()
        routing_decision = await self.orchestrator.decide_next_step(context, full_response)
        
        # Yield routing decision
        yield {
            "type": "routing_decision",
            "action": routing_decision["action"],
            "current_agent": self.task.current_agent,
            "next_agent": routing_decision.get("next_agent"),
            "reason": routing_decision.get("reason", "")
        }
        
        if routing_decision["action"] == "COMPLETE":
            self.task.complete_task()
        elif routing_decision["action"] == "HANDOFF":
            old_agent = self.task.current_agent
            self.task.set_current_agent(routing_decision["next_agent"])
            yield {
                "type": "handoff",
                "from_agent": old_agent,
                "to_agent": routing_decision["next_agent"]
            }

    async def _execute_agent_turn(self) -> str:
        """Execute current agent turn - simple coordination."""
        # Get agent and context from task
        agent = self.task.get_agent(self.task.current_agent)
        context = self.task.get_context()
        system_prompt = agent.build_system_prompt(context)
        
        # Get conversation history
        messages = self._convert_history_to_messages()
        
        # Agent executes with injected tool manager
        final_response = await agent.generate_response(
            messages=messages,
            system_prompt=system_prompt,
            orchestrator=self.orchestrator
        )
        
        # Add response to task history
        self.task.add_step(TaskStep(
            agent_name=self.task.current_agent, 
            parts=[TextPart(text=final_response)]
        ))
        
        return final_response

    async def _stream_agent_turn(self):
        """Stream current agent turn - simple coordination."""
        # Get agent and context from task
        agent = self.task.get_agent(self.task.current_agent)
        context = self.task.get_context()
        system_prompt = agent.build_system_prompt(context)
        
        # Get conversation history
        messages = self._convert_history_to_messages()
        
        # Check if agent brain has streaming disabled
        if hasattr(agent.brain.config, 'streaming') and not agent.brain.config.streaming:
            
            # Use non-streaming mode
            final_response = await agent.generate_response(
                messages=messages,
                system_prompt=system_prompt,
                orchestrator=self.orchestrator
            )
            
            # Yield the complete response as a single chunk
            yield {"type": "content", "content": final_response}
            
            # Add response to task history
            if final_response:
                self.task.add_step(TaskStep(
                    agent_name=self.task.current_agent, 
                    parts=[TextPart(text=final_response)]
                ))
        else:
            # Stream agent response
            response_chunks = []
            async for chunk in agent.stream_response(
                messages=messages,
                system_prompt=system_prompt,
                orchestrator=self.orchestrator
            ):
                # Handle different chunk types
                if isinstance(chunk, dict):
                    # Structured chunk from agent (tool calls, tool results, etc.)
                    yield chunk
                    if chunk.get("type") == "content":
                        response_chunks.append(chunk.get("content", ""))
                else:
                    # Text chunk from agent
                    response_chunks.append(chunk)
                    yield {"type": "content", "content": chunk}
            
            # Add response to task history
            final_response = "".join(response_chunks)
            if final_response:
                self.task.add_step(TaskStep(
                    agent_name=self.task.current_agent, 
                    parts=[TextPart(text=final_response)]
                ))

    async def _execute_single_tool(self, tool_call: Any) -> ToolResultPart:
        """Helper to execute one tool call and return a ToolResultPart."""
        tool_name = tool_call.function.name
        try:
            tool_args = json.loads(tool_call.function.arguments)
            tool_result: ToolResult = await execute_tool(name=tool_name, **tool_args)
            return ToolResultPart(
                tool_call_id=tool_call.id,
                tool_name=tool_name,
                result=tool_result.result,
                is_error=not tool_result.success
            )
        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}")
            return ToolResultPart(
                tool_call_id=tool_call.id,
                tool_name=tool_name,
                result=f"Error executing tool: {e}",
                is_error=True
            )


    
    def _convert_history_to_messages(self) -> List[Dict[str, Any]]:
        """Convert task history to conversation message format for agents."""
        messages = []
        
        for step in self.task.history:
            if step.agent_name == "user":
                # User messages
                for part in step.parts:
                    if isinstance(part, TextPart):
                        messages.append({
                            "role": "user",
                            "content": part.text
                        })
            elif step.agent_name == "system":
                # Tool results
                for part in step.parts:
                    if isinstance(part, ToolResultPart):
                        messages.append({
                            "role": "tool",
                            "tool_call_id": part.tool_call_id,
                            "name": part.tool_name,
                            "content": json.dumps({
                                "success": not part.is_error,
                                "result": part.result
                            })
                        })
            else:
                # Agent messages
                for part in step.parts:
                    if isinstance(part, TextPart):
                        messages.append({
                            "role": "assistant",
                            "content": part.text
                        })
                    elif isinstance(part, ToolCallPart):
                        # This would be part of an assistant message with tool calls
                        # We'll handle this in a more sophisticated way if needed
                        pass
        
        return messages
    
    def _generate_task_id(self) -> str:
        """Generate a unique task ID."""
        return generate_short_id()
    
    def _generate_step_id(self) -> str:
        """Generate a unique step ID."""
        timestamp = int(datetime.now().timestamp() * 1000)
        return f"{self.task.task_id}_{len(self.task.history) + 1}_{timestamp}"
    


    def _setup_workspace(self) -> None:
        """Set up workspace directory structure."""
        try:
            # Create subdirectories
            (self.task.workspace_dir / "artifacts").mkdir(exist_ok=True)
            (self.task.workspace_dir / "logs").mkdir(exist_ok=True)
            (self.task.workspace_dir / "history").mkdir(exist_ok=True)
            
            # Set up logging for this task
            self._setup_task_logging()
            
        except Exception as e:
            logger.warning(f"Failed to setup workspace: {e}")
    
    def _setup_task_logging(self) -> None:
        """Set up task-specific logging."""
        try:
            import logging
            
            # Create task-specific logger
            task_logger = logging.getLogger(f"agentx.task.{self.task.task_id}")
            task_logger.setLevel(logging.INFO)
            
            # Create file handler for task logs
            log_file = self.task.workspace_dir / "logs" / "task.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            
            # Add handler to logger
            if not task_logger.handlers:
                task_logger.addHandler(file_handler)
            
            # Log task initialization
            task_logger.info(f"Task {self.task.task_id} initialized")
            
        except Exception as e:
            logger.warning(f"Failed to setup task logging: {e}")
    
    async def _save_state_async(self) -> None:
        """Save task state and conversation history to workspace using storage layer."""
        try:
            if not hasattr(self, 'workspace_storage'):
                logger.warning("Workspace storage not initialized, skipping state save")
                return
                
            # Save task state
            state = {
                "task_id": self.task.task_id,
                "initial_prompt": self.task.initial_prompt,
                "current_agent": self.task.current_agent,
                "round_count": self.task.round_count,
                "is_complete": self.task.is_complete,
                "is_paused": self.task.is_paused,
                "created_at": self.task.created_at.isoformat(),
                "artifacts": self.task.artifacts,
                "history_length": len(self.task.history)
            }
            
            await self.workspace_storage.file_storage.write_text(
                "task_state.json", 
                json.dumps(state, indent=2)
            )
            
            # Save conversation history
            await self._save_conversation_history_async()
            
        except Exception as e:
            logger.warning(f"Failed to save task state: {e}")
    
    async def _save_conversation_history_async(self) -> None:
        """Save conversation history to JSONL file using storage layer."""
        try:
            # Prepare conversation history data
            history_lines = []
            for step in self.task.history:
                step_data = {
                    "step_id": step.step_id,
                    "agent_name": step.agent_name,
                    "timestamp": step.timestamp.isoformat(),
                    "parts": []
                }
                
                for part in step.parts:
                    if hasattr(part, 'text'):
                        step_data["parts"].append({
                            "type": "text",
                            "content": part.text
                        })
                    elif isinstance(part, ToolCallPart):
                        step_data["parts"].append({
                            "type": "tool_call",
                            "tool_call_id": part.tool_call_id,
                            "tool_name": part.tool_name,
                            "arguments": part.args
                        })
                    elif hasattr(part, 'tool_result'):
                        step_data["parts"].append({
                            "type": "tool_result",
                            "result": part.tool_result.result,
                            "success": part.tool_result.success
                        })
                
                history_lines.append(json.dumps(step_data))
            
            # Write to storage
            await self.workspace_storage.file_storage.write_text(
                "history/conversation.jsonl",
                '\n'.join(history_lines) + '\n'
            )
                    
        except Exception as e:
            logger.warning(f"Failed to save conversation history: {e}")

    def setup_storage_tools(self):
        """Setup storage tools for the task."""
        if not self.workspace_storage:
            return
        
        try:
            from ..builtin_tools.storage_tools import create_storage_tools
            storage_tools = create_storage_tools(self.workspace_storage)
            for tool in storage_tools:
                register_tool(tool)
            
            logger.debug(f"Registered {len(storage_tools)} storage tools")
        except ImportError as e:
            logger.warning(f"Failed to import storage tools: {e}")


async def execute_task(prompt: str, config_path: str, initial_agent: str = None, stream: bool = False):
    """
    Execute a task to completion (one-shot execution).
    
    Args:
        prompt: Initial task prompt
        config_path: Path to team configuration file
        initial_agent: Optional initial agent name
        stream: Whether to stream responses
    
    Yields:
        Stream chunks if stream=True, or completes silently if stream=False
    """
    task_executor = TaskExecutor(config_path)
    
    if stream:
        async for chunk in task_executor.execute_task(prompt, initial_agent, stream=True):
            yield chunk
    else:
        await task_executor.execute_task(prompt, initial_agent, stream=False)

def start_task(prompt: str, config_path: str, initial_agent: str = None) -> 'TaskExecutor':
    """
    Start a task for step-by-step interactive execution.
    
    Args:
        prompt: Initial task prompt
        config_path: Path to team configuration file  
        initial_agent: Optional initial agent name
    
    Returns:
        TaskExecutor instance ready for step() calls
    """
    task_executor = TaskExecutor(config_path)
    task_executor.start_task(prompt, initial_agent)
    return task_executor