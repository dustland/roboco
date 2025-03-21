# RoboCo

> An advanced multi-agent system for humanoid robot development

RoboCo (Robot Company) is a comprehensive platform designed to develop and adapt humanoid robots for specific occupations. It combines expertise in robotics, human behavior analysis, and occupation-specific knowledge to create effective robot workers that can naturally integrate into human workplaces.

## Features

- **Humanoid Robot Development**: Create and adapt robots for specific occupations
- **Multi-Agent Teams**: Specialized agents for robotics and physical interaction
- **Extensible Tools**: Web research, physics simulation, and robot control capabilities
- **Physical Interaction**: Real-world interaction and robot control
- **Built-in Monitoring**: Comprehensive logging and monitoring system

## Installation

Ensure you have Python 3.10+ installed.

```bash
# Clone the repository
git clone https://github.com/roboco-ai/roboco.git
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
│       ├── agents/       # Agent implementations
│       ├── core/         # Core functionality
│       ├── tools/        # Tool implementations
│       └── models/       # Data models and schemas
├── examples/             # Example scripts
├── config/               # Configuration files
├── tests/                # Test suite
└── docs/                 # Documentation
```

## Available Agents

- **ProductManager**: Defines scope and delegates tasks
- **Researcher**: Analyzes data from various sources
- **ReportWriter**: Compiles findings into reports
- **PhysicalInteractionAgent**: Handles physical interactions
- **SensorProcessingAgent**: Processes sensor data

## Available Tools

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

Configuration uses YAML format in `config/config.yaml`:

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

Add new agents by creating classes in `src/roboco/agents/` that inherit from the base `Agent` class.

Add new tools by creating classes in `src/roboco/tools/` that inherit from the base `Tool` class.

## Contact

- Email: hi@dustland.ai

## Acknowledgments

- Built on top of [AG2](https://github.com/ag2ai/ag2)
- Inspired by the need for better embodied AI and humanoid robotics development
- Special thanks to the robotics and AI communities for their contributions to the field
