import autogen

class UserProxy(autogen.UserProxyAgent):
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
            code_execution_config=False,
            human_input_mode="NEVER",
            **kwargs
        ) 