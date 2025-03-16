"""
Team Management Module

This module provides base classes for organizing agents into teams and managing their interactions.
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple, Callable, Type
from loguru import logger
import inspect

import autogen
from autogen import (
    ConversableAgent,
    UserProxyAgent,
    register_function,
    register_hand_off,
    OnCondition,
    AfterWork,
    AfterWorkOption,
    SwarmResult
)

from autogen.agentchat import initiate_swarm_chat
from autogen.agentchat.conversable_agent import ConversableAgent

from roboco.core.config import load_config, get_llm_config
from roboco.core.agent import Agent
from roboco.core.tool_factory import ToolFactory


class Team:
    """
    Base class for all roboco teams, providing common functionality for team management.
    """
    
    def __init__(
        self,
        name: str,
        agents: List[Any],
        config_path: Optional[str] = None
    ):
        """Initialize a team of agents.
        
        Args:
            name: Name of the team
            agents: List of agents in the team
            config_path: Optional path to team configuration file
        """
        self.name = name
        self.agents = agents
        
        # Load configuration
        self.config = load_config(config_path)
        self.llm_config = get_llm_config(self.config)
        
        logger.info(f"Initialized Team: {name} with {len(agents)} agents")
        
        # Initialize tools registry
        self.tools = {}
        
        # Storage for output artifacts
        self.artifacts = {}
        
        # Flag to indicate if swarm mode is enabled
        self.swarm_enabled = False
        
        # Store handoff configurations for swarm mode
        self.handoffs = {}
        
        # Shared context for swarm agents
        self.shared_context = {}
    
    def add_agent(self, agent_name: str, agent: Agent) -> None:
        """
        Add an agent to the team.
        
        Args:
            agent_name: Name of the agent
            agent: The agent instance
        """
        self.agents[agent_name] = agent
        logger.info(f"Added agent '{agent_name}' to the team")
    
    def get_agent(self, agent_name: str) -> Optional[Agent]:
        """
        Get an agent from the team by name.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            The agent instance or None if not found
        """
        return self.agents.get(agent_name)
    
    def create_agent(self, agent_class: type, name: str, **kwargs) -> ConversableAgent:
        """
        Create an agent with the given class and add it to the team.
        
        Args:
            agent_class: The agent class to instantiate
            name: Name for the agent
            **kwargs: Additional arguments to pass to the agent constructor
            
        Returns:
            The created agent instance
        """
        # Ensure llm_config is set if not provided
        if 'llm_config' not in kwargs:
            kwargs['llm_config'] = self.llm_config
            
        # Create the agent
        agent = agent_class(name=name, **kwargs)
        
        # Add to the team
        self.add_agent(name, agent)
        
        return agent
    
    def register_tool(self, tool_instance: Any, agent_name: Optional[str] = None) -> None:
        """
        Register a tool with an agent.
        
        Args:
            tool_instance: The tool instance to register
            agent_name: Name of the agent to register the tool with (if None, register with all agents)
        """
        tool_name = tool_instance.__class__.__name__
        
        # Get the UserProxyAgent for tool execution
        executor = self.get_agent("ToolUser") if "ToolUser" in self.agents else None
        if not executor:
            logger.warning("No ToolUser agent found for executing tools")
            return
            
        # Get the agents that will call the tools
        caller_agents = []
        if agent_name:
            agent = self.get_agent(agent_name)
            if agent:
                caller_agents.append((agent_name, agent))
            else:
                logger.warning(f"Agent '{agent_name}' not found")
                return
        else:
            # Register with all agents except the executor
            for name, agent in self.agents.items():
                if name != "ToolUser":  # Don't register with the executor itself
                    caller_agents.append((name, agent))
        
        # Find all public methods in the tool
        methods = {}
        for method_name, method in inspect.getmembers(tool_instance, inspect.ismethod):
            if not method_name.startswith('_'):
                methods[method_name] = method
        
        # Register each method as a function with AG2
        from autogen import register_function
        
        for method_name, method in methods.items():
            # Create a function name that includes the tool name for clarity
            function_name = f"{tool_name.lower()}_{method_name}"
            
            # Get the method's docstring for description
            description = inspect.getdoc(method) or f"{method_name} function from {tool_name}"
            
            # Register the function with each caller agent
            for agent_name, agent in caller_agents:
                register_function(
                    method,
                    caller=agent,
                    executor=executor,
                    name=function_name,
                    description=description
                )
                logger.info(f"Registered function {function_name} with agent '{agent_name}'")
    
    def register_tools_from_factory(self, 
                                   tool_names: Optional[List[str]] = None, 
                                   agent_name: Optional[str] = None) -> None:
        """
        Register tools from the ToolFactory with an agent.
        
        Args:
            tool_names: List of tool names to register (if None, register all available tools)
            agent_name: Name of the agent to register tools with (if None, register with all agents)
        """
        if tool_names is None:
            # Get all available tools
            tool_names = ToolFactory.get_available_tools()
            
        for tool_name in tool_names:
            try:
                # Create the tool instance
                tool_instance = ToolFactory.create_tool(tool_name)
                
                # Register the tool with the specified agent(s)
                self.register_tool(tool_instance, agent_name)
                
            except Exception as e:
                logger.error(f"Error registering tool '{tool_name}': {e}")
                
    def register_all_tools(self, agent_name: Optional[str] = None) -> None:
        """
        Register all available tools with an agent.
        
        Args:
            agent_name: Name of the agent to register tools with (if None, register with all agents)
        """
        # This is a convenience method that calls register_tools_from_factory with no tool names
        self.register_tools_from_factory(agent_name=agent_name)
    
    def save_artifact(self, name: str, content: Any, artifact_type: str = "text") -> str:
        """
        Save an artifact produced by the team.
        
        Args:
            name: Name of the artifact
            content: Content of the artifact
            artifact_type: Type of artifact (e.g., 'text', 'image', 'report')
            
        Returns:
            A string identifier for the artifact
        """
        artifact_id = f"{artifact_type}_{name}_{len(self.artifacts)}"
        self.artifacts[artifact_id] = {
            "name": name,
            "content": content,
            "type": artifact_type,
            "timestamp": "now"  # In real implementation, use actual timestamp
        }
        logger.info(f"Saved artifact {artifact_id}")
        return artifact_id
    
    def save_file_artifact(self, content: str, filename: str, directory: str = "outputs") -> str:
        """
        Save an artifact to a file on disk.
        
        Args:
            content: Content to save
            filename: Name of the file
            directory: Directory to save the file in
            
        Returns:
            Path to the saved file
        """
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Save file
        file_path = os.path.join(directory, filename)
        with open(file_path, "w") as f:
            f.write(content)
            
        # Save as artifact too
        self.save_artifact(filename, content, artifact_type="file")
        
        logger.info(f"Saved file artifact to {file_path}")
        return file_path
    
    def _register_tools(self) -> None:
        """
        Register tools with the appropriate agents.
        Override this method in derived classes.
        """
        pass
    
    def enable_swarm(self, shared_context: Optional[Dict[str, Any]] = None) -> None:
        """
        Enable swarm orchestration for this team.
        
        Args:
            shared_context: Initial shared context for the swarm (optional)
        """
        self.swarm_enabled = True
        self.shared_context = shared_context or {}
        logger.info("Swarm orchestration enabled for team")
    
    def register_handoff(self, 
                        agent_name: str, 
                        target_agent_name: str, 
                        condition: str,
                        context_key: Optional[str] = None) -> None:
        """
        Register a conditional handoff between agents for swarm orchestration.
        
        Args:
            agent_name: Name of the source agent
            target_agent_name: Name of the target agent
            condition: Natural language condition for when to hand off
            context_key: Optional context key that must be present for the handoff to be available
        """
        if not self.swarm_enabled:
            logger.warning("Swarm is not enabled. Call enable_swarm() first.")
            return
            
        logger.debug(f"Registering handoff from {agent_name} to {target_agent_name}")
        source_agent = self.get_agent(agent_name)
        target_agent = self.get_agent(target_agent_name)
        
        if source_agent is None:
            logger.error(f"Source agent '{agent_name}' not found")
            return
            
        if target_agent is None:
            logger.error(f"Target agent '{target_agent_name}' not found")
            return
            
        # Initialize handoffs for this agent if not already done
        if agent_name not in self.handoffs:
            self.handoffs[agent_name] = []
            logger.debug(f"Initialized handoffs list for {agent_name}")
            
        # Make the condition unique by prefixing it with agent names and context key
        # This prevents function name collisions in AG2
        unique_condition = f"[{agent_name}->{target_agent_name}"
        if context_key:
            unique_condition += f":{context_key}"
        unique_condition += f"] {condition}"
        logger.debug(f"Created unique condition: {unique_condition}")
            
        # Create the handoff condition
        try:
            handoff = OnCondition(
                target=target_agent,
                condition=unique_condition,
                available=context_key
            )
            logger.debug(f"Created OnCondition object for {agent_name} to {target_agent_name}")
        except Exception as e:
            logger.error(f"Error creating OnCondition: {e}")
            return
        
        # Add to the agent's handoffs
        self.handoffs[agent_name].append(handoff)
        logger.debug(f"Added handoff to {agent_name}'s handoffs list")
        
        logger.info(f"Registered handoff from {agent_name} to {target_agent_name} with condition: {condition}")
    
    def register_default_handoff(self, agent_name: str, target_agent_name: Optional[str] = None) -> None:
        """
        Register a default handoff for an agent when no conditions are met.
        
        Args:
            agent_name: Name of the source agent
            target_agent_name: Name of the target agent (if None, will terminate the swarm)
        """
        if not self.swarm_enabled:
            logger.warning("Swarm is not enabled. Call enable_swarm() first.")
            return
            
        source_agent = self.get_agent(agent_name)
        
        if source_agent is None:
            logger.error(f"Source agent '{agent_name}' not found")
            return
            
        # Initialize handoffs for this agent if not already done
        if agent_name not in self.handoffs:
            self.handoffs[agent_name] = []
            
        # Create the default handoff
        if target_agent_name is None:
            # Terminate the swarm when no conditions are met
            default_handoff = AfterWork(AfterWorkOption.TERMINATE)
        else:
            target_agent = self.get_agent(target_agent_name)
            if target_agent is None:
                logger.error(f"Target agent '{target_agent_name}' not found")
                return
            default_handoff = AfterWork(agent=target_agent)
            
        # Add to the agent's handoffs
        self.handoffs[agent_name].append(default_handoff)
        
        if target_agent_name:
            logger.info(f"Registered default handoff from {agent_name} to {target_agent_name}")
        else:
            logger.info(f"Registered default handoff from {agent_name} to terminate swarm")
    
    def configure_swarm_handoffs(self) -> None:
        """
        Configure all registered handoffs for the swarm.
        This method should be called after all handoffs have been registered.
        """
        if not self.swarm_enabled:
            logger.warning("Swarm is not enabled. Call enable_swarm() first.")
            return
            
        # Register handoffs with AG2
        for agent_name, handoffs in self.handoffs.items():
            agent = self.get_agent(agent_name)
            if agent and handoffs:
                register_hand_off(agent, handoffs)
                logger.info(f"Configured {len(handoffs)} handoffs for agent {agent_name}")
                
        logger.info("Swarm handoffs configured")
    
    def custom_initiate_swarm_chat(
        self, 
        initial_agent: ConversableAgent,
        agents: List[ConversableAgent],
        messages: List[str],
        context_variables: Optional[Dict[str, Any]] = None,
        max_rounds: int = 20
    ) -> Tuple[Any, Dict[str, Any], ConversableAgent]:
        """
        Custom wrapper for initiate_swarm_chat that ensures the conversation continues
        through all agents for the specified number of rounds.
        
        Args:
            initial_agent: The agent to start the conversation
            agents: List of all agents that can participate
            messages: Initial messages to send
            context_variables: Optional context variables
            max_rounds: Maximum number of conversation rounds
            
        Returns:
            Tuple of (chat_result, updated_context, last_agent)
        """
        from loguru import logger
        
        # Start the swarm chat
        logger.debug("Starting custom_initiate_swarm_chat")
        
        # Run the swarm chat with the full max_rounds to allow the conversation to flow through all agents
        chat_result, updated_context, last_agent = initiate_swarm_chat(
            initial_agent=initial_agent,
            agents=agents,
            messages=messages,
            context_variables=context_variables,
            max_rounds=max_rounds  # Use the full max_rounds to allow complete conversation
        )
        
        logger.debug(f"Final response from {last_agent.name if last_agent else 'Unknown'}")
        return chat_result, updated_context, last_agent
    
    def run_swarm(self, 
                initial_agent_name: str, 
                message: str, 
                context_variables: Optional[Dict[str, Any]] = None,
                max_rounds: int = 20) -> Dict[str, Any]:
        """
        Run a scenario using AG2's Swarm orchestration pattern.
        
        Args:
            initial_agent_name: Name of the agent to start the swarm
            message: The initial message to send to the swarm
            context_variables: Optional context variables to initialize the swarm with
            max_rounds: Maximum number of conversation rounds (default: 20)
            
        Returns:
            Dictionary containing the conversation history, context, and results
        """
        logger.debug("Starting run_swarm")
        
        # Get the initial agent
        logger.debug(f"Getting initial agent: {initial_agent_name}")
        initial_agent = self.get_agent(initial_agent_name)
        if not initial_agent:
            raise ValueError(f"Agent {initial_agent_name} not found")
        logger.debug(f"Initial agent found: {initial_agent_name}")
        
        # Prepare context variables
        logger.debug("Preparing context variables")
        context = context_variables or {}
        logger.debug(f"Context keys: {list(context.keys())}")
        
        # Get all agents
        logger.debug("Getting all agents")
        all_agents = list(self.agents.values())
        logger.debug(f"Found {len(all_agents)} agents")
        
        # Add explicit handoff instructions to the message if not already present
        if "Agent Handoff Instructions" not in message:
            handoff_instructions = """
            ## Agent Handoff Instructions:
            - ProductManager: After defining the research scope, explicitly hand off to the Researcher by saying "@Researcher, please proceed with the research."
            - Researcher: After analyzing the information, explicitly hand off to the ToolUser by saying "@ToolUser, please execute the necessary tools."
            - ToolUser: After executing the tools, explicitly hand off to the ReportWriter by saying "@ReportWriter, please compile the report."
            - ReportWriter: After compiling the report, explicitly hand off to the ProductManager by saying "@ProductManager, please review the report."
            
            Please ensure a complete research cycle with all agents participating as needed.
            """
            enhanced_message = message + "\n\n" + handoff_instructions
        else:
            enhanced_message = message
            
        # Log the enhanced message for debugging
        logger.debug(f"Enhanced message: {enhanced_message[:200]}... (truncated)")
        
        # Run the swarm
        logger.info(f"Starting swarm with initial agent {initial_agent_name}")
        logger.debug("Calling custom_initiate_swarm_chat")
        try:
            chat_result, updated_context, last_agent = self.custom_initiate_swarm_chat(
                initial_agent=initial_agent,
                agents=all_agents,
                messages=[enhanced_message],  # Use the enhanced message with handoff instructions
                context_variables=context,
                max_rounds=max_rounds  # Use the provided max_rounds parameter
            )
            logger.debug("custom_initiate_swarm_chat completed successfully")
            logger.debug(f"Last agent: {last_agent.name if last_agent else 'None'}")
            
            # Log the chat history for debugging
            if hasattr(chat_result, "chat_history"):
                logger.debug(f"Chat history length: {len(list(chat_result.chat_history))}")
                for i, msg in enumerate(chat_result.chat_history):
                    sender = getattr(msg, "sender", "Unknown")
                    content = getattr(msg, "content", "")
                    logger.debug(f"Message {i+1} from {sender}: {content[:100]}... (truncated)")
        except Exception as e:
            logger.error(f"Error in custom_initiate_swarm_chat: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
        
        # Update the team's shared context with the results from the swarm
        logger.debug("Updating shared context")
        if updated_context:
            self.shared_context.update(updated_context)
            
        # Prepare the result
        logger.debug("Preparing result")
        result = {
            "chat_history": chat_result,
            "context": updated_context,
            "last_agent": last_agent.name if last_agent else None
        }
        
        logger.debug("run_swarm completed")
        return result
    
    def run_scenario(
        self, 
        prompt: str, 
        user_proxy: Optional[ConversableAgent] = None, 
        sender_agent_name: Optional[str] = None,
        receiver_agent_name: Optional[str] = None,
        max_rounds: int = 10,
        use_swarm: bool = False,
        context_variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run a scenario with the team, starting with a prompt.
        
        Args:
            prompt: The initial prompt to start the conversation
            user_proxy: Optional user proxy agent to use (will create one if not provided)
            sender_agent_name: Name of the agent that will send the initial message
            receiver_agent_name: Name of the agent that will receive the initial message
            max_rounds: Maximum number of conversation rounds (default: 10)
            use_swarm: Whether to use swarm orchestration (default: False)
            context_variables: Optional context variables for swarm mode
            
        Returns:
            Dictionary containing the conversation history and results
        """
        logger.debug("Starting run_scenario")
        
        # If swarm mode is requested and enabled, use run_swarm instead
        if use_swarm and self.swarm_enabled:
            logger.debug("Using swarm orchestration")
            initial_agent = receiver_agent_name or list(self.agents.keys())[0]
            logger.debug(f"Initial agent for swarm: {initial_agent}")
            try:
                return self.run_swarm(
                    initial_agent_name=initial_agent,
                    message=prompt,
                    context_variables=context_variables
                )
            except Exception as e:
                logger.error(f"Error in run_swarm: {e}")
                import traceback
                logger.error(traceback.format_exc())
                raise
        
        # Create a user proxy if not provided
        logger.debug("Using standard conversation flow")
        if user_proxy is None:
            try:
                logger.debug("Creating user proxy agent")
                from autogen import UserProxyAgent
                
                user_proxy = UserProxyAgent(
                    name="User",
                    human_input_mode="NEVER",
                    code_execution_config={"use_docker": False}
                )
                logger.debug("User proxy agent created")
            except Exception as e:
                logger.error(f"Error creating user proxy: {e}")
                import traceback
                logger.error(traceback.format_exc())
                raise
        
        # Determine sender and receiver agents
        logger.debug("Determining sender and receiver agents")
        sender = user_proxy
        
        if sender_agent_name:
            sender_agent = self.get_agent(sender_agent_name)
            if sender_agent:
                sender = sender_agent
                logger.debug(f"Using {sender_agent_name} as sender")
            else:
                logger.warning(f"Sender agent '{sender_agent_name}' not found, using user proxy instead")
        
        if not receiver_agent_name:
            # Use the first agent in the team as the default receiver
            receiver_agent_name = list(self.agents.keys())[0]
            logger.debug(f"No receiver specified, using {receiver_agent_name}")
        
        receiver = self.get_agent(receiver_agent_name)
        if not receiver:
            logger.error(f"Receiver agent '{receiver_agent_name}' not found")
            raise ValueError(f"Receiver agent '{receiver_agent_name}' not found")
        
        logger.debug(f"Using {receiver_agent_name} as receiver")
        
        # Run the conversation
        logger.debug(f"Starting conversation with max_rounds={max_rounds}")
        try:
            chat_result = sender.initiate_chat(
                recipient=receiver,
                message=prompt,
                max_turns=max_rounds
            )
            logger.debug("Conversation completed successfully")
        except Exception as e:
            logger.error(f"Error in conversation: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
        
        # Prepare result
        logger.debug("Preparing result")
        result = {
            "status": "success",
            "agents": list(self.agents.keys()),
            "conversation": chat_result,
            "artifacts": self.artifacts
        }
        
        logger.debug("run_scenario completed")
        return result

    def start_chat(self, message: str) -> None:
        """Start a chat between team members.
        
        Args:
            message: Initial message to start the conversation
        """
        if not self.agents:
            logger.warning("No agents in team to start chat")
            return
        
        # Get the first agent to start the conversation
        initiator = self.agents[0]
        recipients = self.agents[1:]
        
        # Start the chat
        initiator.initiate_chat(
            recipients,
            message=message
        )
