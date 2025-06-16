"""
Clean orchestrator implementation - pure routing logic only.

The orchestrator only makes routing decisions (complete, handoff, continue).
Task creation and execution is handled by the Task class.
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
from .brain import Brain, LLMMessage
from .config import LLMConfig
from ..utils.logger import get_logger

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
    Pure routing orchestrator - only makes decisions about what happens next.
    Does NOT create or execute tasks - that's the Task class's responsibility.
    """
    
    def __init__(self, team: Team, max_rounds: int = None, timeout: int = None):
        """Initialize orchestrator with team and limits."""
        self.team = team
        self.max_rounds = max_rounds or 50
        self.timeout = timeout or 3600  # 1 hour default
        
        # Initialize orchestrator's brain for intelligent decisions
        orchestrator_llm_config = LLMConfig(
            model="deepseek-chat",
            temperature=0.0,  # Low temperature for consistent decisions
            max_tokens=200,   # Short responses for routing decisions
            timeout=10        # Quick decisions
        )
        self.brain = Brain(orchestrator_llm_config)
        
        logger.info(f"🎭 Orchestrator initialized for team '{team.name}' with {len(team.agents)} agents")

    async def decide_next_step(self, current_agent: str, response: str, task_context: Dict[str, Any]) -> RoutingDecision:
        """
        Core routing logic - decide what happens next.
        
        This is the ONLY job of the orchestrator: routing decisions.
        """
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
    
    async def _should_complete_task(self, current_agent: str, response: str, task_context: Dict[str, Any]) -> bool:
        """Use LLM intelligence to decide if the task should be completed."""
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
        """
        Use natural intelligence to decide handoff based on agent descriptions.
        
        This uses the orchestrator's training knowledge about common workflows,
        not hardcoded rules.
        """
        # Get current agent info
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
            # Look for writer first (for revisions)
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
            if round_count >= 6:
                logger.info(f"🔄 Fallback: Completing after {round_count} rounds")
                return True
            return False