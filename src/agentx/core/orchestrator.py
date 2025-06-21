"""
Central orchestrator for coordination and tool execution.

The orchestrator is the centralized service that provides:
- Intelligent agent routing decisions based on task context and previous responses
- Secure tool execution with validation and dispatch
- Structured error feedback for self-correction
- Tool permissions and security policy management
"""

from typing import Dict, Any, Optional, List
import json

from .brain import Brain
from ..utils.logger import get_logger

logger = get_logger(__name__)


class Orchestrator:
    """
    Orchestrates agent coordination and tool execution in the AgentX framework.
    
    The Orchestrator now handles:
    - Agent routing decisions (both intelligent LLM-based and heuristic fallback)
    - Tool execution coordination
    - Memory-driven context injection for enhanced agent awareness
    - Event-driven memory synthesis
    """
    
    def __init__(
        self, 
        task: 'Task' = None, 
        max_rounds: int = 50, 
        timeout: int = 3600,
        memory_system: Optional['MemorySystem'] = None
    ):
        """
        Initialize orchestrator for task coordination.
        
        Args:
            task: Task instance to orchestrate (optional for standalone routing)
            max_rounds: Maximum execution rounds
            timeout: Task timeout in seconds
            memory_system: Optional memory system instance
        """
        self.task = task
        self.max_rounds = max_rounds
        self.timeout = timeout
        self.memory_system = memory_system
        self.routing_brain = None  # Will be initialized lazily
        
        if task:
            if not task.agents:
                logger.warning(f"Task '{task.task_id}' has no agents configured yet - routing brain will be initialized later")
            
            # Initialize memory system if not provided
            if not self.memory_system:
                self._initialize_memory_system()
                
            logger.info(f"Orchestrator initialized with task '{task.task_id}' (routing brain: deferred, memory: {'enabled' if self.memory_system else 'disabled'})")
        else:
            logger.info("Orchestrator initialized without task (pure routing only)")

    def _initialize_memory_system(self) -> None:
        """Initialize the memory system with synthesis engine."""
        if not self.task:
            return
            
        try:
            from ..memory.factory import create_memory_backend
            # Skip synthesis engine and memory system for now
            
            # Get memory config from task if available
            memory_config = getattr(self.task.team_config, 'memory', None)
            
            if memory_config:
                backend = create_memory_backend(memory_config)
                logger.info("Memory backend initialized")
            
        except Exception as e:
            logger.warning(f"Failed to initialize memory system: {e}")
            self.memory_system = None

    def _ensure_routing_brain(self):
        """Ensure routing brain is initialized when needed."""
        if self.routing_brain is not None:
            return
            
        if not self.task or not self.task.agents:
            raise RuntimeError("Cannot initialize routing brain: no task or agents available")
        
        try:
            orchestrator_config = getattr(self.task.team_config, 'orchestrator', None)
            if orchestrator_config and hasattr(orchestrator_config, 'brain_config'):
                # Use explicit orchestrator brain config if provided
                logger.debug(f"Using explicit orchestrator brain config")
                self.routing_brain = Brain.from_config(orchestrator_config.brain_config)
            else:
                # Use the first agent's brain config for routing decisions
                first_agent = list(self.task.agents.values())[0]
                logger.debug(f"Using first agent '{first_agent.name}' brain config for routing")
                self.routing_brain = Brain.from_config(first_agent.config.brain_config)
            
            # Routing brain is mandatory for teams
            if not self.routing_brain:
                raise RuntimeError(f"Brain.from_config() returned None for task '{self.task.task_id}'")
                
            logger.info(f"Routing brain initialized successfully for task '{self.task.task_id}'")
            
        except Exception as e:
            logger.error(f"Failed to initialize routing brain: {e}")
            raise

    # ============================================================================
    # AGENT ROUTING - Intelligent coordination decisions
    # ============================================================================

    async def get_next_agent(self, context: Dict[str, Any], last_response: str = None) -> str:
        """
        Determine the next agent to execute.
        """
        try:
            return await self._intelligent_agent_selection(context, last_response)
        except Exception as e:
            logger.error(f"Error in get_next_agent: {e}")
            # Fallback to first agent
            return list(self.task.agents.keys())[0] if self.task.agents else "unknown"

    async def decide_next_step(self, context: Dict[str, Any], last_response: str = None) -> Dict[str, Any]:
        """
        Decide the next action using handoff determination.
        """
        # No task: complete immediately
        if not self.task:
            return {
                "action": "COMPLETE",
                "next_agent": context.get("current_agent", "assistant"),
                "reason": "No task configured"
            }
        
        # Single-agent teams: complete after response
        if len(self.task.agents) <= 1:
            return {
                "action": "COMPLETE",
                "next_agent": context.get("current_agent", "assistant"),
                "reason": "Single agent task complete"
            }
        
        # Multi-agent teams: determine handoff
        return await self.determine_handoff(context, last_response)



    async def _intelligent_agent_selection(
        self, 
        context: Dict[str, Any], 
        last_response: str = None
    ) -> str:
        """
        Determine which agent should execute next based on task context and previous response.
        
        Args:
            context: Current task context including history, current agent, available agents
            last_response: The last agent's response (optional for initial selection)
            
        Returns:
            Name of the agent that should execute next
        """
        if not self.task or len(self.task.agents) <= 1:
            # Single agent or no team - return the only/current agent
            if self.task and self.task.agents:
                return list(self.task.agents.keys())[0]
            return context.get("current_agent", "default")
        
        # Use our simplified handoff determination
        routing_decision = await self.determine_handoff(context, last_response)
        
        if routing_decision["action"] == "HANDOFF":
            return routing_decision["next_agent"]
        elif routing_decision["action"] == "CONTINUE":
            return context.get("current_agent")
        else:  # COMPLETE
            # Task is complete, return current agent for final cleanup
            return context.get("current_agent")

    async def determine_handoff(self, context: Dict[str, Any], last_response: str = None) -> Dict[str, Any]:
        """
        Main method to determine handoff decision.
        """
        current_agent = context.get("current_agent")
        
        try:
            # Ensure routing brain is initialized
            self._ensure_routing_brain()
            
            # Get relevant handoffs for current agent
            filtered_handoffs = self._filter_relevant_handoffs(current_agent)
            
            # Build prompt with all necessary context
            prompt = self._build_prompt(current_agent, last_response, filtered_handoffs)
            
            # Get brain decision
            if not self.routing_brain:
                raise RuntimeError("Routing brain is None after initialization attempt")
            
            brain_response = await self.routing_brain.generate_response(
                messages=[{"role": "user", "content": prompt}]
            )
            
            decision = json.loads(brain_response.content)
            return {
                "action": decision.get("action", "CONTINUE"),
                "next_agent": decision.get("next_agent", current_agent),
                "reason": "Brain handoff decision"
            }
            
        except Exception as e:
            logger.error(f"Handoff determination failed: {e}")
            return {
                "action": "CONTINUE",
                "next_agent": current_agent,
                "reason": f"Error fallback: {e}"
            }
    
    def _filter_relevant_handoffs(self, current_agent: str) -> List[str]:
        """
        Filter handoffs relevant to the current agent.
        """
        all_agents = list(self.task.agents.keys())
        
        # For now, return all other agents as potential handoffs
        # This can be enhanced with agent-specific handoff rules
        return [agent for agent in all_agents if agent != current_agent]
    
    def _build_prompt(self, current_agent: str, last_response: str, filtered_handoffs: List[str]) -> str:
        """
        Build prompt with enough context for brain decision.
        """
        all_agents = list(self.task.agents.keys())
        
        prompt = f"""
Current agent: {current_agent}
Last response: "{last_response[:400] if last_response else 'No response'}"

All agents: {all_agents}
Possible handoffs: {filtered_handoffs}

Based on the current agent's response, decide:
- CONTINUE: Keep working with {current_agent}
- HANDOFF: Switch to another agent (specify which one)
- COMPLETE: Task is finished

Return JSON: {{"action": "CONTINUE|HANDOFF|COMPLETE", "next_agent": "agent_name"}}
"""
        return prompt



    def _format_team_info(self) -> str:
        """Format team information for routing prompts."""
        if not self.task:
            return "No team configured"
        
        info = f"Team: {self.task.team_config.name}\n"
        for name, agent in self.task.agents.items():
            info += f"- {name}: {agent.config.description}\n"
        return info






