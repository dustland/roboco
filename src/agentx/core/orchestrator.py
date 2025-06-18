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

from .team import Team
from .brain import Brain
from ..utils.logger import get_logger

# Import ToolExecutor for secure tool dispatch
from ..tool.executor import ToolExecutor, ToolResult
from ..tool.registry import get_tool_registry

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
        team: Team = None, 
        max_rounds: int = 50, 
        timeout: int = 3600,
        memory_system: Optional['MemorySystem'] = None
    ):
        self.team = team
        self.max_rounds = max_rounds
        self.timeout = timeout
        self.memory_system = memory_system
        
        # Initialize tool execution components
        self.tool_registry = get_tool_registry()
        self.tool_executor = ToolExecutor(registry=self.tool_registry)
        
        # Initialize routing brain if configured and team exists
        if team:
            orchestrator_config = getattr(team.config, 'orchestrator', None)
            if orchestrator_config and hasattr(orchestrator_config, 'brain_config'):
                self.routing_brain = Brain.from_config(orchestrator_config.brain_config)
            else:
                self.routing_brain = None
            
            # Initialize memory system if not provided
            if not self.memory_system:
                self._initialize_memory_system()
                
            logger.info(f"Orchestrator initialized with team '{team.name}' (routing brain: {'enabled' if self.routing_brain else 'disabled'}, memory: {'enabled' if self.memory_system else 'disabled'})")
        else:
            self.routing_brain = None
            logger.info("Orchestrator initialized without team (tool execution only)")

    def _initialize_memory_system(self) -> None:
        """Initialize the memory system with synthesis engine."""
        if not self.team:
            return
            
        try:
            from ..memory.factory import create_memory_backend
            # Skip synthesis engine and memory system for now
            
            # Get memory config from team if available
            memory_config = getattr(self.team.config, 'memory', None)
            
            if memory_config:
                backend = create_memory_backend(memory_config)
                logger.info("Memory backend initialized")
            
        except Exception as e:
            logger.warning(f"Failed to initialize memory system: {e}")
            self.memory_system = None

    # ============================================================================
    # AGENT ROUTING - Intelligent coordination decisions
    # ============================================================================

    async def get_next_agent(self, context: Dict[str, Any], last_response: str = None) -> str:
        """
        Determine the next agent to execute with memory-enhanced context.
        
        Now includes memory-derived context for better routing decisions.
        """
        try:
            # Enhance context with memory if available
            enhanced_context = await self._enhance_context_with_memory(context, last_response)
            
            if self.routing_brain:
                return await self._intelligent_agent_selection(enhanced_context, last_response)
            else:
                return self._heuristic_agent_selection(enhanced_context)
                
        except Exception as e:
            logger.error(f"Error in get_next_agent: {e}")
            # Fallback to first agent
            return list(self.team.agents.keys())[0] if self.team.agents else "unknown"

    async def decide_next_step(self, context: Dict[str, Any], last_response: str = None) -> Dict[str, Any]:
        """
        Decide the next action with memory-enhanced context.
        
        Enhanced with memory system integration for better decision making.
        """
        try:
            # Enhance context with memory if available
            enhanced_context = await self._enhance_context_with_memory(context, last_response)
            
            if self.routing_brain:
                return await self._intelligent_routing_decision(enhanced_context, last_response)
            else:
                return self._heuristic_routing_decision(enhanced_context)
                
        except Exception as e:
            logger.error(f"Error in decide_next_step: {e}")
            return {
                "action": "CONTINUE",
                "next_agent": context.get("current_agent", "unknown"),
                "reason": f"Error in routing decision: {e}"
            }

    async def _enhance_context_with_memory(self, context: Dict[str, Any], last_response: str = None) -> Dict[str, Any]:
        """
        Enhance context with memory-derived information.
        
        This implements the context injection pipeline from the architecture.
        """
        enhanced_context = context.copy()
        
        if not self.memory_system:
            return enhanced_context
        
        try:
            # Get relevant memory context
            memory_context = await self.memory_system.get_relevant_context(
                last_user_message=last_response or context.get("last_user_message", ""),
                agent_name=context.get("current_agent")
            )
            
            if memory_context:
                enhanced_context["memory_context"] = memory_context
                enhanced_context["has_memory_context"] = True
                logger.debug("Enhanced context with memory information")
            else:
                enhanced_context["has_memory_context"] = False
                
        except Exception as e:
            logger.error(f"Error enhancing context with memory: {e}")
            enhanced_context["memory_context_error"] = str(e)
            enhanced_context["has_memory_context"] = False
        
        return enhanced_context

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
        if not self.team or len(self.team.agents) <= 1:
            # Single agent or no team - return the only/current agent
            if self.team and self.team.agents:
                return list(self.team.agents.keys())[0]
            return context.get("current_agent", "default")
        
        routing_decision = await self._intelligent_routing_decision(context, last_response)
        
        if routing_decision["action"] == "HANDOFF":
            return routing_decision["next_agent"]
        elif routing_decision["action"] == "CONTINUE":
            return context.get("current_agent")
        else:  # COMPLETE
            # Task is complete, return current agent for final cleanup
            return context.get("current_agent")

    async def _intelligent_routing_decision(
        self, 
        context: Dict[str, Any], 
        last_response: str
    ) -> Dict[str, Any]:
        """Use LLM to make intelligent routing decisions."""
        try:
            # Build routing prompt
            routing_prompt = self._build_routing_prompt(context, last_response)
            
            messages = [
                {"role": "user", "content": routing_prompt}
            ]
            
            # Get routing decision from Brain
            brain_response = await self.routing_brain.generate_response(
                messages=messages,
                system_prompt=self._get_routing_system_prompt()
            )
            
            # Parse the structured response
            try:
                decision = json.loads(brain_response.content)
                
                # Validate the decision structure
                if not isinstance(decision, dict) or "action" not in decision:
                    raise ValueError("Invalid decision format")
                
                # Ensure next_agent is provided for handoff
                if decision["action"] == "HANDOFF" and "next_agent" not in decision:
                    raise ValueError("Handoff decision missing next_agent")
                
                return decision
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse routing decision: {e}, falling back to heuristic")
                return self._heuristic_routing_decision(context, last_response)
                
        except Exception as e:
            logger.error(f"Error in intelligent routing: {e}, falling back to heuristic")
            return self._heuristic_routing_decision(context, last_response)

    def _heuristic_agent_selection(self, context: Dict[str, Any]) -> str:
        """
        Determine which agent should execute next based on task context and previous response.
        
        Args:
            context: Current task context including history, current agent, available agents
            
        Returns:
            Name of the agent that should execute next
        """
        if not self.team or len(self.team.agents) <= 1:
            # Single agent or no team - return the only/current agent
            if self.team and self.team.agents:
                return list(self.team.agents.keys())[0]
            return context.get("current_agent", "default")
        
        # For heuristic selection, just return current agent or first agent
        current_agent = context.get("current_agent")
        if current_agent and current_agent in self.team.agents:
            return current_agent
        else:
            return list(self.team.agents.keys())[0]

    def _heuristic_routing_decision(
        self, 
        context: Dict[str, Any], 
        last_response: str = None
    ) -> Dict[str, Any]:
        """Fall back to simple heuristic routing logic."""
        if not last_response:
            return {"action": "CONTINUE", "reason": "No response to analyze"}
        
        # Check for completion signals in response
        completion_signals = [
            "task complete", "task is complete", "finished", "done",
            "final answer", "conclusion", "summary"
        ]
        
        response_lower = last_response.lower()
        if any(signal in response_lower for signal in completion_signals):
            return {"action": "COMPLETE", "reason": "Completion signal detected in response"}
        
        # Simple handoff logic based on agent roles and descriptions
        current_agent = context.get("current_agent")
        if current_agent and current_agent in self.team.agents:
            next_agent = self._decide_handoff_target(current_agent, last_response)
            if next_agent:
                return {
                    "action": "HANDOFF", 
                    "next_agent": next_agent,
                    "reason": f"Handoff to {next_agent} based on task flow"
                }
        
        # Default: continue with current agent
        return {"action": "CONTINUE", "reason": "Continue with current agent"}

    def _decide_handoff_target(self, current_agent: str, response: str) -> Optional[str]:
        """Decide handoff target based on current agent and response content."""
        current_agent_obj = self.team.agents.get(current_agent)
        if not current_agent_obj:
            return None
            
        current_desc = current_agent_obj.config.description.lower()
        
        # Get other available agents
        other_agents = {name: agent for name, agent in self.team.agents.items() 
                       if name != current_agent}
        
        if not other_agents:
            return None
        
        # Simple handoff logic based on agent descriptions
        # Writer typically hands off to reviewer
        if 'writ' in current_desc:
            for name, agent in other_agents.items():
                desc = agent.config.description.lower()
                if any(word in desc for word in ['review', 'quality', 'edit', 'check']):
                    return name
        
        # Researcher typically hands off to writer
        if 'research' in current_desc:
            for name, agent in other_agents.items():
                desc = agent.config.description.lower()
                if 'writ' in desc:
                    return name
        
        # Reviewer can hand back to writer or move forward
        if 'review' in current_desc:
            for name, agent in other_agents.items():
                desc = agent.config.description.lower()
                if 'writ' in desc:
                    return name
        
        return None

    def _build_routing_prompt(self, context: Dict[str, Any], last_response: str = None) -> str:
        """Build routing prompt with memory context."""
        current_agent = context.get("current_agent", "unknown")
        available_agents = context.get("available_agents", [])
        round_count = context.get("round_count", 0)
        initial_prompt = context.get("initial_prompt", "")
        
        # Get agent descriptions
        agent_descriptions = {}
        if self.team:
            for name, agent in self.team.agents.items():
                agent_descriptions[name] = agent.config.description
        
        base_prompt = f"""
You are an intelligent agent routing system for the AgentX framework.
Your task is to analyze the current context and decide which agent should handle the next step.

TEAM CONFIGURATION:
{self._format_team_info() if self.team else 'No team configured'}

CURRENT CONTEXT:
- Current Agent: {context.get('current_agent', 'None')}
- Round: {context.get('round_count', 0)} / {context.get('max_rounds', self.max_rounds)}
- Task Status: {context.get('task_status', 'active')}
- Available Agents: {list(self.team.agents.keys()) if self.team else []}

RECENT ACTIVITY:
"""
        
        # Add memory context if available
        if context.get("has_memory_context") and context.get("memory_context"):
            base_prompt += f"""
MEMORY CONTEXT:
{context['memory_context']}
"""
        
        # Add conversation history
        if last_response:
            base_prompt += f"""
Last Response: {last_response[:500]}...

"""
        
        base_prompt += """
Based on this information, determine the most appropriate next agent.
Respond with just the agent name."""
        
        return base_prompt

    def _format_team_info(self) -> str:
        """Format team information for routing prompts."""
        if not self.team:
            return "No team configured"
        
        info = f"Team: {self.team.name}\n"
        for name, agent in self.team.agents.items():
            info += f"- {name}: {agent.config.description}\n"
        return info

    def _get_routing_system_prompt(self) -> str:
        """Get system prompt for routing decisions with memory awareness."""
        return """You are an expert agent coordination system with access to team memory and context.

Your responsibilities:
1. Analyze the current task state and agent capabilities
2. Consider memory context including user constraints and active issues
3. Route work to the most appropriate agent based on skills and current needs
4. Ensure efficient collaboration and avoid redundant work

Key principles:
- Respect user constraints and preferences from memory
- Address active issues and hot problems first
- Leverage agent strengths and specializations
- Maintain task momentum and quality standards
- Make routing decisions that advance toward completion

Always consider the memory context when making routing decisions."""

    # ============================================================================
    # TOOL EXECUTION DISPATCH - Security and centralized control
    # ============================================================================

    async def execute_tool_calls(
        self, 
        tool_calls: List[Any], 
        agent_name: str = "default"
    ) -> List[Dict[str, Any]]:
        """
        Dispatch tool calls to ToolExecutor for secure execution.
        
        This provides centralized security control over all tool execution.
        """
        logger.debug(f"🔧 Orchestrator dispatching {len(tool_calls)} tool calls for agent '{agent_name}'")
        return await self.tool_executor.execute_tool_calls(tool_calls, agent_name)

    async def execute_single_tool(
        self, 
        tool_name: str, 
        agent_name: str = "default",
        **kwargs
    ) -> ToolResult:
        """
        Dispatch single tool execution to ToolExecutor.
        
        Args:
            tool_name: Name of the tool to execute
            agent_name: Name of the agent requesting execution
            **kwargs: Tool arguments
            
        Returns:
            ToolResult with execution outcome
        """
        logger.debug(f"🔧 Orchestrator dispatching tool '{tool_name}' for agent '{agent_name}'")
        return await self.tool_executor.execute_tool(tool_name, agent_name, **kwargs)

    def get_available_tools(self, agent_name: str = "default") -> List[str]:
        """Get list of tools available to an agent."""
        all_tools = self.tool_registry.list_tools()
        
        # Filter by agent permissions
        security_policy = self.tool_executor.security_policy
        allowed_tools = security_policy.TOOL_PERMISSIONS.get(
            agent_name, 
            security_policy.TOOL_PERMISSIONS["default"]
        )
        
        return [tool for tool in all_tools if tool in allowed_tools]

    def get_tool_schemas_for_agent(self, agent_name: str = "default") -> List[Dict[str, Any]]:
        """Get tool schemas available to a specific agent."""
        from ..tool.schemas import get_tool_schemas
        available_tools = self.get_available_tools(agent_name)
        return get_tool_schemas(available_tools)

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get tool execution statistics."""
        return self.tool_executor.get_execution_stats()

    def clear_execution_history(self):
        """Clear tool execution history."""
        self.tool_executor.clear_history()
        logger.info("🧹 Tool execution history cleared")


# Global orchestrator instance for single-agent tool execution
_global_orchestrator = None


def get_orchestrator() -> Orchestrator:
    """Get the global orchestrator instance for single-agent tool execution."""
    global _global_orchestrator
    if _global_orchestrator is None:
        _global_orchestrator = Orchestrator(team=None)  # No team = tool execution only
    return _global_orchestrator