import autogen
from typing import Dict, Any, Optional
from autogen import AssistantAgent, SwarmResult

def update_product_spec(spec: Dict[str, Any], context_variables: Dict[str, Any]) -> SwarmResult:
    """Update the product specification in the shared context."""
    # Update reviews counter
    reviews_left = context_variables.get("reviews_left", 0)
    if reviews_left > 0:
        context_variables["reviews_left"] = reviews_left - 1
    
    # Store current spec in history
    if "spec_history" not in context_variables:
        context_variables["spec_history"] = []
    if "product_spec" in context_variables:
        context_variables["spec_history"].append(context_variables["product_spec"])
    
    # Update the current spec
    context_variables["product_spec"] = spec
    
    # Return SwarmResult with updated context
    return SwarmResult(context_variables=context_variables)

def get_current_spec(context_variables: Dict[str, Any]) -> Dict[str, Any]:
    """Get the current product specification."""
    return context_variables.get("product_spec", {})

class ProductManager(AssistantAgent):
    """Product manager agent responsible for detailed specifications.
    
    Acts as a technical product manager who translates high-level strategy
    into detailed, actionable technical specifications and requirements.
    """
    
    DEFAULT_SYSTEM_MESSAGE = """You are a senior product manager responsible for:
    1. Converting high-level vision and strategy into detailed specifications
    2. Breaking down features into implementable components
    3. Defining clear acceptance criteria and requirements
    4. Ensuring specifications are clear, testable, and achievable
    
    When you receive strategic analysis, create detailed specifications including:
    - Feature Breakdown
    - Technical Requirements
    - User Stories
    - Acceptance Criteria
    - Implementation Priorities
    
    Always output specifications in a clear, structured JSON format."""

    def __init__(self, **kwargs):
        """Initialize the product manager agent with default settings."""
        super().__init__(
            name="product_manager",
            system_message=self.DEFAULT_SYSTEM_MESSAGE,
            functions=[update_product_spec, get_current_spec],
            **kwargs
        ) 