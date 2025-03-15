"""
Tool User Agent Module

This module provides the ToolUser agent implementation for executing tools and functions.
"""

from typing import Dict, Any, Optional, List
import os
from autogen import UserProxyAgent, SwarmResult

def store_search_results(results: List[Dict[str, Any]], context_variables: Dict[str, Any]) -> SwarmResult:
    """Store search results in the shared context."""
    # Initialize search_results if it doesn't exist
    if "search_results" not in context_variables:
        context_variables["search_results"] = []
    
    # Add the new results
    context_variables["search_results"].append(results)
    
    # Return SwarmResult with updated context
    return SwarmResult(context_variables=context_variables)

def get_search_results(context_variables: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get all search results from the shared context."""
    return context_variables.get("search_results", [])

class ToolUser(UserProxyAgent):
    """Tool user agent responsible for executing tools and functions.
    
    This agent acts as a proxy for executing tools and functions, such as web searches,
    file operations, and other external actions.
    """
    
    DEFAULT_SYSTEM_MESSAGE = """You are a tool execution agent that helps other agents by running tools and functions.
    Your primary responsibility is to execute requested tools accurately and report the results back.
    
    You can execute:
    1. Web searches to find information
    2. File operations to save and retrieve data
    3. Other tools as they become available
    
    When executing tools:
    - Follow instructions precisely
    - Report results clearly
    - Handle errors gracefully
    - Provide relevant context with results
    
    Do not make decisions about what to search for or what to analyze - simply execute the tools
    as requested by other agents and return the results.
    """
    
    def __init__(self, name: str = "ToolUser", **kwargs):
        """
        Initialize the ToolUser agent.
        
        Args:
            name: Name of the agent (default: "ToolUser")
            **kwargs: Additional arguments to pass to the UserProxyAgent
        """
        # Set default values if not provided
        if 'human_input_mode' not in kwargs:
            kwargs['human_input_mode'] = "NEVER"
            
        if 'code_execution_config' not in kwargs:
            kwargs['code_execution_config'] = {
                "last_n_messages": 3, 
                "work_dir": "workspace", 
                "use_docker": False
            }
            
        # Set default system message if not provided
        if 'system_message' not in kwargs:
            kwargs['system_message'] = self.DEFAULT_SYSTEM_MESSAGE
            
        # Initialize the UserProxyAgent
        super().__init__(name=name, **kwargs)
        
        # Create workspace directory if it doesn't exist
        os.makedirs("workspace", exist_ok=True)
        
        # Register functions for swarm mode
        self.register_for_swarm([
            store_search_results,
            get_search_results
        ])
    
    def register_for_swarm(self, functions: List[callable]):
        """Register functions for swarm mode."""
        # This is a placeholder for future implementation
        # Will be used to register functions with the agent for swarm mode
        pass
