from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, AsyncGenerator
from datetime import datetime
import asyncio

from .team import Team
from .task_step import TaskStep, TextPart, ToolCallPart, ToolResultPart, ArtifactPart
from .brain import Brain, LLMMessage
from .event import (
    TaskStartEvent, TaskCompleteEvent, TaskPausedEvent, TaskResumedEvent,
    AgentStartEvent, AgentCompleteEvent, AgentHandoffEvent, ToolCallEvent, ToolResultEvent,
    BreakpointHitEvent, UserInterventionEvent, ErrorEvent
)
from .streaming import StreamChunk, StreamError, StreamComplete
from .config import ExecutionMode
from ..utils.id import generate_short_id
from ..event import publish_event


class TaskState:
    """Maintains the current state of a task execution."""
    
    def __init__(self, task_id: str, team: Team, initial_prompt: str, workspace_dir: Path):
        self.task_id = task_id
        self.team = team
        self.initial_prompt = initial_prompt
        self.workspace_dir = workspace_dir
        self.history: List[TaskStep] = []
        self.current_agent: Optional[str] = None
        self.round_count = 0
        self.is_complete = False
        self.is_paused = False
        self.created_at = datetime.now()
        self.artifacts: Dict[str, Any] = {}
        
        # Create workspace directory
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # Save initial state
        self._save_state()
    
    def add_step(self, step: TaskStep) -> None:
        """Add a new step to the history."""
        self.history.append(step)
        self._save_state()
    
    def set_current_agent(self, agent_name: str) -> None:
        """Set the current active agent."""
        self.current_agent = agent_name
        self._save_state()
    
    def increment_round(self) -> None:
        """Increment the round counter."""
        self.round_count += 1
        self._save_state()
    
    def complete_task(self) -> None:
        """Mark the task as complete."""
        self.is_complete = True
        self._save_state()
    
    def pause_task(self) -> None:
        """Pause the task execution."""
        self.is_paused = True
        self._save_state()
    
    def resume_task(self) -> None:
        """Resume the task execution."""
        self.is_paused = False
        self._save_state()
    
    def add_artifact(self, name: str, content: Any, metadata: Dict[str, Any] = None) -> None:
        """Add an artifact to the task state."""
        self.artifacts[name] = {
            'content': content,
            'metadata': metadata or {},
            'created_at': datetime.now().isoformat()
        }
        self._save_state()
    
    def _save_state(self) -> None:
        """Save the current state to disk."""
        state_file = self.workspace_dir / "task_state.json"
        
        # Convert history to serializable format
        history_data = []
        for step in self.history:
            step_dict = step.model_dump()
            # Convert datetime to ISO string
            if 'timestamp' in step_dict and step_dict['timestamp']:
                step_dict['timestamp'] = step_dict['timestamp'].isoformat() if hasattr(step_dict['timestamp'], 'isoformat') else step_dict['timestamp']
            history_data.append(step_dict)
        
        state_data = {
            'task_id': self.task_id,
            'team_name': self.team.name,
            'initial_prompt': self.initial_prompt,
            'current_agent': self.current_agent,
            'round_count': self.round_count,
            'is_complete': self.is_complete,
            'is_paused': self.is_paused,
            'created_at': self.created_at.isoformat(),
            'history': history_data,
            'artifacts': self.artifacts
        }
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_state(cls, workspace_dir: Path, team: Team) -> "TaskState":
        """Load task state from disk."""
        state_file = workspace_dir / "task_state.json"
        
        if not state_file.exists():
            raise FileNotFoundError(f"Task state file not found: {state_file}")
        
        with open(state_file, 'r', encoding='utf-8') as f:
            state_data = json.load(f)
        
        # Create instance
        instance = cls.__new__(cls)
        instance.task_id = state_data['task_id']
        instance.team = team
        instance.initial_prompt = state_data['initial_prompt']
        instance.workspace_dir = workspace_dir
        instance.current_agent = state_data['current_agent']
        instance.round_count = state_data['round_count']
        instance.is_complete = state_data['is_complete']
        instance.is_paused = state_data['is_paused']
        instance.created_at = datetime.fromisoformat(state_data['created_at'])
        instance.artifacts = state_data.get('artifacts', {})
        
        # Reconstruct history
        instance.history = []
        for step_data in state_data.get('history', []):
            step = TaskStep(**step_data)
            instance.history.append(step)
        
        return instance


