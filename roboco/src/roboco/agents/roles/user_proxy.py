import autogen
from typing import Dict, Any, Optional
from autogen import SwarmAgent, SwarmResult

def record_vision(vision: str, context_variables: Dict[str, Any]) -> SwarmResult:
    """Record the product vision in the shared context."""
    context_variables["vision"] = vision
    context_variables["current_timestamp"] = "now"  # In a real implementation, use actual timestamp
    
    # Initialize or reset product context
    context_variables["product_spec"] = {}
    context_variables["analyses"] = []
    context_variables["spec_history"] = []
    context_variables["reviews_left"] = 2  # Reset review counter
    
    # Always go to executive first for vision analysis
    return SwarmResult(
        context_variables=context_variables,
        next_agent="executive"
    )

def get_final_result(context_variables: Dict[str, Any]) -> Dict[str, Any]:
    """Get the final result including vision, analysis, and specifications."""
    # Ensure we're really done
    if context_variables.get("reviews_left", 0) > 0:
        return SwarmResult(
            context_variables=context_variables,
            next_agent="executive"  # Continue the review cycle
        )
        
    return {
        "vision": context_variables.get("vision", ""),
        "analysis": context_variables.get("current_analysis", {}),
        "specification": context_variables.get("product_spec", {}),
        "history": {
            "analyses": context_variables.get("analyses", []),
            "spec_history": context_variables.get("spec_history", [])
        }
    }

class UserProxy(SwarmAgent):
    """User proxy agent that acts as a bridge between human users and other agents.
    
    This agent facilitates communication between human users and the agent system,
    handling input/output and maintaining conversation context.
    """

    DEFAULT_SYSTEM_MESSAGE = """You are a user proxy responsible for:
    1. Facilitating communication between humans and the agent system
    2. Formatting human inputs appropriately for other agents
    3. Ensuring clear and structured responses back to humans
    4. Maintaining conversation context and flow
    
    Focus on clear communication and proper message formatting."""

    def __init__(self, **kwargs):
        """Initialize the user proxy agent with default settings."""
        super().__init__(
            name="user_proxy",
            system_message=self.DEFAULT_SYSTEM_MESSAGE,
            functions=[record_vision, get_final_result],
            code_execution_config=False,
            human_input_mode="NEVER",
            **kwargs
        ) 