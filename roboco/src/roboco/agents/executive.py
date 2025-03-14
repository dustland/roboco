import autogen
from typing import Dict, Any, Optional
from autogen import AssistantAgent, SwarmResult

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

class Executive(AssistantAgent):
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

    def __init__(self, **kwargs):
        """Initialize the executive agent with default settings."""
        super().__init__(
            name="executive",
            system_message=self.DEFAULT_SYSTEM_MESSAGE,
            functions=[record_analysis],
            **kwargs
        )
        self.register_reply(
            trigger=lambda msg: "vision" in msg.get("content", "").lower(),
            reply_func=record_analysis,
            config={"context_variables": True}
        )
        
    def determine_next_agent(self, context_variables: Dict[str, Any]) -> Optional[str]:
        """Determine the next agent based on current context."""
        if not context_variables.get("product_spec"):
            return "product_manager"  # Need initial specifications
        elif context_variables.get("reviews_left", 0) > 0:
            return "product_manager"  # Continue review cycle
        else:
            return "user_proxy"  # Finalize results 