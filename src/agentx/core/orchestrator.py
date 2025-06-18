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
    Central orchestrator for coordination and tool execution.
    
    This class handles:
    - Making intelligent agent routing decisions based on context and responses
    - Validating tool calls against schemas
    - Dispatching tool calls to ToolExecutor for security
    - Managing tool permissions and access control
    - Providing structured error feedback for agent self-correction
    """
    
    def __init__(self, team: Team = None):
        """Initialize orchestrator for coordination and tool execution."""
        self.team = team
        
        # Initialize ToolExecutor for secure tool dispatch
        self.tool_executor = ToolExecutor()
        self.tool_registry = get_tool_registry()
        
        # Initialize Brain for routing decisions if team is provided
        self.routing_brain = None
        if team and team.config.orchestrator:
            brain_config = team.config.orchestrator.brain_config or team.config.orchestrator.get_default_brain_config()
            self.routing_brain = Brain(brain_config)
        
        if team:
            logger.info(f"🎭 Orchestrator initialized for coordination and tool execution with team '{team.name}'")
        else:
            # Single-agent mode or global orchestrator
            logger.info("🎭 Orchestrator initialized for tool execution only")

    # ============================================================================
    # AGENT ROUTING - Intelligent coordination decisions
    # ============================================================================

    async def get_next_agent(
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
        
        routing_decision = await self.decide_next_step(context, last_response)
        
        if routing_decision["action"] == "HANDOFF":
            return routing_decision["next_agent"]
        elif routing_decision["action"] == "CONTINUE":
            return context.get("current_agent")
        else:  # COMPLETE
            # Task is complete, return current agent for final cleanup
            return context.get("current_agent")

    async def decide_next_step(
        self, 
        context: Dict[str, Any], 
        last_response: str = None
    ) -> Dict[str, Any]:
        """
        Make an intelligent routing decision based on task context and agent response.
        
        Args:
            context: Current task context including history, agents, progress
            last_response: The last agent's response to analyze
            
        Returns:
            Dict with action ("CONTINUE", "HANDOFF", "COMPLETE"), next_agent, and reason
        """
        if not self.team:
            return {"action": "COMPLETE", "reason": "No team configured"}
        
        # Single agent teams always complete after response
        if len(self.team.agents) == 1:
            return {"action": "COMPLETE", "reason": "Single agent task completed"}
        
        # Check basic completion conditions first
        if context.get("round_count", 0) >= context.get("max_rounds", 50):
            return {"action": "COMPLETE", "reason": "Maximum rounds reached"}
        
        # Use Brain for intelligent routing if available
        if self.routing_brain and last_response:
            return await self._intelligent_routing_decision(context, last_response)
        else:
            # Fall back to simple heuristic routing
            return self._heuristic_routing_decision(context, last_response)

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

    def _build_routing_prompt(self, context: Dict[str, Any], last_response: str) -> str:
        """Build the prompt for intelligent routing decisions."""
        current_agent = context.get("current_agent", "unknown")
        available_agents = context.get("available_agents", [])
        round_count = context.get("round_count", 0)
        initial_prompt = context.get("initial_prompt", "")
        
        # Get agent descriptions
        agent_descriptions = {}
        if self.team:
            for name, agent in self.team.agents.items():
                agent_descriptions[name] = agent.config.description
        
        prompt = f"""Analyze the current task context and last agent response to determine the next routing decision.

TASK CONTEXT:
- Initial task: {initial_prompt}
- Current round: {round_count}
- Current agent: {current_agent}
- Available agents: {', '.join(available_agents)}

AGENT DESCRIPTIONS:
{json.dumps(agent_descriptions, indent=2)}

LAST AGENT RESPONSE:
{last_response}

Based on this information, determine the next action. Consider:
1. Is the task complete based on the response?
2. Should we continue with the current agent?
3. Should we hand off to a different agent, and if so, which one?

Respond with a JSON object in this exact format:
{{
    "action": "CONTINUE|HANDOFF|COMPLETE",
    "next_agent": "agent_name_if_handoff",
    "reason": "explanation of the decision"
}}

For HANDOFF actions, next_agent must be one of the available agents.
For CONTINUE or COMPLETE actions, next_agent should be omitted or null."""
        
        return prompt

    def _get_routing_system_prompt(self) -> str:
        """Get the system prompt for routing decisions."""
        return """You are an intelligent task orchestrator responsible for routing decisions in a multi-agent system.

Your role is to analyze the current task context and agent responses to make optimal routing decisions:
- CONTINUE: Keep the current agent working if they should continue their current task
- HANDOFF: Transfer control to another agent when their expertise is needed
- COMPLETE: End the task when the objective has been achieved

Always respond with valid JSON in the exact format requested. Base decisions on:
1. Task completion indicators in the response
2. Whether the current agent has completed their specialized role
3. Which agent's expertise is needed next
4. Overall task progress and efficiency

Be decisive and provide clear reasoning for each decision."""

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
        _global_orchestrator = Orchestrator()  # No team = tool execution only
    return _global_orchestrator