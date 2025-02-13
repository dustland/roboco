"""Human agent implementation."""

import autogen

from roboco.core.types import AgentRole

class HumanAgent(autogen.UserProxyAgent):
    """Human agent that provides the vision and interacts with the system."""
    
    def __init__(self, **kwargs):
        system_message = """You are a human operator interacting with the RoboCo system.
You will provide the vision for robot adaptation and validate the specifications."""

        super().__init__(
            name="Human",
            system_message=system_message,
            human_input_mode="ALWAYS",
            code_execution_config={"work_dir": "workspace"},
            **kwargs
        )
        self.role = AgentRole.HUMAN 