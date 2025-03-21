import autogen
from typing import Dict, Any, Optional, List
from autogen import SwarmResult

# Import the Agent class from our core module
from roboco.core.agent import Agent

def record_analysis(analysis: str, context_variables: Dict[str, Any]) -> SwarmResult:
    """Record the strategic analysis in the shared context."""
    if "analyses" not in context_variables:
        context_variables["analyses"] = []
    
    # Record the analysis
    context_variables["analyses"].append({
        "timestamp": context_variables.get("current_timestamp", "unknown"),
        "content": analysis
    })
    
    # Update the current analysis
    context_variables["current_analysis"] = analysis
    
    # Return SwarmResult with updated context
    return SwarmResult(context_variables=context_variables)

class Executive(Agent):
    """Executive agent responsible for high-level vision and strategy.
    
    Acts as a senior executive who understands both business and technical aspects,
    focusing on strategic planning and high-level architecture decisions.
    """
    
    DEFAULT_SYSTEM_MESSAGE = """You are a senior executive responsible for:
    1. Analyzing and structuring product visions strategically
    2. Breaking down high-level goals into clear objectives
    3. Making architectural and strategic technical decisions
    4. Ensuring alignment between business goals and technical implementation
    
    When you receive a vision, structure it into:
    - Overview & Strategic Context
    - Key Business Objectives
    - Technical Success Metrics
    - Risk Factors & Mitigation Strategies
    - Architectural Recommendations
    
    Always output your analysis in a clear, structured JSON format."""

    def __init__(
        self,
        name: str = "Executive",
        system_message: Optional[str] = None,
        tools: Optional[List[Any]] = None,  # Kept for backward compatibility but not used
        config_path: Optional[str] = None,
        terminate_msg: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the Executive agent.
        
        Args:
            name: Name of the agent (default: "Executive")
            system_message: Custom system message for the agent
            tools: Optional list of tools available to the agent (not used, kept for compatibility)
            config_path: Optional path to agent configuration file
            terminate_msg: Optional message to include at the end of responses to signal completion
            **kwargs: Additional arguments to pass to the base Agent class
        """
        # Set default system message if not provided
        if system_message is None:
            system_message = self.DEFAULT_SYSTEM_MESSAGE
            
        # Create function map for record_analysis
        function_map = {
            "record_analysis": record_analysis
        }
        
        # Filter out 'tools' parameter to avoid ConversableAgent error
        safe_kwargs = {k: v for k, v in kwargs.items() if k != 'tools'}
        
        # Initialize the base agent
        super().__init__(
            name=name,
            system_message=system_message,
            config_path=config_path,
            terminate_msg=terminate_msg,
            function_map=function_map,
            **safe_kwargs
        )
        
        # Register custom reply for vision-related messages
        self.register_reply(
            trigger="vision",  # Trigger based on the message containing "vision"
            reply_func=self._reply_to_vision_request,
        )
    
    def _reply_to_vision_request(self, msg):
        """Custom reply function for vision-related messages."""
        # Extract the message content
        content = msg.get("content", "")
        
        # Generate a structured analysis of the vision
        response = f"""Thank you for sharing your vision. Let me analyze it strategically:

### Strategic Analysis
{content}

I've identified the following key elements:
1. Business objectives: [Extracted from vision]
2. Technical requirements: [Extracted from vision]
3. Success metrics: [Extracted from vision]
4. Potential risks: [Extracted from vision]

Is there any specific aspect of this vision you'd like me to elaborate on?"""
        
        return response
    
    def determine_next_agent(self, context_variables: Dict[str, Any]) -> Optional[str]:
        """Determine the next agent to hand off to based on the current context."""
        # Simple logic for demonstration - can be expanded based on complex heuristics
        if context_variables.get("requires_research", False):
            return "Researcher"
        elif context_variables.get("requires_implementation", False):
            return "SoftwareEngineer"
        elif context_variables.get("requires_summary", False):
            return "ReportWriter"
        
        # Default handoff to Product Manager
        return "ProductManager"