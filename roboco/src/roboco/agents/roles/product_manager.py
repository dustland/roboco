import autogen
from typing import Dict, Any, Optional
from autogen import SwarmAgent, SwarmResult

def update_product_spec(spec: Dict[str, Any], context_variables: Dict[str, Any]) -> SwarmResult:
    """Update the product specification in the shared context."""
    if "product_spec" not in context_variables:
        context_variables["product_spec"] = {}
    
    # Merge new specifications with existing ones
    context_variables["product_spec"].update(spec)
    
    # Record specification history
    if "spec_history" not in context_variables:
        context_variables["spec_history"] = []
    
    context_variables["spec_history"].append({
        "timestamp": context_variables.get("current_timestamp", "unknown"),
        "spec_update": spec,
        "reviews_remaining": context_variables.get("reviews_left", 0)
    })
    
    # Determine next agent based on context
    next_agent = "executive" if context_variables.get("reviews_left", 0) > 0 else "user_proxy"
    
    return SwarmResult(
        context_variables=context_variables,
        next_agent=next_agent
    )

def get_current_spec(context_variables: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieve the current product specification."""
    return context_variables.get("product_spec", {})

class ProductManager(SwarmAgent):
    """Product manager agent responsible for detailed specifications.
    
    Acts as a technical product manager who translates high-level strategy
    into detailed, actionable technical specifications and requirements.
    """
    
    DEFAULT_SYSTEM_MESSAGE = """You are a technical product manager responsible for:
    1. Creating detailed technical specifications from strategic visions
    2. Defining specific feature requirements and acceptance criteria
    3. Planning development phases and technical milestones
    4. Breaking down high-level objectives into actionable tasks
    5. Ensuring technical feasibility and implementation clarity
    
    Work with the executive to translate strategic vision into detailed specifications.
    Your output should include:
    - Detailed Technical Requirements
    - API Specifications
    - Data Models
    - Integration Requirements
    - Performance Criteria
    - Development Milestones
    
    Always output your specifications in a clear, structured JSON format that can be
    directly used by development teams."""

    def __init__(self, **kwargs):
        """Initialize the product manager agent with default settings."""
        super().__init__(
            name="product_manager",
            system_message=self.DEFAULT_SYSTEM_MESSAGE,
            functions=[update_product_spec, get_current_spec],
            **kwargs
        ) 