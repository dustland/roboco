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
- **Fallback Mechanisms**: Graceful degradation for browser tools when dependencies are unavailable

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

Ensure you have Python 3.10 or later and [Node.js](https://nodejs.org/) v20.x installed.

```bash
# Install dependencies using uv (recommended)
pip install uv
uv venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
uv pip install -e .
```

## Quick Start

```bash
# Clone the repository
git clone https://github.com/roboco-ai/roboco.git
cd roboco

# Install dependencies using uv
pip install uv
uv venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
uv pip install -e .

# Set up OpenAI API keys (or other providers)
cp config/config.example.toml config/config.toml
# Edit config/config.toml with your API keys

# Run an example
python examples/web_surf.py
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

- **BrowserTool**: Web browsing and interaction capabilities with fallback mechanism
- **BrowserUseTool**: High-level browser automation with fallback to requests/BeautifulSoup
- **FileSystemTool**: File system operations
- **BashTool**: Bash command execution
- **TerminalTool**: Terminal command execution
- **RunTool**: Code execution

### Browser Tools Fallback Mechanism

The browser tools (`BrowserTool` and `BrowserUseTool`) include a fallback mechanism that allows them to function even when the required dependencies (`browser-use` and `playwright`) are unavailable or incompatible with the current Python version. This ensures your applications can continue to operate in various environments.

The fallback implementation:

- Uses `requests` and `BeautifulSoup` for basic web browsing
- Automatically activates when browser automation fails
- Provides seamless degradation of functionality
- Works with Python 3.13+ where `playwright` may have compatibility issues

See the [web_surf examples](examples/web_surf/) for demonstrations of both standard and fallback usage.

## Requirements

- Python >= 3.10
- uv for dependency management
- OpenAI API key or other LLM provider API key
- Internet connection for web research capabilities
- For browser tools: `requests` and `beautifulsoup4` (fallback mode) or `browser-use` and `playwright` (full mode)

## Development

```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run linting
flake8
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

## Configuration

Roboco can be configured using a TOML configuration file. The default location for the configuration file is `config/config.toml`.

### Configuration Options

#### Workspace Configuration

The workspace is where Roboco stores all work artifacts, including research reports, code, and documentation.

```toml
# In config.toml
workspace_root = "workspace"  # Relative to project root
# OR
workspace_root = "/absolute/path/to/workspace"  # Absolute path
# OR
workspace_root = "~/roboco_workspace"  # Home directory
```

By default, Roboco uses the `workspace` directory in the project root. The workspace is organized into the following subdirectories:

- `research`: Contains research reports and materials
- `code`: Contains source code for projects
- `docs`: Contains documentation
- `data`: Contains data files

#### LLM Configuration
