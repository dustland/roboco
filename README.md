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

### Backend (roboco)

The core multi-agent system that powers robot adaptation:

- 🤖 Multi-agent architecture for robot development
- 🧠 Intelligent task delegation and coordination
- 📊 Built-in monitoring and logging
- 🔄 Asynchronous communication between agents
- ⚙️ Flexible configuration system

### Frontend (Studio)

A modern web interface for robot development and monitoring:

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

1. Set up the backend:

```bash
cd roboco
poetry install
uvicorn roboco.service:app --reload
```

2. Set up the frontend:

```bash
cd ../studio
pnpm install
pnpm dev
```

3. Run a simple example:

```python
from roboco.examples.market_research import ResearchTeam

# Create a research team
team = ResearchTeam()

# Run market research with physical interaction capabilities
result = team.run_research("What are the latest trends in humanoid robotics?")
```

## Project Structure

```
roboco/
├── src/
│   └── roboco/
│       ├── agents/         # Agent implementations for embodied AI
│       ├── core/           # Core functionality for physical interaction
│       ├── tools/          # Tool implementations for robot control
│       └── api/            # API endpoints for robot interfaces
├── examples/              # All example code MUST be placed here, not in src/roboco/examples
│   └── market_research/   # Market research example with physical interaction
├── tests/                # Test suite
└── docs/                 # Documentation
```

**Note**: All example code must be placed in the root `examples/` directory, not in `src/roboco/examples/`. This ensures consistency and makes examples easily discoverable.

## Available Agents

- **ProductManager**: Defines research scope and delegates tasks for physical interaction
- **Researcher**: Analyzes data and extracts insights from physical interactions
- **ReportWriter**: Compiles findings into comprehensive reports
- **ToolUser**: Executes tools and functions for robot control
- **Executive**: Provides high-level vision and strategy for embodied tasks
- **PhysicalInteractionAgent**: Specialized agent for handling physical interactions
- **SensorProcessingAgent**: Processes and interprets sensor data
- **RobotController**: Manages robot movements and actions

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

- Python >= 3.10, < 3.13
- Poetry for dependency management
- Node.js >= 18
- PNPM package manager
- CUDA-enabled GPU (recommended)
- Ubuntu 24.04 LTS (recommended)

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
3. Implement required methods and customize behavior for embodied AI tasks
4. Add the agent to `src/roboco/agents/__init__.py`

### Adding New Tools

1. Create a new tool class in `src/roboco/tools/`
2. Inherit from the base `Tool` class
3. Implement required methods and customize behavior for physical interaction
4. Add the tool to `src/roboco/tools/__init__.py`

## Documentation

Documentation is currently under development. Please refer to the following resources:

- [AG2 Documentation](https://docs.ag2.ai) - The underlying framework documentation
- [Examples](examples/) - Code examples and usage patterns
- [API Reference](src/roboco/api/) - Core API documentation

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
