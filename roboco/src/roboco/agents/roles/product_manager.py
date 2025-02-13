import autogen

class ProductManager(autogen.AssistantAgent):
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
            **kwargs
        ) 