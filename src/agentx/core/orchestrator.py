"""
Central orchestrator for managing agent interactions and tool execution.

The orchestrator is the central nervous system that:
- Makes routing decisions (complete, handoff, continue)
- Dispatches tool calls to ToolExecutor for secure execution
- Manages agent collaboration and handoffs
- Maintains task workflow coordination
"""

import asyncio
import json
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List, AsyncGenerator

from .team import Team
from .agent import Agent
from .brain import Brain, LLMMessage
from .config import BrainConfig
from ..utils.logger import get_logger

# Import ToolExecutor for secure tool dispatch
from ..tool.executor import ToolExecutor, ToolResult
from ..tool.registry import get_tool_registry

logger = get_logger(__name__)


class RoutingAction(Enum):
    """Possible routing actions."""
    COMPLETE = "complete"
    HANDOFF = "handoff" 
    CONTINUE = "continue"


@dataclass
class RoutingDecision:
    """Represents a routing decision made by the orchestrator."""
    action: RoutingAction
    next_agent: Optional[str] = None
    reason: str = ""


class Orchestrator:
    """
    Central orchestrator for agent coordination and secure tool execution.
    
    This class handles:
    - Routing decisions between agents (core orchestration)
    - Dispatching tool calls to ToolExecutor for security
    - Managing team collaboration workflows
    - Intelligent handoff detection and execution
    """
    
    def __init__(self, team: Team = None, max_rounds: int = None, timeout: int = None):
        """Initialize orchestrator with team and limits."""
        self.team = team
        self.max_rounds = max_rounds or 50
        self.timeout = timeout or 3600  # 1 hour default
        
        # Initialize ToolExecutor for secure tool dispatch
        self.tool_executor = ToolExecutor()
        self.tool_registry = get_tool_registry()
        
        # Initialize orchestrator's brain for intelligent routing decisions
        if team:
            orchestrator_brain_config = BrainConfig(
                model="deepseek/deepseek-chat",
                temperature=0.0,  # Low temperature for consistent decisions
                max_tokens=200,   # Short responses for routing decisions
                timeout=10        # Quick decisions
            )
            self.brain = Brain(orchestrator_brain_config)
            logger.info(f"🎭 Orchestrator initialized for team '{team.name}' with {len(team.agents)} agents")
        else:
            # Single-agent mode or global orchestrator
            self.brain = None
            logger.info("🎭 Orchestrator initialized for tool execution")

    # ============================================================================
    # CORE ORCHESTRATION - Agent routing and collaboration
    # ============================================================================

    async def decide_next_step(self, current_agent: str, response: str, task_context: Dict[str, Any]) -> RoutingDecision:
        """
        Core routing logic - decide what happens next.
        
        This is the primary orchestration responsibility.
        """
        if not self.team:
            # Single agent mode - always complete
            return RoutingDecision(
                action=RoutingAction.COMPLETE,
                reason="Single agent task completed"
            )
        
        # Check if task should be completed
        if await self._should_complete_task(current_agent, response, task_context):
            return RoutingDecision(
                action=RoutingAction.COMPLETE,
                reason="Task completion criteria met"
            )
        
        # Check if we should handoff to another agent
        next_agent = self._decide_handoff_target(current_agent, response, task_context)
        if next_agent:
            return RoutingDecision(
                action=RoutingAction.HANDOFF,
                next_agent=next_agent,
                reason=f"Intelligent routing suggests handoff to {next_agent}"
            )
        
        # Default: continue with current agent
        return RoutingDecision(
            action=RoutingAction.CONTINUE,
            reason="No handoff needed, continue with current agent"
        )

    async def route_to_agent(
        self, 
        agent_name: str, 
        messages: List[Dict[str, Any]], 
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Route messages to a specific agent for processing.
        
        The orchestrator delegates to the agent but provides itself for tool execution.
        """
        if not self.team or agent_name not in self.team.agents:
            raise ValueError(f"Agent '{agent_name}' not found in team")
        
        agent = self.team.agents[agent_name]
        
        # Agent handles conversation flow, orchestrator handles tool execution
        return await agent.generate_response(
            messages=messages,
            system_prompt=system_prompt,
            orchestrator=self  # Agent delegates tool execution to orchestrator
        )

    async def stream_from_agent(
        self, 
        agent_name: str, 
        messages: List[Dict[str, Any]], 
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream response from a specific agent.
        
        The orchestrator delegates to the agent but provides itself for tool execution.
        """
        if not self.team or agent_name not in self.team.agents:
            raise ValueError(f"Agent '{agent_name}' not found in team")
        
        agent = self.team.agents[agent_name]
        
        # Agent handles conversation flow, orchestrator handles tool execution
        async for chunk in agent.stream_response(
            messages=messages,
            system_prompt=system_prompt,
            orchestrator=self  # Agent delegates tool execution to orchestrator
        ):
            yield chunk

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

    # ============================================================================
    # PRIVATE ROUTING LOGIC - Team coordination and handoff intelligence
    # ============================================================================

    async def _should_complete_task(self, current_agent: str, response: str, task_context: Dict[str, Any]) -> bool:
        """Use LLM intelligence to decide if the task should be completed."""
        if not self.team:
            return True
            
        # Single agent teams complete after first response
        if len(self.team.agents) == 1:
            return True
        
        round_count = task_context.get('round_count', 0)
        
        # Hard limits to prevent infinite loops
        if round_count >= self.max_rounds:
            return True
        
        # Use LLM to intelligently detect completion
        return await self._llm_detect_completion(current_agent, response, task_context)

    def _decide_handoff_target(self, current_agent: str, response: str, task_context: Dict[str, Any]) -> Optional[str]:
        """Decide if we should handoff and to whom."""
        if not self.team:
            return None
            
        # First check explicit handoff rules
        rule_target = self._check_handoff_rules(current_agent, response)
        if rule_target:
            return rule_target
        
        # Then use natural intelligence based on agent descriptions
        return self._natural_handoff_decision(current_agent, response, task_context)

    def _check_handoff_rules(self, current_agent: str, response: str) -> Optional[str]:
        """Check if handoff rules provide specific guidance."""
        if not hasattr(self.team, 'config') or not hasattr(self.team.config, 'handoffs'):
            return None
            
        possible_handoffs = [
            rule for rule in self.team.config.handoffs 
            if rule.from_agent == current_agent
        ]
        
        if not possible_handoffs:
            return None
            
        # For now, return the first valid handoff rule
        # In the future, we could use LLM to evaluate conditions
        for rule in possible_handoffs:
            if rule.to_agent in self.team.agents:
                logger.info(f"🎯 Rule-based handoff: {current_agent} → {rule.to_agent}")
                return rule.to_agent
        
        return None

    def _natural_handoff_decision(self, current_agent: str, response: str, task_context: Dict[str, Any]) -> Optional[str]:
        """Use natural intelligence to decide handoff based on agent descriptions."""
        current_agent_obj = self.team.agents.get(current_agent)
        if not current_agent_obj:
            return None
            
        current_desc = current_agent_obj.config.description.lower()
        
        # Get other available agents
        other_agents = {name: agent for name, agent in self.team.agents.items() 
                       if name != current_agent}
        
        if not other_agents:
            return None
        
        # Use natural reasoning based on descriptions
        # Writer typically hands off to reviewer
        if 'writ' in current_desc:
            for name, agent in other_agents.items():
                desc = agent.config.description.lower()
                if any(word in desc for word in ['review', 'quality', 'edit', 'check']):
                    logger.info(f"🧠 Natural handoff: writer → reviewer ({name})")
                    return name
        
        # Researcher typically hands off to writer
        if 'research' in current_desc:
            for name, agent in other_agents.items():
                desc = agent.config.description.lower()
                if 'writ' in desc:
                    logger.info(f"🧠 Natural handoff: researcher → writer ({name})")
                    return name
        
        # Reviewer can hand back to writer or move forward
        if 'review' in current_desc:
            for name, agent in other_agents.items():
                desc = agent.config.description.lower()
                if 'writ' in desc:
                    logger.info(f"🧠 Natural handoff: reviewer → writer ({name})")
                    return name
        
        # Consultant typically hands off to researcher or writer
        if 'consult' in current_desc:
            for name, agent in other_agents.items():
                desc = agent.config.description.lower()
                if 'research' in desc:
                    logger.info(f"🧠 Natural handoff: consultant → researcher ({name})")
                    return name
            for name, agent in other_agents.items():
                desc = agent.config.description.lower()
                if 'writ' in desc:
                    logger.info(f"🧠 Natural handoff: consultant → writer ({name})")
                    return name
        
        return None

    async def _llm_detect_completion(self, current_agent: str, response: str, task_context: Dict[str, Any]) -> bool:
        """Use LLM intelligence to detect if the task should be completed."""
        if not self.brain:
            # Fallback without LLM
            round_count = task_context.get('round_count', 0)
            return round_count >= 6
            
        try:
            # Get task context
            initial_prompt = task_context.get('initial_prompt', 'Unknown task')
            round_count = task_context.get('round_count', 0)
            
            # Get agent descriptions for context
            agent_descriptions = {
                name: agent.config.description 
                for name, agent in self.team.agents.items()
            }
            
            # Create completion detection prompt
            system_prompt = f"""You are an intelligent task orchestrator. Your job is to determine if a multi-agent collaboration task should be completed.

TASK: {initial_prompt}

AGENTS AVAILABLE:
{chr(10).join([f"- {name}: {desc}" for name, desc in agent_descriptions.items()])}

CURRENT SITUATION:
- Current agent: {current_agent}
- Round: {round_count}
- Latest response: {response[:500]}...

Analyze if this task should be COMPLETED or CONTINUED:

COMPLETE if:
- The task objective has been fully achieved
- All necessary work has been done (writing, reviewing, approving, etc.)
- The output is ready for delivery/publication
- The collaboration has reached a natural conclusion
- Quality standards have been met and approved

CONTINUE if:
- More work is needed
- The task is incomplete
- Additional collaboration would improve the result
- No clear completion signal has been given

Respond with exactly one word: COMPLETE or CONTINUE"""

            messages = [
                LLMMessage(role="user", content="Should this task be completed or continued?")
            ]
            
            response_obj = await self.brain.generate_response(
                messages=messages,
                system_prompt=system_prompt
            )
            
            decision = response_obj.content.strip().upper()
            should_complete = decision == "COMPLETE"
            
            if should_complete:
                logger.info(f"🧠 LLM decision: Task should be completed (reason: {decision})")
            else:
                logger.debug(f"🧠 LLM decision: Task should continue (reason: {decision})")
            
            return should_complete
            
        except Exception as e:
            logger.error(f"LLM completion detection failed: {e}")
            # Fallback: complete after reasonable rounds to prevent infinite loops
            round_count = task_context.get('round_count', 0)
            if round_count >= 6:
                logger.info(f"🔄 Fallback: Completing after {round_count} rounds")
                return True
            return False


# Global orchestrator instance for single-agent tool execution
_global_orchestrator = None


def get_orchestrator() -> Orchestrator:
    """Get the global orchestrator instance for single-agent tool execution."""
    global _global_orchestrator
    if _global_orchestrator is None:
        _global_orchestrator = Orchestrator()  # No team = tool execution only
    return _global_orchestrator