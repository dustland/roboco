"""Product manager agent implementation."""

import autogen

from roboco.core.types import AgentRole

class ProductManagerAgent(autogen.AssistantAgent):
    """Product Manager agent responsible for creating detailed specifications."""
    
    def __init__(self, **kwargs):
        system_message = """You are the Product Manager agent responsible for creating detailed specifications.
Your responsibilities:
- Take the vision and Executive Board's direction as input
- Create detailed product specifications
- Define clear success criteria and metrics
- Ensure specifications are practical and achievable

Focus on creating clear, actionable specifications that align with the vision.
Break down complex requirements into manageable tasks."""

        super().__init__(
            name="ProductManager",
            system_message=system_message,
            **kwargs
        )
        self.role = AgentRole.PRODUCT_MANAGER 