class Orchestrator:
    """
    The central controller for task execution. Manages the flow of collaboration
    between agents, handles tool execution, and maintains task state.
    """
    
    def __init__(self, team: Team, workspace_dir: Path = None):
        self.team = team
        self.workspace_dir = workspace_dir or Path.cwd() / "agentx_workspace"
        self.active_tasks: Dict[str, TaskState] = {}
    
    async def start_task(
        self,
        prompt: str,
        initial_agent: str = None,
        execution_mode: ExecutionMode = ExecutionMode.AUTONOMOUS,
        task_id: str = None
    ) -> str:
        """
        Start a new task execution.
        
        Args:
            prompt: The initial task prompt
            initial_agent: Name of the agent to start with (defaults to first agent)
            execution_mode: Execution mode (autonomous or step-through)
            task_id: Optional task ID (generated if not provided)
            
        Returns:
            Task ID for tracking the execution
        """
        # Generate task ID if not provided
        if task_id is None:
            task_id = generate_short_id()
        
        # Determine initial agent
        if initial_agent is None:
            initial_agent = list(self.team.agents.keys())[0]
        
        if initial_agent not in self.team.agents:
            raise ValueError(f"Initial agent '{initial_agent}' not found in team")
        
        # Create task workspace
        task_workspace = self.workspace_dir / task_id
        
        # Create task state
        task_state = TaskState(task_id, self.team, prompt, task_workspace)
        task_state.set_current_agent(initial_agent)
        
        # Store active task
        self.active_tasks[task_id] = task_state
        
        return task_id
    
    async def execute_task(
        self,
        task_id: str
    ) -> TaskState:
        """
        Execute a task to completion or until paused.
        
        Args:
            task_id: ID of the task to execute
            
        Returns:
            Final task state
        """
        if task_id not in self.active_tasks:
            raise ValueError(f"Task not found: {task_id}")
        
        task_state = self.active_tasks[task_id]
        
        # Emit task started event
        await publish_event(
            TaskStartEvent(
                task_id=task_id,
                timestamp=datetime.now(),
                initial_prompt=task_state.initial_prompt,
                execution_mode="autonomous",
                team_config=self.team.to_dict()
            ),
            source="orchestrator",
            correlation_id=task_id
        )
        
        try:
            # Main execution loop
            while not task_state.is_complete and not task_state.is_paused:
                # Check round limit
                if task_state.round_count >= self.team.max_rounds:
                    break
                
                # Execute current agent turn
                await self._execute_agent_turn(task_state)
                
                # Increment round counter
                task_state.increment_round()
            
            # Mark as complete if not paused
            if not task_state.is_paused:
                task_state.complete_task()
                
                await publish_event(
                    TaskCompleteEvent(
                        task_id=task_id,
                        timestamp=datetime.now(),
                        final_status="success",
                        total_steps=len(task_state.history),
                        total_duration_ms=int((datetime.now() - task_state.created_at).total_seconds() * 1000),
                        artifacts_created=list(task_state.artifacts.keys())
                    ),
                    source="orchestrator",
                    correlation_id=task_id
                )
        
        except Exception as e:
            await publish_event(
                ErrorEvent(
                    error_id=generate_short_id(),
                    error_type="execution_error",
                    error_message=str(e),
                    context={"task_id": task_id, "current_agent": task_state.current_agent},
                    timestamp=datetime.now(),
                    recoverable=False
                ),
                source="orchestrator",
                correlation_id=task_id
            )
            raise
        
        return task_state
    
    async def execute_task_streaming(
        self,
        task_id: str
    ):
        """
        Execute a task with streaming responses.
        
        Args:
            task_id: ID of the task to execute
            
        Yields:
            Dict containing streaming updates with agent responses
        """
        if task_id not in self.active_tasks:
            raise ValueError(f"Task not found: {task_id}")

        task_state = self.active_tasks[task_id]
        
        # Emit task started event
        await publish_event(
            TaskStartEvent(
                task_id=task_id,
                timestamp=datetime.now(),
                initial_prompt=task_state.initial_prompt,
                execution_mode="streaming",
                team_config=self.team.to_dict()
            ),
            source="orchestrator",
            correlation_id=task_id
        )
        
        try:
            # Main execution loop
            while not task_state.is_complete and not task_state.is_paused:
                # Check round limit
                if task_state.round_count >= self.team.max_rounds:
                    break
                
                # Execute current agent turn with streaming
                async for chunk in self._execute_agent_turn_streaming(task_state):
                    yield chunk
                
                # Increment round counter
                task_state.increment_round()
            
            # Mark as complete if not paused
            if not task_state.is_paused:
                task_state.complete_task()
                
                await publish_event(
                    TaskCompleteEvent(
                        task_id=task_id,
                        timestamp=datetime.now(),
                        final_status="success",
                        total_steps=len(task_state.history),
                        total_duration_ms=int((datetime.now() - task_state.created_at).total_seconds() * 1000),
                        artifacts_created=list(task_state.artifacts.keys())
                    ),
                    source="orchestrator",
                    correlation_id=task_id
                )
                
                # Yield completion signal
                yield {
                    "type": "task_complete",
                    "task_id": task_id,
                    "status": "success",
                    "total_steps": len(task_state.history)
                }
        
        except Exception as e:
            await publish_event(
                ErrorEvent(
                    error_id=generate_short_id(),
                    error_type="execution_error",
                    error_message=str(e),
                    context={"task_id": task_id, "current_agent": task_state.current_agent},
                    timestamp=datetime.now(),
                    recoverable=False
                ),
                source="orchestrator",
                correlation_id=task_id
            )
            
            # Yield error signal
            yield {
                "type": "error",
                "task_id": task_id,
                "error": str(e)
            }
            raise
    
    async def _execute_agent_turn_streaming(
        self,
        task_state: TaskState
    ):
        """Execute a single agent turn with streaming."""
        current_agent = task_state.current_agent
        step_id = generate_short_id()
        
        # Yield agent start signal
        yield {
            "type": "agent_start",
            "agent_name": current_agent,
            "step_id": step_id,
            "timestamp": datetime.now().isoformat()
        }
        
        await publish_event(
            AgentStartEvent(
                agent_name=current_agent,
                step_id=step_id,
                timestamp=datetime.now()
            ),
            source=f"agent:{current_agent}",
            correlation_id=task_state.task_id
        )
        
        # Get agent configuration
        agent_config = self.team.get_agent(current_agent)
        if not agent_config:
            raise ValueError(f"Agent not found: {current_agent}")
        
        # Prepare context for prompt rendering
        context = {
            'task_prompt': task_state.initial_prompt,
            'history': task_state.history,
            'available_tools': self.team.get_agent_tools(current_agent),
            'handoff_targets': self.team.get_handoff_targets(current_agent),
            'artifacts': task_state.artifacts
        }
        
        # Render agent prompt
        system_prompt = self.team.render_agent_prompt(current_agent, context)
        
        # Get agent's LLM configuration or use default
        agent_llm_config = agent_config.llm_config
        if agent_llm_config is None:
            # Use default LLM configuration
            from .config import LLMConfig
            agent_llm_config = LLMConfig()
        
        # Create Brain instance with agent's LLM configuration
        brain = Brain(agent_llm_config)
        
        # Prepare conversation messages
        messages = []
        
        # Smart conversation flow detection
        is_single_agent_chat = len(self.team.agents) == 1
        
        if is_single_agent_chat:
            # For single-agent chat, only include the initial user message
            messages.append(LLMMessage(
                role="user",
                content=task_state.initial_prompt,
                timestamp=datetime.now()
            ))
        else:
            # Multi-agent conversation: include full history with proper role assignment
            messages.append(LLMMessage(
                role="user",
                content=task_state.initial_prompt,
                timestamp=datetime.now()
            ))
            
            # Add conversation history
            for step in task_state.history:
                for part in step.parts:
                    if isinstance(part, TextPart):
                        # Determine role based on agent
                        role = "assistant" if step.agent_name == current_agent else "user"
                        messages.append(LLMMessage(
                            role=role,
                            content=part.text,
                            timestamp=step.timestamp
                        ))
        
        try:
            # Stream response using Brain
            response_chunks = []
            async for chunk in brain.stream_response(
                messages=messages,
                system_prompt=system_prompt
            ):
                response_chunks.append(chunk)
                
                # Yield streaming chunk
                yield {
                    "type": "response_chunk",
                    "agent_name": current_agent,
                    "step_id": step_id,
                    "chunk": chunk,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Combine all chunks for final response
            response_text = "".join(response_chunks)
            
        except Exception as e:
            # Fallback response on error
            response_text = f"I apologize, but I encountered an error while processing your request: {str(e)}"
            
            # Yield error chunk
            yield {
                "type": "response_chunk",
                "agent_name": current_agent,
                "step_id": step_id,
                "chunk": response_text,
                "timestamp": datetime.now().isoformat(),
                "error": True
            }
        
        # Check for handoff requests in the response
        handoff_target = self._detect_handoff_request(response_text)
        if handoff_target:
            # Process handoff
            await self._process_handoff(task_state, current_agent, handoff_target, response_text)
            
            # Yield handoff signal
            yield {
                "type": "handoff",
                "from_agent": current_agent,
                "to_agent": handoff_target,
                "step_id": step_id,
                "timestamp": datetime.now().isoformat()
            }
            return
        
        # Create task step
        step = TaskStep(
            step_id=step_id,
            agent_name=current_agent,
            parts=[TextPart(text=response_text)],
            timestamp=datetime.now()
        )
        
        # Add step to history
        task_state.add_step(step)
        
        # Smart completion: For single-agent chats, complete after first response
        is_single_agent_chat = len(self.team.agents) == 1
        if is_single_agent_chat and len(task_state.history) >= 1:
            task_state.complete_task()
        
        await publish_event(
            AgentCompleteEvent(
                agent_name=current_agent,
                step_id=step_id,
                timestamp=datetime.now()
            ),
            source=f"agent:{current_agent}",
            correlation_id=task_state.task_id
        )
        
        # Yield agent complete signal
        yield {
            "type": "agent_complete",
            "agent_name": current_agent,
            "step_id": step_id,
            "response_length": len(response_text),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_agent_turn(
        self,
        task_state: TaskState
    ) -> None:
        """Execute a single agent turn."""
        current_agent = task_state.current_agent
        step_id = generate_short_id()
        
        await publish_event(
            AgentStartEvent(
                agent_name=current_agent,
                step_id=step_id,
                timestamp=datetime.now()
            ),
            source=f"agent:{current_agent}",
            correlation_id=task_state.task_id
        )
        
        # Get agent configuration
        agent_config = self.team.get_agent(current_agent)
        if not agent_config:
            raise ValueError(f"Agent not found: {current_agent}")
        
        # Prepare context for prompt rendering
        context = {
            'task_prompt': task_state.initial_prompt,
            'history': task_state.history,
            'available_tools': self.team.get_agent_tools(current_agent),
            'handoff_targets': self.team.get_handoff_targets(current_agent),
            'artifacts': task_state.artifacts
        }
        
        # Render agent prompt
        system_prompt = self.team.render_agent_prompt(current_agent, context)
        
        # Get agent's LLM configuration or use default
        agent_llm_config = agent_config.llm_config
        if agent_llm_config is None:
            # Use default LLM configuration
            from .config import LLMConfig
            agent_llm_config = LLMConfig()
        
        # Create Brain instance with agent's LLM configuration
        brain = Brain(agent_llm_config)
        
        # Prepare conversation messages
        messages = []
        
        # Smart conversation flow detection
        is_single_agent_chat = len(self.team.agents) == 1
        
        if is_single_agent_chat:
            # For single-agent chat, only include the initial user message
            # Don't include agent's own responses in history to avoid self-conversation
            messages.append(LLMMessage(
                role="user",
                content=task_state.initial_prompt,
                timestamp=datetime.now()
            ))
            
            # In single-agent mode, we should complete after one response
            # The agent should not see its own previous responses
            
        else:
            # Multi-agent conversation: include full history with proper role assignment
            messages.append(LLMMessage(
                role="user",
                content=task_state.initial_prompt,
                timestamp=datetime.now()
            ))
            
            # Add conversation history
            for step in task_state.history:
                for part in step.parts:
                    if isinstance(part, TextPart):
                        # Determine role based on agent
                        role = "assistant" if step.agent_name == current_agent else "user"
                        messages.append(LLMMessage(
                            role=role,
                            content=part.text,
                            timestamp=step.timestamp
                        ))
        
        try:
            # Generate response using Brain
            response = await brain.generate_response(
                messages=messages,
                system_prompt=system_prompt,
                available_tools=agent_config.tools
            )
            
            response_text = response.content
            
        except Exception as e:
            # Fallback response on error
            response_text = f"I apologize, but I encountered an error while processing your request: {str(e)}"
        
        # Check for handoff requests in the response
        handoff_target = self._detect_handoff_request(response_text)
        if handoff_target:
            # Process handoff
            await self._process_handoff(task_state, current_agent, handoff_target, response_text)
            return
        
        # Create task step
        step = TaskStep(
            step_id=step_id,
            agent_name=current_agent,
            parts=[TextPart(text=response_text)],
            timestamp=datetime.now()
        )
        
        # Add step to history
        task_state.add_step(step)
        
        # Smart completion: For single-agent chats, complete after first response
        is_single_agent_chat = len(self.team.agents) == 1
        if is_single_agent_chat and len(task_state.history) >= 1:
            task_state.complete_task()
        
        await publish_event(
            AgentCompleteEvent(
                agent_name=current_agent,
                step_id=step_id,
                timestamp=datetime.now()
            ),
            source=f"agent:{current_agent}",
            correlation_id=task_state.task_id
        )
    
    async def pause_task(self, task_id: str) -> None:
        """Pause a running task."""
        if task_id not in self.active_tasks:
            raise ValueError(f"Task not found: {task_id}")
        
        task_state = self.active_tasks[task_id]
        task_state.pause_task()
        
        await publish_event(
            TaskPausedEvent(
                task_id=task_id,
                timestamp=datetime.now(),
                reason="user_request"
            ),
            source="orchestrator",
            correlation_id=task_id
        )
    
    async def resume_task(self, task_id: str) -> None:
        """Resume a paused task."""
        if task_id not in self.active_tasks:
            raise ValueError(f"Task not found: {task_id}")
        
        task_state = self.active_tasks[task_id]
        task_state.resume_task()
        
        await publish_event(
            TaskResumedEvent(
                task_id=task_id,
                timestamp=datetime.now(),
                reason="user_request"
            ),
            source="orchestrator",
            correlation_id=task_id
        )
    
    def get_task_state(self, task_id: str) -> Optional[TaskState]:
        """Get the current state of a task."""
        return self.active_tasks.get(task_id)
    
    def list_active_tasks(self) -> List[str]:
        """Get list of active task IDs."""
        return list(self.active_tasks.keys())
    
    async def load_task(self, workspace_dir: Path) -> str:
        """Load a task from a workspace directory."""
        task_state = TaskState.load_state(workspace_dir, self.team)
        self.active_tasks[task_state.task_id] = task_state
        return task_state.task_id 