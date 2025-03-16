"""
Researcher Agent Module

This module provides the Researcher agent implementation for analyzing data and extracting insights.
"""

from typing import Dict, Any, Optional, List

# ag2 and autogen are identical packages
from autogen import SwarmResult

# Import the Agent class from our core module
from roboco.core.agent import Agent

def analyze_data(data: Dict[str, Any], context_variables: Dict[str, Any]) -> SwarmResult:
    """Analyze data and update the analysis in the shared context."""
    # Store current analysis in history
    if "analysis_history" not in context_variables:
        context_variables["analysis_history"] = []
    if "analysis" in context_variables:
        context_variables["analysis_history"].append(context_variables["analysis"])
    
    # Update the current analysis
    if "analysis" not in context_variables:
        context_variables["analysis"] = []
    
    context_variables["analysis"].append(data)
    
    # Return SwarmResult with updated context
    return SwarmResult(context_variables=context_variables)

def get_current_analysis(context_variables: Dict[str, Any]) -> Dict[str, Any]:
    """Get the current analysis."""
    return context_variables.get("analysis", [])

class Researcher(Agent):
    """Researcher agent responsible for analyzing data and extracting insights.
    
    Specializes in processing raw information, identifying patterns, and extracting
    actionable insights from various data sources.
    """
    
    DEFAULT_SYSTEM_MESSAGE = """You are a skilled market researcher who specializes in analyzing data and 
    extracting insights. Your job is to analyze search results, organize information, and identify key trends.
    
    When given raw search results, you should:
    1. Identify key market trends and patterns
    2. Analyze competitor information
    3. Extract customer needs and pain points
    4. Organize information in a structured format
    5. Provide actionable insights based on the data
    
    You have access to these research tools:
    - WebSearchTool: For finding relevant information on the web
    - FileSystemTool: For saving and retrieving your analysis
    
    When analyzing data, follow these steps:
    1. Review all search results thoroughly
    2. Identify the most relevant information
    3. Look for patterns and trends across multiple sources
    4. Categorize information by topic, company, or technology
    5. Identify gaps in the research that need further investigation
    6. Summarize your findings in a clear, structured format
    
    Your analysis should be:
    - Objective and based on evidence
    - Well-organized with clear sections
    - Focused on actionable insights
    - Comprehensive but concise
    """
    
    def __init__(
        self,
        name: str = "Researcher",
        system_message: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        config_path: Optional[str] = None,
        terminate_msg: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the Researcher agent.
        
        Args:
            name: Name of the agent (default: "Researcher")
            system_message: Custom system message for the agent
            tools: Optional list of tools available to the agent
            config_path: Optional path to agent configuration file
            terminate_msg: Optional message to include at the end of responses to signal completion
            **kwargs: Additional arguments to pass to the base Agent class
        """
        # Set default system message if not provided
        if system_message is None:
            system_message = self.DEFAULT_SYSTEM_MESSAGE
            
        # Initialize the base agent
        super().__init__(
            name=name,
            system_message=system_message,
            tools=tools,
            config_path=config_path,
            terminate_msg=terminate_msg,
            **kwargs
        )
        
        # Register functions for swarm mode
        self.register_for_swarm([
            analyze_data,
            get_current_analysis
        ])
    
    def register_for_swarm(self, functions):
        """Register functions for swarm mode."""
        # This is a placeholder for future implementation
        # Will be used to register functions with the agent for swarm mode
        pass
