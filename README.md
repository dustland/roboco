# RoboCo

> [!Warning]
> This project is currently open source, but may transition to a closed source license in the future for production use.

RoboCo (Robot Company) is a comprehensive platform designed to develop and adapt humanoid robots for specific occupations. It combines expertise in robotics, human behavior analysis, and occupation-specific knowledge to create effective robot workers that can naturally integrate into human workplaces.

## Features

- **Humanoid Robot Development**: Create and adapt robots for specific occupations
- **Multi-Agent Teams**: Specialized agents for robotics and physical interaction
- **Configuration-Based System**: Define teams and agents using YAML configs and markdown prompts
- **Extensible Tools**: Web research, physics simulation, and robot control capabilities
- **Physical Interaction**: Real-world interaction and robot control
- **Built-in Monitoring**: Comprehensive logging and monitoring system
- **MCP Servers**: Support MCP (Model Context Protocols) Servers

## Installation

Ensure you have Python 3.10+ installed.

```bash
# Clone the repository
git clone https://github.com/dustland/roboco.git
cd roboco

# Setup using shell script
./setup_workspace.sh  # On Unix/macOS
# or
setup_workspace.bat  # On Windows

# Add your API keys to .env
# Activate virtual environment
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows

# Run an example
python examples/test_config.py
```

## Project Structure

```
roboco/
├── src/
│   └── roboco/
│       ├── agents/       # Custom agent implementations
│       ├── teams/        # Team implementations
│       ├── core/         # Core functionality
│       ├── tools/        # Tool implementations
│       └── models/       # Data models and schemas
├── config/
│   ├── roles/            # Agent role definitions in markdown
│   ├── teams/            # Team-specific configurations
│   └── teams.yaml        # Global team definitions
├── examples/             # Example scripts
├── tests/                # Test suite
└── docs/                 # Documentation
```

## Agent System

RoboCo now uses a configuration-based approach for defining agents:

### Role Definitions

Agents are defined using markdown files in `config/roles/` directory:

```markdown
# Software Engineer

You are the Software Engineer agent, responsible for implementing technical solutions...

## Responsibilities

- Develop software components
- Review code for quality and security
- ...
```

### Custom Agents

For specialized needs, you can create custom Agent subclasses:

```python
from roboco.core.agent import Agent

class DataAnalystAgent(Agent):
    """Custom agent with specialized data analysis capabilities"""

    def __init__(self, name, **kwargs):
        self.data_sources = kwargs.pop("data_sources", [])
        super().__init__(name, **kwargs)

    async def generate_response(self, messages):
        # Custom response generation logic
        return await super().generate_response(messages)
```

## Team System

Teams are defined in YAML configuration files:

### Global Team Configuration

```yaml
# config/teams.yaml
teams:
  planning:
    name: "PlanningTeam"
    description: "Team for project planning"
    roles:
      - executive
      - product_manager
      - software_engineer
    workflow:
      - from: product_manager
        to: software_engineer
      # More workflow steps...
    tools:
      - filesystem
```

### Creating Teams

Teams can be created from configuration:

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

## Available Roles

- **Executive**: Provides strategic direction and final approval
- **ProductManager**: Defines scope and delegates tasks
- **SoftwareEngineer**: Implements technical solutions
- **ReportWriter**: Creates and formats documentation
- **RoboticsScientist**: Designs robotics systems and algorithms
- **HumanProxy**: Executes tools and real-world interactions

## Available Tools

- **FileSystemTool**: Read and write files and directories
- **BrowserUseTool**: Web browsing with fallback mechanism
  - Supports custom output directories: `BrowserUseTool(output_dir="./browser_output")`
- **WebSearchTool**: Search engine integration
- **ArxivTool**: Scientific paper research
- **GitHubTool**: Code repository integration
- **GenesisTool**: Physics engine integration
  - Uses shell commands: `GenesisTool(genesis_executable="/path/to/genesis")`
- **TerminalTool**: Command execution
- **RunTool**: Code execution

## Configuration

Core configuration uses YAML format in `config/config.yaml`:

```yaml
# Core Settings
core:
  workspace_base: "./workspace"
  workspace_root: "workspace"

# LLM Settings
llm:
  model: "gpt-4o"
  api_key: "${OPENAI_API_KEY}"
  max_tokens: 8000
  temperature: 0.7
  base_url: "https://api.openai.com/v1"

  # Model-specific configurations also available
  openai:
    model: "gpt-4o"
    # Additional settings

  deepseek:
    model: "deepseek-coder"
    # Additional settings
```

## Development

Create new role definitions by adding markdown files to `config/roles/`.

Create team configurations by adding entries to `config/teams.yaml` or team-specific files in `config/teams/`.

For specialized behavior, add custom agents by creating classes in `src/roboco/agents/` that inherit from the base `Agent` class.

Add new tools by creating classes in `src/roboco/tools/` that inherit from the base `Tool` class.

## Contact

- Email: hi@dustland.ai

## Acknowledgments

- Built on top of [AG2](https://github.com/ag2ai/ag2)
- Inspired by the concepts of [Manus](https://manus.im/) and [OpenManus](https://github.com/mannaandpoem/OpenManus/)
- Inspired by the need for better embodied AI and humanoid robotics development
- Special thanks to the robotics and AI communities for their contributions to the field

## Tool Registration with Executor Agents

The Genesis agent can now be initialized with an `executor_agent` parameter, which simplifies tool registration. This allows tools to be automatically registered with a specified executor agent during initialization, eliminating the need for explicit calls to `register_tools_with_executor`.

### Example Usage

```python
# Create a human proxy agent
human_proxy = HumanProxy(
    name="User",
    system_message="You are a user who tests physics simulations.",
    terminate_msg="=== End of conversation ===",
    human_input_mode="NEVER"
)

# Method 1: Create an agent with executor_agent in constructor
genesis_agent = GenesisAgent(
    name="PhysicsAssistant",
    system_message="You are a physics simulation expert that helps users test simulations.",
    terminate_msg="=== End of conversation ===",
    mcp_server_command="genesis-mcp",
    executor_agent=human_proxy  # Set the human_proxy as the executor for tools
)

# Method 2: Create an agent and set executor later
genesis_agent = GenesisAgent(
    name="PhysicsAssistant",
    system_message="You are a physics simulation expert."
)
# Later register tools with an executor
genesis_agent.register_tools_with_executor(human_proxy)
```

This improvement streamlines the process of setting up tool execution between different agents, making it easier to build complex multi-agent systems with separate tool definition and execution responsibilities.

### Initiating Conversations with Tool Executors

When using agents with tool execution, it's recommended to have the executor agent initiate the conversation. This pattern works especially well with the `HumanProxy` as executor:

```python
# Create a human proxy agent
human_proxy = HumanProxy(
    name="User",
    system_message="You are a user interested in physics simulations.",
    human_input_mode="ALWAYS"
)

# Create the Genesis agent with the human proxy as the executor
genesis_agent = GenesisAgent(
    name="GenesisAssistant",
    system_message="You are a physics simulation expert that helps users create and run simulations.",
    mcp_server_command="genesis-mcp",
    executor_agent=human_proxy
)

# Let the human proxy initiate the chat with the Genesis agent
await human_proxy.initiate_chat(
    recipient=genesis_agent,
    message="Hello, I'd like to learn about physics simulations.",
    max_turns=10
)
```

This approach ensures proper handling of tool execution and conversation flow, with the human proxy managing both the conversation and the execution of tools.
