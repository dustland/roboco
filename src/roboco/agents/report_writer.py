"""
Report Writer Agent Module

This module provides the ReportWriter agent implementation for creating well-structured reports.
"""

from typing import Dict, Any, Optional, List

# ag2 and autogen are identical packages
from autogen import SwarmResult

# Import the Agent class from our core module
from roboco.core.agent import Agent

def create_report(report_content: str, context_variables: Dict[str, Any]) -> SwarmResult:
    """Create a report and update the report content in the shared context."""
    # Store current report in history if it exists
    if "report_history" not in context_variables:
        context_variables["report_history"] = []
    if "report_content" in context_variables and context_variables["report_content"]:
        context_variables["report_history"].append(context_variables["report_content"])
    
    # Update the current report
    context_variables["report_content"] = report_content
    
    # Mark the status as complete
    context_variables["status"] = "complete"
    
    # Return SwarmResult with updated context
    return SwarmResult(context_variables=context_variables)

def get_current_report(context_variables: Dict[str, Any]) -> str:
    """Get the current report content."""
    return context_variables.get("report_content", "")

class ReportWriter(Agent):
    """Report writer agent responsible for creating well-structured reports.
    
    Specializes in transforming research and analysis into comprehensive, 
    well-organized reports with clear recommendations.
    """
    
    DEFAULT_SYSTEM_MESSAGE = """You are a professional report writer who specializes in creating 
    clear, concise, and well-structured market research reports. Your job is to take analyzed information 
    and create comprehensive reports that are easy to understand.
    
    When creating reports, you should:
    1. Use clear headings and subheadings
    2. Include an executive summary
    3. Present data in a logical flow
    4. Use bullet points for key findings
    5. Provide recommendations based on the research
    6. Format the report in markdown for readability
    
    You have access to these tools:
    - FileSystemTool: For saving your reports and accessing analysis
    
    Your reports should follow this structure:
    
    # Title
    
    ## Executive Summary
    Brief overview of the key findings and recommendations.
    
    ## Introduction
    Context and objectives of the research.
    
    ## Market Analysis
    Overview of the current market landscape.
    
    ## Key Findings
    Detailed presentation of research findings, organized by theme.
    
    ## Competitor Analysis
    Analysis of key players in the market.
    
    ## Opportunities and Challenges
    Identification of potential opportunities and challenges.
    
    ## Recommendations
    Strategic recommendations based on the research.
    
    ## Conclusion
    Summary of the main points and next steps.
    
    Always format your reports in markdown for better readability.
    """
    
    def __init__(
        self,
        name: str = "ReportWriter",
        system_message: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        config_path: Optional[str] = None,
        terminate_msg: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the ReportWriter agent.
        
        Args:
            name: Name of the agent (default: "ReportWriter")
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
            create_report,
            get_current_report
        ])
    
    def register_for_swarm(self, functions: List[callable]):
        """Register functions for swarm mode."""
        # This is a placeholder for future implementation
        # Will be used to register functions with the agent for swarm mode
        pass
