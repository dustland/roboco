# RoboCo

> An advanced multi-agent system for humanoid robot development

RoboCo (Robot Company) is a comprehensive platform designed to develop and adapt humanoid robots for specific occupations. Built on top of AG2 (AutoGen 2.0), it combines expertise in robotics, human behavior analysis, and occupation-specific knowledge to create effective robot workers that can naturally integrate into human workplaces.

## Features

- **Humanoid Robot Development**: Create and adapt humanoid robots for specific occupations
- **Multi-Agent Teams**: Specialized agents for humanoid robotics and physical interaction
- **Swarm Orchestration**: Dynamic agent collaboration in physical environments
- **Extensible Tools**: Tools for physical interaction, sensor processing, and robot control
- **Physical Interaction**: Real-world interaction and robot control capabilities
- **Sensor Integration**: Support for processing various sensor inputs (vision, audio, tactile)
- **Built-in Monitoring**: Comprehensive logging and monitoring system
- **Asynchronous Communication**: Efficient agent interaction patterns

## System Components

### Core Framework

The core multi-agent system that powers robot adaptation:

- 🤖 Multi-agent architecture for robot development
- 🧠 Intelligent task delegation and coordination
- 📊 Built-in monitoring and logging
- 🔄 Asynchronous communication between agents
- ⚙️ Flexible configuration system

### Future UI Plans

A Streamlit-based user interface is planned for future development:

- 🎯 Intuitive robot task configuration
- 📈 Real-time monitoring and analytics
- 🔍 Detailed agent interaction visualization
- 🛠️ Development tools and debugging interfaces

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/roboco.git
cd roboco

# Install dependencies using Poetry (recommended)
poetry install

# Or install using pip
pip install -e .
```

## Quick Start

1. Set up the environment:

```bash
# Clone the repository
git clone https://github.com/yourusername/roboco.git
cd roboco

# Install dependencies using Poetry
poetry install
```

2. Configure your API keys:

```bash
# Copy the example .env file
cp .env.example .env

# Edit the .env file with your API keys
nano .env
```

3. Run a simple example:

```python
# Run the web research example
poetry run python examples/web_surf.py

# Or import and use in your own script
from roboco.agents import ProductManager, HumanProxy

# Create a research team
researcher = ProductManager()
user = HumanProxy()

# Run market research
user.initiate_chat(
    researcher,
    message="What are the latest trends in humanoid robotics?"
)
```

## Project Structure

```
roboco/
├── src/
│   └── roboco/
│       ├── agents/         # Agent implementations
│       ├── core/           # Core functionality and base classes
│       ├── tools/          # Tool implementations
│       └── models/         # Data models and schemas
├── examples/               # Example scripts and use cases
├── config/                 # Configuration files
├── tests/                  # Test suite
└── docs/                   # Documentation
```

**Note**: All example code should be placed in the root `examples/` directory to ensure consistency and make examples easily discoverable.

## Available Agents

RoboCo provides several specialized agents for different aspects of robot development:

- **ProductManager**: Defines research scope and delegates tasks to other agents
- **Researcher**: Analyzes data and extracts insights from various sources
- **ReportWriter**: Compiles findings into comprehensive reports
- **HumanProxy**: Acts as a proxy for human users, enabling natural interaction
- **PhysicalInteractionAgent**: Specialized agent for handling physical interactions
- **SensorProcessingAgent**: Processes and interprets sensor data

All agents support termination messages, following AG2's conversation termination pattern. This allows agents to signal when they have completed their task, enabling more efficient conversations. The termination message is configurable through the `config.toml` file.

## Agent Communication

RoboCo extends AG2's agent communication patterns with additional features:

1. **Termination Messages**: Agents can signal completion of tasks with configurable termination messages
2. **Automatic Propagation**: Termination messages are automatically propagated between agents
3. **Configuration-Driven**: Communication patterns can be configured through the config file

## Available Tools

- **BrowserTool**: Web browsing and interaction capabilities
- **FileSystemTool**: File system operations
- **BashTool**: Bash command execution
- **TerminalTool**: Terminal command execution
- **RunTool**: Code execution
- **SimulationTool**: Simulation capabilities for embodied AI
- **RobotControlTool**: Interface for controlling robot movements
- **SensorTool**: Processing and interpreting sensor data
- **VisionTool**: Computer vision and image processing
- **AudioTool**: Audio processing and speech recognition
- **TactileTool**: Processing tactile sensor data

## Requirements

- Python >= 3.10
- Poetry for dependency management
- OpenAI API key or other LLM provider API key
- Internet connection for web research capabilities

## Development

### Setting Up Development Environment

```bash
# Install development dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Run linting
poetry run flake8
```

### Adding New Agents

1. Create a new agent class in `src/roboco/agents/`
2. Inherit from the base `Agent` class
3. Implement required methods and customize behavior
4. Add the agent to `src/roboco/agents/__init__.py`

### Adding New Tools

1. Create a new tool class in `src/roboco/tools/`
2. Inherit from the base `Tool` class
3. Implement required methods and customize behavior
4. Add the tool to `src/roboco/tools/__init__.py`

## Documentation

Documentation is available in the `docs/` directory:

- [Agent Communication Patterns](docs/agents/communication.md) - How agents communicate, including termination messages
- [Tool Design](docs/tool_design.md) - How tools are designed and used in the system

For additional resources, please refer to:

- [AG2 Documentation](https://docs.ag2.ai) - The underlying framework documentation
- [Examples](examples/) - Code examples and usage patterns

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

Apache 2.0

## Contact

- Email: hi@dustland.ai

## Acknowledgments

- Built on top of [AG2](https://github.com/microsoft/autogen) (AutoGen 2.0)
- Inspired by the need for better embodied AI and humanoid robotics development
- Special thanks to the robotics and AI communities for their contributions to the field
