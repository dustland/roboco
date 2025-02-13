"""Executive board agent implementation."""

import autogen

from roboco.core.types import AgentRole

class ExecutiveBoardAgent(autogen.AssistantAgent):
    """Executive Board agent responsible for strategic direction and orchestration."""
    
    def __init__(self, **kwargs):
        system_message = """You are the Executive Board agent responsible for strategic direction and orchestration.
Your responsibilities:
- Analyze the vision from the human operator
- Coordinate with Product Manager to create specifications
- Make strategic decisions about robot adaptation
- Ensure alignment between vision and implementation

Always consider market needs, technical feasibility, and resource constraints in your decisions.
Coordinate the work between other agents and maintain focus on the vision."""

        super().__init__(
            name="ExecutiveBoard",
            system_message=system_message,
            **kwargs
        )
        self.role = AgentRole.EXECUTIVE_BOARD 