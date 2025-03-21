# Roboco Agents

This directory is for creating custom Agent implementations with specialized behavior that goes beyond what can be expressed through configuration alone.

## Configuration-Based Approach

Most standard agents have been moved to a configuration-based system, where agent behavior is defined in markdown files located in `config/roles/`. This approach offers several advantages:

- **Simplicity**: Define agents through plain text files without coding
- **Maintainability**: Separate agent behavior (prompts) from code
- **Flexibility**: Easily modify agent behavior without changing code

For standard agents, we recommend using the configuration-based approach rather than creating custom agent classes.

## When to Use Custom Agents

Consider creating custom Agent subclasses when:

1. You need specialized processing logic that goes beyond what prompts can express
2. You want to integrate with external systems or APIs in a way specific to an agent role
3. You need to implement complex state management within an agent
4. You're extending the Agent functionality with new capabilities

## Creating Custom Agents

To create a custom agent, create a new class that inherits from the base `Agent` class:

```python
from roboco.core.agent import Agent
from typing import List, Dict, Any
import some_external_library

class CustomAnalyticsAgent(Agent):
    """Custom agent that integrates with analytics tools."""

    def __init__(self, name: str, api_key: str = None, **kwargs):
        self.api_key = api_key
        self.analytics_client = None
        super().__init__(name, **kwargs)

    def _setup_analytics(self):
        """Initialize the analytics client."""
        if self.api_key:
            self.analytics_client = some_external_library.Client(self.api_key)

    async def generate_response(self, messages: List[Dict[str, Any]]) -> str:
        """Enhance response with analytics data."""
        # Ensure client is set up
        if not self.analytics_client:
            self._setup_analytics()

        # Get analytics data for context
        analytics_data = self.analytics_client.get_data()

        # Add context to the message
        context_message = {
            "role": "system",
            "content": f"Current analytics data: {analytics_data}"
        }
        enhanced_messages = messages + [context_message]

        # Get response using the enhanced context
        return await super().generate_response(enhanced_messages)
```

## Registering Custom Agents

To use your custom agent in the configuration-based system, register it with the `AgentFactory`:

```python
from roboco.core.agent_factory import AgentFactory
from my_custom_agents import CustomAnalyticsAgent

# Register your custom agent class
factory = AgentFactory()
factory.register_agent_class("analytics_agent", CustomAnalyticsAgent)

# Now you can use "analytics_agent" as a role in your team configurations
```

## Remaining Specialized Agents

The following specialized agent remains in this directory:

### RoboticsScientist

The RoboticsScientist agent specializes in designing and implementing robotic systems. It has expertise in robot design, kinematics, dynamics, and control systems.

## Agent Collaboration

Agents are designed to work together in teams defined by YAML configurations.

## Termination Messages

All Roboco agents support termination messages, following AG2's conversation termination pattern. A termination message is a specific string that an agent includes at the end of its response to signal that it has completed its task.

## Tools and Capabilities

Tools are provided separately and can be attached to any agent in a team configuration:

```yaml
# config/teams.yaml
teams:
  research_team:
    name: "ResearchTeam"
    roles:
      - product_manager
      - researcher
      - analytics_agent # Our custom agent
    tools:
      - browser_use
      - filesystem
    tool_executor: human_proxy
```

This allows for flexible tool assignment based on team needs.
