"""Product manager agent implementation."""

from typing import Dict, Any, Optional, List
from roboco.core import Agent

def update_product_spec(spec: Dict[str, Any], context_variables: Dict[str, Any]) -> Dict[str, Any]:
    """Update the product specification in the shared context.
    
    Args:
        spec: The new product specification to store
        context_variables: The current context variables
        
    Returns:
        The updated context variables
    """
    # Store current spec in history
    if "spec_history" not in context_variables:
        context_variables["spec_history"] = []
    if "product_spec" in context_variables:
        context_variables["spec_history"].append(context_variables["product_spec"])
    
    # Update the current spec
    context_variables["product_spec"] = spec
    
    return context_variables

def get_current_spec(context_variables: Dict[str, Any]) -> Dict[str, Any]:
    """Get the current product specification.
    
    Args:
        context_variables: The current context variables
        
    Returns:
        The current product specification
    """
    return context_variables.get("product_spec", {})

class ProductManager(Agent):
    """Agent that acts as a product manager, conducting research and analysis."""

    def __init__(
        self,
        name: str = "ProductManager",
        system_message: Optional[str] = None,
        _tools: Optional[List[Any]] = None,
        config_path: Optional[str] = None,
        **kwargs
    ):
        """Initialize the ProductManager agent.
        
        Args:
            name: Name of the agent
            system_message: Custom system message for the agent
            _tools: Optional list of tools available to the agent
            config_path: Optional path to agent configuration file
            **kwargs: Additional arguments passed to Agent
        """
        if system_message is None:
            system_message = """You are a Product Manager specializing in robotics technology.
            Use available tools to research and provide detailed, accurate information.
            Focus on:
            1. Latest technological developments
            2. Market trends and applications
            3. Key challenges and solutions
            Always cite your sources and provide specific examples."""

        super().__init__(
            name=name,
            system_message=system_message,
            _tools=_tools,
            config_path=config_path,
            **kwargs
        )
    
    def analyze_strategy(self, content: str) -> Dict[str, Any]:
        """Analyze strategic content and generate product specifications.
        
        Args:
            content: The strategic content to analyze
            
        Returns:
            A dictionary containing the product specification
        """
        spec = {
            "features": [
                "Core functionality for embodied AI integration",
                "Data collection and processing pipelines", 
                "User interface for monitoring and control",
                "API for third-party extensions"
            ],
            "technical_requirements": [
                "Real-time processing capabilities",
                "Scalable architecture",
                "Secure communication protocols",
                "Cross-platform compatibility"
            ],
            "priorities": [
                "Establish core framework",
                "Develop basic sensor integration",
                "Implement control mechanisms",
                "Add advanced AI capabilities"
            ]
        }
        
        return spec