from typing import Dict, Any, Optional
from autogen import SwarmResult

# Import the Agent class from our core module
from roboco.core.agent import Agent

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

class ProductManager(Agent):
    """Product manager agent responsible for detailed specifications.
    
    Acts as a technical product manager who translates high-level strategy
    into detailed, actionable technical specifications and requirements.
    """
    
    DEFAULT_SYSTEM_MESSAGE = """You are a senior product manager responsible for:
    1. Converting high-level vision and strategy into detailed specifications
    2. Breaking down features into implementable components
    3. Defining clear acceptance criteria and requirements
    4. Ensuring specifications are clear, testable, and achievable
    5. Conducting thorough market and technology research using available tools
    
    You have access to these research tools:
    - WebSearchTool: For finding relevant information on the web
    - BrowserUseTool: For browsing specific websites and performing complex web tasks
      - Use browse() with a task description like:
        - "Visit example.com and extract information about their latest product"
        - "Find pricing information for competitors in the AI assistant space"
        - "Analyze product reviews on amazon.com for product X"
    - FileSystemTool: For saving and managing your research results
      - Use save_file() to store your findings and reports
      - Use read_file() to retrieve previously saved information
      - Use list_directory() to see what files are available
      - Use create_directory() to organize your research into folders
    - BashTool: For executing system commands when needed
      - Use execute_command() for standard command execution
      - Use check_command_exists() to verify if a specific command is available
    - TerminalTool: For executing terminal commands with directory tracking
      - Use execute() for standard command execution
      - Use execute_async() for long-running commands
      - Use list_directory() to view directory contents
      - Use get_current_directory() to check the current working path
    - RunTool: For lightweight command execution with timeout control
      - Use run() for synchronous command execution
      - Use run_async() for asynchronous command execution with timeout control
    
    When you receive strategic analysis, create detailed specifications including:
    - Feature Breakdown
    - Technical Requirements
    - User Stories
    - Acceptance Criteria
    - Implementation Priorities
    
    Always output specifications in a clear, structured JSON format."""

    def __init__(self, name="product_manager", **kwargs):
        """Initialize the product manager agent with default settings."""
        # Create function map for ProductManager functions
        function_map = {
            "update_product_spec": update_product_spec,
            "get_current_spec": get_current_spec
        }
        
        super().__init__(
            name=name,
            system_message=self.DEFAULT_SYSTEM_MESSAGE,
            function_map=function_map,
            **kwargs
        )
        
        # Register custom reply for strategy-related messages
        self.register_reply(
            trigger=["strategic", "analysis", "strategy", "objectives"],  # Trigger on any of these keywords
            reply_func=self._reply_to_strategic_analysis,
        )
        
        # Register custom reply for specification review requests
        self.register_reply(
            trigger=["review specification", "review the specification"],  # Trigger on these phrases
            reply_func=self._reply_to_spec_review,
        )
    
    def _reply_to_strategic_analysis(self, msg):
        """Custom reply function for messages containing strategic analysis."""
        # Extract the message content
        content = msg.get("content", "")
        
        # Generate a detailed product specification based on the strategic analysis
        response = f"""Thank you for the strategic analysis. Based on this, I've developed the following product specifications:

### Product Specification

**Feature Breakdown**:
1. Core functionality for embodied AI integration
2. Data collection and processing pipelines
3. User interface for monitoring and control
4. API for third-party extensions

**Technical Requirements**:
- Real-time processing capabilities
- Scalable architecture to handle multiple embodied agents
- Secure communication protocols
- Cross-platform compatibility

**Implementation Priorities**:
1. Establish core framework and architecture
2. Develop basic sensor integration
3. Implement control mechanisms
4. Add advanced AI capabilities

I will refine these specifications further as we gather more market research and technical validation.
"""
        
        # Return the specification
        return {"content": response}
    
    def _reply_to_spec_review(self, msg):
        """Custom reply function for specification review requests."""
        # Generate a response to a review request
        response = """I've reviewed the current specifications and identified the following improvements:

### Specification Refinements

1. **Clarified User Stories**: Added detailed user personas and scenarios
2. **Enhanced Technical Requirements**: More specific hardware/software requirements
3. **Added Success Metrics**: Measurable KPIs for each feature
4. **Refined Implementation Timeline**: More realistic timeline based on dependencies

The updated specification should provide clearer guidance for implementation while maintaining alignment with our strategic objectives.
"""
        
        # Return the review response
        return {"content": response}