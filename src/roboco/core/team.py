"""
Unified Team class - replaces AG2's problematic GroupChat + GroupChatManager split.

This single class manages multi-agent conversations elegantly.
"""

import asyncio
from ..utils.logger import get_logger
import json
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass
from enum import Enum

from .agent import Agent
from .brain import Message, ChatHistory
from .event import Event

logger = get_logger(__name__)


class SpeakerSelectionMethod(Enum):
    """Methods for selecting the next speaker."""
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    LLM_BASED = "llm_based"
    MANUAL = "manual"
    CUSTOM = "custom"


@dataclass
class TeamConfig:
    """Team configuration."""
    name: str
    max_rounds: int = 10
    speaker_selection: SpeakerSelectionMethod = SpeakerSelectionMethod.ROUND_ROBIN
    allow_repeat_speaker: bool = True
    enable_memory: bool = True
    auto_save_history: bool = True
    termination_keywords: List[str] = None
    
    def __post_init__(self):
        if self.termination_keywords is None:
            self.termination_keywords = ["TERMINATE", "EXIT", "STOP"]


class Team:
    """
    Unified Team class for multi-agent conversations.
    
    This replaces AG2's confusing GroupChat + GroupChatManager split
    with a single, elegant class that manages everything.
    """
    
    def __init__(self, config: Union[TeamConfig, Dict[str, Any]], agents: List[Agent]):
        # Convert dict to config if needed
        if isinstance(config, dict):
            config = TeamConfig(**config)
        
        self.config = config
        self.name = config.name
        self.agents = {agent.name: agent for agent in agents}
        self.agent_list = agents
        
        # Conversation state - using task-level ChatHistory
        self.chat_history = ChatHistory(task_id="")
        self.current_round = 0
        self.current_speaker: Optional[Agent] = None
        self.is_active = False
        
        # Speaker selection
        self._speaker_index = 0
        self._custom_selector: Optional[Callable] = None
        
        # Tool management
        self._tool_executor: Optional[Agent] = None
        self._team_tools: Dict[str, "Tool"] = {}
        
        # Set agent teams and find tool executor
        for agent in self.agent_list:
            agent._team = self  # Set team reference
            
            # Auto-detect tool executor (agent with tools or code execution)
            if (self._tool_executor is None and 
                (agent.config.enable_code_execution or 
                 "executor" in agent.name.lower() or 
                 "tool" in agent.name.lower())):
                self._tool_executor = agent
                logger.info(f"Auto-detected tool executor: {agent.name}")
        
        # Validation
        self._validate_agents()
        
        logger.info(f"Created team '{self.name}' with {len(self.agents)} agents")
        if self._tool_executor:
            logger.info(f"Tool executor: {self._tool_executor.name}")
    
    def _validate_agents(self):
        """Validate team configuration."""
        if not self.agents:
            raise ValueError("Team must have at least one agent")
        
        # Check for duplicate names
        names = [agent.name for agent in self.agent_list]
        if len(names) != len(set(names)):
            raise ValueError("Agent names must be unique")
        
        # Ensure at least one assistant agent for conversations
        assistant_count = sum(1 for agent in self.agent_list if agent.is_assistant_agent)
        if assistant_count == 0:
            logger.warning("Team has no assistant agents - conversations may be limited")
    
    def add_agent(self, agent: Agent):
        """Add an agent to the team."""
        if agent.name in self.agents:
            raise ValueError(f"Agent '{agent.name}' already exists in team")
        
        self.agents[agent.name] = agent
        self.agent_list.append(agent)
        
        logger.info(f"Added agent '{agent.name}' to team '{self.name}'")
    
    def remove_agent(self, agent_name: str):
        """Remove an agent from the team."""
        if agent_name not in self.agents:
            raise ValueError(f"Agent '{agent_name}' not found in team")
        
        agent = self.agents.pop(agent_name)
        self.agent_list.remove(agent)
        
        logger.info(f"Removed agent '{agent_name}' from team '{self.name}'")
    
    def get_agent(self, name: str) -> Optional[Agent]:
        """Get an agent by name."""
        return self.agents.get(name)
    
    async def start_conversation(
        self, 
        initial_message: str,
        initial_speaker: Optional[str] = None
    ) -> ChatHistory:
        """Start a team conversation."""
        if self.is_active:
            raise RuntimeError("Team conversation is already active")
        
        self.is_active = True
        self.current_round = 0
        
        try:
            # Select initial speaker
            if initial_speaker:
                self.current_speaker = self.get_agent(initial_speaker)
                if not self.current_speaker:
                    raise ValueError(f"Initial speaker '{initial_speaker}' not found")
            else:
                self.current_speaker = self._select_next_speaker(None)
            
            # Create initial message
            initial_msg = Message(
                content=initial_message,
                sender="System",
                recipient=self.current_speaker.name,
                role="system"
            )
            
            self.chat_history.add_message(initial_msg)
            
            # Start conversation loop
            await self._conversation_loop(initial_msg)
            
            return self.chat_history
            
        finally:
            self.is_active = False
    
    async def _conversation_loop(self, initial_message: Message):
        """Main conversation loop."""
        current_message = initial_message
        
        while (self.current_round < self.config.max_rounds and 
               not self._should_terminate(current_message)):
            
            # Send message to current speaker
            response = await self.current_speaker.receive_message(
                current_message, 
                request_reply=True
            )
            
            if not response:
                logger.info("No response generated, ending conversation")
                break
            
            # Add response to history
            self.chat_history.add_message(response)
            
            # Check for termination
            if self._should_terminate(response):
                logger.info("Termination condition met")
                break
            
            # Select next speaker
            next_speaker = self._select_next_speaker(self.current_speaker)
            if not next_speaker:
                logger.info("No next speaker available, ending conversation")
                break
            
            # Update state
            self.current_speaker = next_speaker
            current_message = response
            self.current_round += 1
            
            logger.debug(f"Round {self.current_round}: {next_speaker.name} speaking")
    
    def _select_next_speaker(self, current_speaker: Optional[Agent]) -> Optional[Agent]:
        """Select the next speaker based on configuration."""
        if not self.agent_list:
            return None
        
        if self.config.speaker_selection == SpeakerSelectionMethod.ROUND_ROBIN:
            return self._select_round_robin(current_speaker)
        elif self.config.speaker_selection == SpeakerSelectionMethod.RANDOM:
            return self._select_random(current_speaker)
        elif self.config.speaker_selection == SpeakerSelectionMethod.LLM_BASED:
            return self._select_llm_based(current_speaker)
        elif self.config.speaker_selection == SpeakerSelectionMethod.MANUAL:
            return self._select_manual(current_speaker)
        elif self.config.speaker_selection == SpeakerSelectionMethod.CUSTOM:
            return self._select_custom(current_speaker)
        else:
            return self._select_round_robin(current_speaker)
    
    def _select_round_robin(self, current_speaker: Optional[Agent]) -> Agent:
        """Select next speaker using round-robin."""
        if not self.config.allow_repeat_speaker and current_speaker:
            # Find next different speaker
            current_index = self.agent_list.index(current_speaker)
            for i in range(1, len(self.agent_list)):
                next_index = (current_index + i) % len(self.agent_list)
                if self.agent_list[next_index] != current_speaker:
                    return self.agent_list[next_index]
        
        # Standard round-robin
        self._speaker_index = (self._speaker_index + 1) % len(self.agent_list)
        return self.agent_list[self._speaker_index]
    
    def _select_random(self, current_speaker: Optional[Agent]) -> Agent:
        """Select next speaker randomly."""
        import random
        
        if not self.config.allow_repeat_speaker and current_speaker and len(self.agent_list) > 1:
            candidates = [agent for agent in self.agent_list if agent != current_speaker]
            return random.choice(candidates)
        
        return random.choice(self.agent_list)
    
    def _select_llm_based(self, current_speaker: Optional[Agent]) -> Agent:
        """Select next speaker using LLM reasoning."""
        # TODO: Implement LLM-based speaker selection
        # For now, fall back to round-robin
        return self._select_round_robin(current_speaker)
    
    def _select_manual(self, current_speaker: Optional[Agent]) -> Optional[Agent]:
        """Select next speaker manually."""
        try:
            print("\nAvailable speakers:")
            for i, agent in enumerate(self.agent_list):
                print(f"{i + 1}. {agent.name} ({agent.role.value})")
            
            choice = input("Select next speaker (number or name): ").strip()
            
            # Try to parse as number
            try:
                index = int(choice) - 1
                if 0 <= index < len(self.agent_list):
                    return self.agent_list[index]
            except ValueError:
                pass
            
            # Try to find by name
            for agent in self.agent_list:
                if agent.name.lower() == choice.lower():
                    return agent
            
            print("Invalid selection, using round-robin")
            return self._select_round_robin(current_speaker)
            
        except (EOFError, KeyboardInterrupt):
            return None
    
    def _select_custom(self, current_speaker: Optional[Agent]) -> Optional[Agent]:
        """Select next speaker using custom selector."""
        if self._custom_selector:
            return self._custom_selector(current_speaker, self)
        return self._select_round_robin(current_speaker)
    
    def set_custom_selector(self, selector: Callable[[Optional[Agent], "Team"], Optional[Agent]]):
        """Set a custom speaker selector function."""
        self._custom_selector = selector
    
    def _should_terminate(self, message: Message) -> bool:
        """Check if conversation should terminate."""
        return any(keyword in message.content.upper() for keyword in self.config.termination_keywords)
    
    def get_chat_history(self) -> ChatHistory:
        """Get the chat history."""
        return self.chat_history
    
    def clear_history(self):
        """Clear conversation history."""
        self.chat_history.clear_history()
        self.current_round = 0
    
    def get_agent_names(self) -> List[str]:
        """Get list of agent names."""
        return list(self.agents.keys())
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get conversation summary."""
        return {
            "team_name": self.name,
            "agents": self.get_agent_names(),
            "rounds": self.current_round,
            "messages": len(self.chat_history),
            "is_active": self.is_active,
            "current_speaker": self.current_speaker.name if self.current_speaker else None
        }
    
    def reset(self):
        """Reset team state."""
        self.clear_history()
        self.current_speaker = None
        self.is_active = False
        self._speaker_index = 0
        
        # Reset all agents
        for agent in self.agent_list:
            agent.reset()
    
    def __str__(self) -> str:
        return f"Team({self.name}, {len(self.agents)} agents)"
    
    def __repr__(self) -> str:
        return f"Team(name='{self.name}', agents={len(self.agents)}, active={self.is_active})"
    
    def set_tool_executor(self, agent_name: str):
        """Manually set the tool executor agent."""
        agent = self.get_agent(agent_name)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found in team")
        
        self._tool_executor = agent
        logger.info(f"Set tool executor: {agent_name}")
    
    def get_tool_executor(self) -> Optional[Agent]:
        """Get the team's tool executor agent."""
        return self._tool_executor
    
    def register_tool(self, tool: "Tool"):
        """Register a tool with the team."""
        self._team_tools[tool.name] = tool
        logger.info(f"Registered tool '{tool.name}' with team '{self.name}'")
    
    async def execute_tool(self, tool_name: str, **kwargs):
        """Execute a tool using the team's tool registry."""
        from .tool import ToolResult  # Import here to avoid circular imports
        
        tool = self._team_tools.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                result=None,
                error=f"Tool '{tool_name}' not found in team registry"
            )
        
        return await tool.execute(**kwargs)
    
    def list_team_tools(self) -> List[str]:
        """List all tools registered with the team."""
        return list(self._team_tools.keys())
    
    async def execute_tool_calls(self, message: "Message") -> List["Message"]:
        """Execute tool calls using the team's tool executor."""
        from .brain import Message  # Import here to avoid circular imports
        
        if not message.tool_calls:
            return []
        
        if not self._tool_executor:
            logger.error(f"No tool executor in team {self.name}")
            return []
        
        results = []
        
        for call in message.tool_calls:
            try:
                tool_name = call["function"]["name"]
                tool_args = json.loads(call["function"]["arguments"])
                
                # Execute the tool
                result = await self.execute_tool(tool_name, **tool_args)
                
                # Create result message
                results.append(Message(
                    content=str(result.result) if result.success else f"Error: {result.error}",
                    sender=self._tool_executor.name,
                    role="tool",
                    name=tool_name,
                    metadata={
                        "tool_call_id": call["id"],
                        "success": result.success,
                        "execution_time": result.execution_time
                    }
                ))
                
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                results.append(Message(
                    content=f"Error: {str(e)}",
                    sender=self._tool_executor.name,
                    role="tool",
                    name=call.get("function", {}).get("name", "unknown"),
                    metadata={"error": True, "tool_call_id": call.get("id", "unknown")}
                ))
        
        return results


def create_team(
    name: str,
    agents: List[Agent],
    max_rounds: int = 10,
    speaker_selection: SpeakerSelectionMethod = SpeakerSelectionMethod.ROUND_ROBIN,
    **kwargs
) -> Team:
    """Create a team with the given configuration."""
    config = TeamConfig(
        name=name,
        max_rounds=max_rounds,
        speaker_selection=speaker_selection,
        **kwargs
    )
    return Team(config, agents) 