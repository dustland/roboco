"""
Task execution class - the primary interface for AgentX task execution.

Clean API:
    # One-shot execution
    task = create_task(config_path)
    await task.execute_task(prompt)
    
    # Step-by-step execution
    task = create_task(config_path)
    task.start_task(prompt)
    while not task.is_complete:
        await task.step()
"""

import asyncio
import json
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List

from .team import Team
from .agent import Agent
from .message import TaskStep, TextPart, ToolCallPart, ToolResultPart
from .brain import LLMMessage
from ..event.api import publish_event
from .event import (
    TaskStartEvent, TaskCompleteEvent, ErrorEvent,
    AgentStartEvent, AgentCompleteEvent, AgentHandoffEvent
)
from ..utils.logger import get_logger
from ..storage.workspace import WorkspaceStorage
from .tool import execute_tool, ToolResult

logger = get_logger(__name__)


class Task:
    """
    Primary interface for AgentX task execution.
    
    One-shot execution:
        task = create_task(config_path)
        await task.execute_task(prompt)
        
    Step-by-step execution:
        task = create_task(config_path)
        task.start_task(prompt)
        while not task.is_complete:
            await task.step()
    """
    
    def __init__(self, team: Team, task_id: str = None, workspace_dir: Path = None):
        """Initialize task with team configuration."""
        self.team = team
        self.task_id = task_id or self._generate_task_id()
        self.workspace_dir = workspace_dir or Path("./workspace") / self.task_id
        
        # Create internal orchestrator for routing decisions
        from .orchestrator import Orchestrator, RoutingAction
        self._orchestrator = Orchestrator(team)
        self._RoutingAction = RoutingAction
        
        # Task state
        self.initial_prompt: Optional[str] = None
        self.history: List[TaskStep] = []
        self.current_agent: Optional[str] = None
        self.round_count = 0
        self.is_complete = False
        self.is_paused = False
        self.created_at = datetime.now()
        self.artifacts: Dict[str, Any] = {}
        
        # Create workspace directory and subdirectories
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self._setup_workspace()
        
        # Register task-specific tools with this workspace
        self._register_task_tools()
        
        logger.info(f"🎯 Task {self.task_id} initialized")
    
    def start_task(self, prompt: str, initial_agent: str = None) -> None:
        """Start task for step-by-step execution."""
        self._initialize_task(prompt, initial_agent)
        logger.info(f"🚀 Task started for step-by-step execution")
    
    async def execute_task(self, prompt: str, initial_agent: str = None, stream: bool = False):
        """Execute task to completion (one-shot)."""
        self._initialize_task(prompt, initial_agent)
        logger.info(f"🚀 Task started for one-shot execution")
        
        if stream:
            async for chunk in self._stream_execute():
                yield chunk
        else:
            await self._execute()
    
    async def step(self, user_input: str = None, stream: bool = False):
        """Execute one step (for step-by-step execution)."""
        if not self.initial_prompt:
            raise ValueError("Task not started. Call start_task() first.")
        
        if stream:
            async for chunk in self._stream_step(user_input):
                yield chunk
        else:
            result = await self._step(user_input)
            yield result
    
    def _initialize_task(self, prompt: str, initial_agent: str = None) -> None:
        """Initialize task with prompt and agent."""
        self.initial_prompt = prompt
        self.is_paused = False
        self.is_complete = False
        
        # Set initial agent
        if initial_agent:
            self.current_agent = initial_agent
        elif hasattr(self.team.config.execution, 'initial_agent') and self.team.config.execution.initial_agent:
            self.current_agent = self.team.config.execution.initial_agent
        else:
            self.current_agent = list(self.team.agents.keys())[0]
        
        asyncio.create_task(self._save_state_async())

    async def _execute(self) -> None:
        """Execute the task without streaming."""
        while not self.is_complete and self.round_count < self._orchestrator.max_rounds:
            if self.is_paused:
                break
                
            self.round_count += 1
            response = await self._execute_agent_turn()
            
            routing_decision = await self._orchestrator.decide_next_step(
                current_agent=self.current_agent,
                response=response,
                task_context=self._get_task_context()
            )
            
            if routing_decision.action == self._RoutingAction.COMPLETE:
                self.complete_task()
                break
            elif routing_decision.action == self._RoutingAction.HANDOFF:
                self.set_current_agent(routing_decision.next_agent)
    
    async def _stream_execute(self):
        """Execute the task with streaming."""
        while not self.is_complete and self.round_count < self._orchestrator.max_rounds:
            if self.is_paused:
                break
                
            self.round_count += 1
            
            # Stream current agent turn
            response_chunks = []
            async for chunk in self._stream_agent_turn():
                response_chunks.append(chunk)
                yield chunk
            
            # Get routing decision
            full_response = "".join(chunk.get("content", "") for chunk in response_chunks if chunk.get("type") == "content")
            routing_decision = await self._orchestrator.decide_next_step(
                current_agent=self.current_agent,
                response=full_response,
                task_context=self._get_task_context()
            )
            
            # Yield routing decision
            yield {
                "type": "routing_decision",
                "action": routing_decision.action.value,
                "current_agent": self.current_agent,
                "next_agent": routing_decision.next_agent,
                "reason": routing_decision.reason
            }
            
            if routing_decision.action == self._RoutingAction.COMPLETE:
                self.complete_task()
                break
            elif routing_decision.action == self._RoutingAction.HANDOFF:
                old_agent = self.current_agent
                self.set_current_agent(routing_decision.next_agent)
                yield {
                    "type": "handoff",
                    "from_agent": old_agent,
                    "to_agent": routing_decision.next_agent
                }

    async def _step(self, user_input: str = None) -> Dict[str, Any]:
        """Execute one turn without streaming."""
        if self.is_complete:
            return {"status": "complete", "message": "Task already complete"}
        
        if self.round_count >= self._orchestrator.max_rounds:
            self.complete_task()
            return {"status": "complete", "message": "Max rounds reached"}
        
        self.round_count += 1
        
        # Add user input to history if provided
        if user_input:
            user_step = TaskStep(
                step_id=self._generate_step_id(),
                agent_name="user",
                parts=[TextPart(text=user_input)],
                timestamp=datetime.now()
            )
            self.add_step(user_step)
        
        # Execute current agent turn
        response = await self._execute_agent_turn()
        
        # Get routing decision
        routing_decision = await self._orchestrator.decide_next_step(
            current_agent=self.current_agent,
            response=response,
            task_context=self._get_task_context()
        )
        
        result = {
            "status": "continue",
            "agent": self.current_agent,
            "response": response,
            "routing_action": routing_decision.action.value,
            "next_agent": routing_decision.next_agent,
            "reason": routing_decision.reason,
            "round": self.round_count
        }
        
        if routing_decision.action == self._RoutingAction.COMPLETE:
            self.complete_task()
            result["status"] = "complete"
        elif routing_decision.action == self._RoutingAction.HANDOFF:
            old_agent = self.current_agent
            self.set_current_agent(routing_decision.next_agent)
            result["handoff"] = {"from": old_agent, "to": routing_decision.next_agent}
        
        return result
    
    async def _stream_step(self, user_input: str = None):
        """Execute one turn with streaming."""
        if self.is_complete:
            yield {"status": "complete", "message": "Task already complete"}
            return
        
        if self.round_count >= self._orchestrator.max_rounds:
            self.complete_task()
            yield {"status": "complete", "message": "Max rounds reached"}
            return
        
        self.round_count += 1
        
        # Add user input to history if provided
        if user_input:
            user_step = TaskStep(
                step_id=self._generate_step_id(),
                agent_name="user",
                parts=[TextPart(text=user_input)],
                timestamp=datetime.now()
            )
            self.add_step(user_step)
        
        # Stream the agent turn
        response_chunks = []
        async for chunk in self._stream_agent_turn():
            response_chunks.append(chunk)
            yield chunk
        
        # Get routing decision
        full_response = "".join(chunk.get("content", "") for chunk in response_chunks if chunk.get("type") == "content")
        routing_decision = await self._orchestrator.decide_next_step(
            current_agent=self.current_agent,
            response=full_response,
            task_context=self._get_task_context()
        )
        
        # Yield routing decision
        yield {
            "type": "routing_decision",
            "action": routing_decision.action.value,
            "current_agent": self.current_agent,
            "next_agent": routing_decision.next_agent,
            "reason": routing_decision.reason
        }
        
        if routing_decision.action == self._RoutingAction.COMPLETE:
            self.complete_task()
        elif routing_decision.action == self._RoutingAction.HANDOFF:
            old_agent = self.current_agent
            self.set_current_agent(routing_decision.next_agent)
            yield {
                "type": "handoff",
                "from_agent": old_agent,
                "to_agent": routing_decision.next_agent
            }
    
    async def _execute_agent_turn(self) -> str:
        """
        Execute a full agent turn using orchestrator's agent routing.
        """
        context = self._prepare_agent_context()
        
        # Convert task history to conversation format
        conversation_messages = self._convert_history_to_messages()
        
        # Build system prompt for agent
        agent = self.team.get_agent(self.current_agent)
        system_prompt = agent.build_system_prompt(context)
        
        # Use orchestrator to route to agent - orchestrator handles tool execution
        final_response = await self._orchestrator.route_to_agent(
            agent_name=self.current_agent,
            messages=conversation_messages,
            system_prompt=system_prompt
        )
        
        # Add final response to task history
        self.add_step(TaskStep(
            agent_name=self.current_agent, 
            parts=[TextPart(text=final_response)]
        ))
        
        return final_response

    async def _stream_agent_turn(self):
        """
        Execute a full agent turn with streaming using orchestrator's agent routing.
        """
        context = self._prepare_agent_context()
        
        # Convert task history to conversation format
        conversation_messages = self._convert_history_to_messages()
        
        # Build system prompt for agent
        agent = self.team.get_agent(self.current_agent)
        system_prompt = agent.build_system_prompt(context)
        
        # Use orchestrator to stream from agent - orchestrator handles tool execution
        response_chunks = []
        async for chunk in self._orchestrator.stream_from_agent(
            agent_name=self.current_agent,
            messages=conversation_messages,
            system_prompt=system_prompt
        ):
            yield {"type": "content", "content": chunk}
            response_chunks.append(chunk)
        
        # Add final response to task history
        final_response = "".join(response_chunks)
        if final_response:
            self.add_step(TaskStep(
                agent_name=self.current_agent, 
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

    def _prepare_agent_context(self) -> Dict[str, Any]:
        """Prepare context for agent execution."""
        return {
            "task_id": self.task_id,
            "round_count": self.round_count,
            "workspace_dir": str(self.workspace_dir),
            "artifacts": self.artifacts
        }
    
    def _get_task_context(self) -> Dict[str, Any]:
        """Get current task context for routing decisions."""
        return {
            "task_id": self.task_id,
            "initial_prompt": self.initial_prompt,
            "round_count": self.round_count,
            "total_steps": len(self.history),
            "is_complete": self.is_complete,
            "current_agent": self.current_agent,
            "available_agents": list(self.team.agents.keys())
        }
    
    def _convert_history_to_messages(self) -> List[Dict[str, Any]]:
        """Convert task history to conversation message format for orchestrator."""
        messages = []
        
        for step in self.history:
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
        from ..utils.id import generate_short_id
        return generate_short_id()
    
    def _generate_step_id(self) -> str:
        """Generate a unique step ID."""
        return f"{self.task_id}_{len(self.history) + 1}_{int(time.time() * 1000)}"
    
    def add_step(self, step: TaskStep) -> None:
        """Add a step to the conversation history."""
        self.history.append(step)
        asyncio.create_task(self._save_state_async())
    
    def set_current_agent(self, agent_name: str) -> None:
        """Set the current active agent."""
        self.current_agent = agent_name
        asyncio.create_task(self._save_state_async())
    
    def complete_task(self) -> None:
        """Mark the task as complete."""
        self.is_complete = True
        asyncio.create_task(self._save_state_async())
        logger.info(f"✅ Task completed after {self.round_count} rounds")
    
    def pause_task(self) -> None:
        """Pause the task execution."""
        self.is_paused = True
        asyncio.create_task(self._save_state_async())
    
    def resume_task(self) -> None:
        """Resume the task execution."""
        self.is_paused = False
        asyncio.create_task(self._save_state_async())
    
    def add_artifact(self, name: str, content: Any, metadata: Dict[str, Any] = None) -> None:
        """Add an artifact to the task."""
        self.artifacts[name] = {
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat()
        }
        asyncio.create_task(self._save_state_async())
    
    def _setup_workspace(self) -> None:
        """Set up workspace directory structure."""
        try:
            # Create subdirectories
            (self.workspace_dir / "artifacts").mkdir(exist_ok=True)
            (self.workspace_dir / "logs").mkdir(exist_ok=True)
            (self.workspace_dir / "history").mkdir(exist_ok=True)
            
            # Set up logging for this task
            self._setup_task_logging()
            
        except Exception as e:
            logger.warning(f"Failed to setup workspace: {e}")
    
    def _setup_task_logging(self) -> None:
        """Set up task-specific logging."""
        try:
            import logging
            
            # Create task-specific logger
            task_logger = logging.getLogger(f"agentx.task.{self.task_id}")
            task_logger.setLevel(logging.INFO)
            
            # Create file handler for task logs
            log_file = self.workspace_dir / "logs" / "task.log"
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
            task_logger.info(f"Task {self.task_id} initialized")
            
        except Exception as e:
            logger.warning(f"Failed to setup task logging: {e}")
    
    def _register_task_tools(self) -> None:
        """Register task-specific tools with this task's workspace."""
        try:
            from ..storage.factory import StorageFactory
            from ..builtin_tools.storage_tools import create_storage_tools
            from ..core.tool import register_tool
            
            # Create workspace storage for this task
            self.workspace_storage = StorageFactory.create_workspace_storage(
                self.workspace_dir, 
                use_git_artifacts=True
            )
            
            # Create and register storage tools
            storage_tool, artifact_tool = create_storage_tools(str(self.workspace_dir))
            
            register_tool(storage_tool)
            register_tool(artifact_tool)
            
            # Also register other built-in tools (context, planning, etc.)
            from ..builtin_tools import register_builtin_tools
            register_builtin_tools(workspace_path=str(self.workspace_dir))
            
            logger.info(f"Registered task-specific storage tools for workspace: {self.workspace_dir}")
            
        except Exception as e:
            logger.warning(f"Failed to register task tools: {e}")
    
    async def _save_state_async(self) -> None:
        """Save task state and conversation history to workspace using storage layer."""
        try:
            if not hasattr(self, 'workspace_storage'):
                logger.warning("Workspace storage not initialized, skipping state save")
                return
                
            # Save task state
            state = {
                "task_id": self.task_id,
                "initial_prompt": self.initial_prompt,
                "current_agent": self.current_agent,
                "round_count": self.round_count,
                "is_complete": self.is_complete,
                "is_paused": self.is_paused,
                "created_at": self.created_at.isoformat(),
                "artifacts": self.artifacts,
                "history_length": len(self.history)
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
            for step in self.history:
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
                    elif hasattr(part, 'tool_call'):
                        step_data["parts"].append({
                            "type": "tool_call",
                            "tool_name": part.tool_call.tool_name,
                            "arguments": part.tool_call.arguments
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


# Factory function for creating tasks
def create_task(team_config_path: str, task_id: str = None, workspace_dir: Path = None) -> Task:
    """
    Create a new task from team configuration.
    
    Args:
        team_config_path: Path to team configuration file
        task_id: Optional task ID (auto-generated if not provided)
        workspace_dir: Optional workspace directory (auto-generated if not provided)
    
    Returns:
        Task instance ready to be started
    """
    team = Team.from_config(team_config_path)
    return Task(team, task_id, workspace_dir)

async def execute_task(prompt: str, config_path: str = None, stream: bool = False):
    """
    A convenience function to create and run a task in one call.

    This is a "fire-and-forget" method for autonomous runs.
    """
    task = create_task(prompt, config_path)
    async for update in task.run(stream=stream):
        yield update

async def start_task(prompt: str, config_path: str = None):
    """
    A convenience function to create and start a task for interactive sessions.
    """
    task = create_task(prompt, config_path)
    await task.start()
    return task