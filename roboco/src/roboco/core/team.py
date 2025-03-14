"""
Team Management Module

This module provides base classes for organizing agents into teams and managing their interactions.
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from loguru import logger
import inspect

import autogen
from autogen import ConversableAgent

from roboco.core.config import load_config_from_file, get_llm_config
from roboco.core.agent import Agent
from roboco.core.tool_factory import ToolFactory


class Team:
    """
    Base class for all roboco teams, providing common functionality for team management.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the team with configuration.
        
        Args:
            config_path: Path to the configuration file (optional)
        """
        # Load configuration
        self.config_path = config_path
        if self.config_path is None:
            # Try to find config in the current directory
            current_dir = Path.cwd()
            default_config = current_dir / "config.toml"
            if default_config.exists():
                self.config_path = str(default_config)
            else:
                logger.warning("No config_path provided and no default config.toml found")
                
        # Load configuration if available
        self.config = {}
        if self.config_path:
            self.config = load_config_from_file(self.config_path)
            
        # Get LLM configuration
        self.llm_config = get_llm_config(self.config)
        
        # Initialize agents dictionary
        self.agents = {}
        
        # Initialize tools registry
        self.tools = {}
        
        # Storage for output artifacts
        self.artifacts = {}
        
        logger.info(f"Initialized team with configuration from {self.config_path}")
    
    def add_agent(self, agent_name: str, agent: ConversableAgent) -> None:
        """
        Add an agent to the team.
        
        Args:
            agent_name: Name of the agent
            agent: The agent instance
        """
        self.agents[agent_name] = agent
        logger.info(f"Added agent '{agent_name}' to the team")
    
    def get_agent(self, agent_name: str) -> Optional[ConversableAgent]:
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
        
        # Get functions from the tool
        functions = {}
        if hasattr(tool_instance, "get_functions"):
            functions = tool_instance.get_functions()
        else:
            # Use reflection to extract public methods
            for method_name, method in inspect.getmembers(tool_instance, inspect.ismethod):
                if not method_name.startswith('_'):
                    function_key = f"{tool_name}_{method_name}"
                    functions[function_key] = method
            
            if not functions:
                logger.warning(f"Tool {tool_name} does not have any public methods")
                return
        
        # Register with specified agent or all agents
        if agent_name:
            agent = self.get_agent(agent_name)
            if agent and hasattr(agent, "register_function"):
                agent.register_function(function_map=functions)
                logger.info(f"Registered {len(functions)} functions from {tool_name} with agent '{agent_name}'")
            else:
                logger.warning(f"Could not register tool with agent '{agent_name}'")
        else:
            # Register with all agents that support it
            for name, agent in self.agents.items():
                if hasattr(agent, "register_function"):
                    agent.register_function(function_map=functions)
                    logger.info(f"Registered {len(functions)} functions from {tool_name} with agent '{name}'")
                    
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
    
    def run_scenario(
        self, 
        prompt: str, 
        user_proxy: Optional[ConversableAgent] = None, 
        sender_agent_name: Optional[str] = None,
        receiver_agent_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run a scenario with the team, starting with a prompt.
        
        Args:
            prompt: The initial prompt to start the conversation
            user_proxy: Optional user proxy agent to use (will create one if not provided)
            sender_agent_name: Name of the agent that will send the initial message
            receiver_agent_name: Name of the agent that will receive the initial message
            
        Returns:
            Dictionary containing the conversation history and results
        """
        try:
            # Create a UserProxyAgent if not provided
            if user_proxy is None:
                user_proxy = autogen.UserProxyAgent(
                    name="User",
                    human_input_mode="NEVER",
                    code_execution_config={"use_docker": False},
                    llm_config=False  # No LLM for user proxy
                )
                
            # Determine sender and receiver
            if sender_agent_name is None:
                sender = user_proxy
            else:
                # Get the sender agent from our collection (not from the user_proxy)
                sender = self.get_agent(sender_agent_name)
                if sender is None:  # Use is None instead of not sender
                    raise ValueError(f"Sender agent '{sender_agent_name}' not found")
                
            if receiver_agent_name is None:
                # Use the first agent that's not the sender
                receiver = None  # Initialize receiver variable
                for name, agent in self.agents.items():
                    if agent != sender:
                        receiver = agent
                        break
                
                if receiver is None:
                    raise ValueError("No suitable receiver agent found")
            else:
                # Get the receiver agent from our collection (not from the user_proxy)
                receiver = self.get_agent(receiver_agent_name)
                if receiver is None:  # Use is None instead of not receiver
                    raise ValueError(f"Receiver agent '{receiver_agent_name}' not found")
            
            # Start the conversation - using autogen's built-in method
            chat_result = sender.initiate_chat(
                recipient=receiver,
                message=prompt
            )
            
            # Prepare conversation history
            all_agents = {}
            
            # Add team agents to the collection
            for name, agent in self.agents.items():
                all_agents[name] = agent
            
            # Add user_proxy separately with its proper name
            all_agents[user_proxy.name] = user_proxy
            
            # Extract conversation histories
            conversation = {}
            for name, agent in all_agents.items():
                if hasattr(agent, "chat_history") and agent.chat_history is not None:
                    # Create a copy of the chat history if possible
                    try:
                        conversation[name] = agent.chat_history.copy()
                    except (AttributeError, TypeError):
                        # If the chat_history doesn't have a copy method, use it directly
                        conversation[name] = agent.chat_history
                else:
                    conversation[name] = []
            
            # Prepare result
            result = {
                "status": "success",
                "agents": list(all_agents.keys()),
                "conversation": conversation,
                "artifacts": self.artifacts,
            }
            
            return result
        except Exception as e:
            import traceback
            trace = traceback.format_exc()
            logger.error(f"Error in run_scenario: {e}")
            logger.debug(f"Traceback: {trace}")
            return {
                "status": "error",
                "error": str(e),
                "traceback": trace,
                "agents": list(self.agents.keys()),
                "artifacts": self.artifacts
            }
