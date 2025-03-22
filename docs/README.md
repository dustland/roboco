# RoboCo Documentation

Welcome to the RoboCo documentation! This guide will help you get started with RoboCo, a platform for developing and adapting humanoid robots for specific occupations.

## Getting Started

### Prerequisites

Before installing RoboCo, ensure you have:

- Python 3.10 or newer
- Git
- A terminal or command prompt

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/dustland/roboco.git
   cd roboco
   ```

2. Run the setup script:

   ```bash
   # On Unix/macOS
   ./setup.sh

   # On Windows
   setup.bat
   ```

3. Configure your API keys:

   - Copy `.env.example` to `.env`
   - Edit `.env` to add your API keys (OpenAI, etc.)

4. Activate the virtual environment:

   ```bash
   # On Unix/macOS
   source .venv/bin/activate

   # On Windows
   .venv\Scripts\activate
   ```

5. Run an example to verify the installation:
   ```bash
   python examples/test_config.py
   ```

## Documentation Structure

- [Agent System](agent.md): Overview of the agent architecture
- [Team System](config_based_design.md): How to work with agent teams
- [Tools](tools.md): Available tools and their usage
- [MCP Integration](mcp.md): Using the Model Context Protocol
- [API Reference](api/README.md): Detailed API documentation

## Quickstart Examples

### Creating a Simple Agent

```python
from roboco.core import Agent

# Create a basic agent
agent = Agent(
    name="Assistant",
    system_message="You are a helpful assistant.",
)

# Generate a response
response = await agent.generate_response("Hello, can you help me?")
print(response)
```

### Setting Up a Team

```python
from roboco.core import TeamBuilder

# Create team from configuration
team = TeamBuilder.create_team("planning")

# Run the team
result = await team.run_swarm(
    initial_agent_name="ProductManager",
    query="Create a project plan"
)
```

## Configuration

RoboCo uses YAML for configuration. The main configuration files are:

- `config/config.yaml`: Global settings
- `config/teams.yaml`: Team definitions
- `config/roles/*.md`: Agent role definitions

## Next Steps

- Explore the [examples](../examples/) directory for more usage patterns
- Read about the [agent system](agent.md) to understand how agents work
- Learn how to create [teams](config_based_design.md) of specialized agents
- Check out the available [tools](tools.md) for agent capabilities

## Getting Help

If you encounter issues or have questions:

- Check the [FAQ](faq.md) for common questions
- Open an issue on GitHub
- Contact us at hi@dustland.ai
