# RoboCo: A Robot-driven Company

> [!Warning]
> This project is currently open source, but may transition to a closed source license in the future for production use.

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>
  <a href="https://x.com/dustland_ai"><img src="https://img.shields.io/badge/Twitter-@dustland__ai-blue?logo=twitter" alt="Twitter"></a>
</p>

A comprehensive platform for developing and adapting humanoid robots for specific occupations, combining AI, robotics, and human behavior analysis to create effective robot workers that integrate naturally into human workplaces.

## Key Features

- 🤖 **Multi-Agent Teams** - Specialized agents for robotics, planning, and interaction
- 🔧 **Configuration-Based System** - Define teams and agents using YAML configs
- 📋 **Project Management** - Track goals, sprints, and todos across teams
- 🛠️ **Extensible Tools** - Web research, physics simulation, and robot control
- 🔌 **Model Context Protocol** - Support for MCP server integration
- 🔄 **Physical Interaction** - Real-world interaction capabilities
- 📊 **Built-in Monitoring** - Comprehensive logging and monitoring
- 🌐 **REST API** - Control and monitor via HTTP API endpoints

## Quick Start

```bash
# Clone repository
git clone https://github.com/dustland/roboco.git
cd roboco

# Setup environment (uses uv package manager)
./setup.sh  # On Unix/macOS
# or
setup.bat   # On Windows

# Add your API keys to .env
cp .env.example .env
# Edit .env with your API keys

# Start the API server
./start.sh  # On Unix/macOS
# or
python -m roboco server  # Start directly with CLI

# Run an example
python examples/test_config.py

# Try the project management API
python examples/api/project_example.py
```

## Documentation

- [Configuration Based Design](docs/config_based_design.md) - Working with agent teams
- [Agent System](docs/agent.md) - Creating and configuring agents
- [Tools](docs/tools.md) - Built-in tools documentation
- [MCP Integration](docs/mcp.md) - Model Context Protocol details
- [API Server](docs/api.md) - REST API documentation
- [Project Management](docs/projects.md) - Managing projects, sprints, and todos

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

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md).

## Contact

- 📧 Email: hi@dustland.ai
- 🌐 Website: [dustland.ai](https://dustland.ai)
- 🐦 Twitter: [@dustland_ai](https://twitter.com/dustland_ai)

## Acknowledgments

- Built on top of [AG2](https://github.com/ag2ai/ag2)
- Inspired by [Manus](https://manus.im/) and [OpenManus](https://github.com/mannaandpoem/OpenManus/)
- Thanks to Anthropic for MCP(Model Context Protocol) design
- Special thanks to the robotics and AI research communities

## Citation

```bibtex
@misc{roboco2025,
  author = {Dustland Team},
  title = {RoboCo: A Robot-driven Company powered by Multi-agent System},
  year = {2025},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/dustland/roboco}},
}
```
