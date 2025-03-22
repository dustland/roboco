# RoboCo

A Domain-Driven Multi-Agent Platform for Robot-Human Collaboration

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0+-00a393?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Built on AG2](https://img.shields.io/badge/Built%20on-AG2-orange)](https://github.com/ag2ai/ag2)

## Overview

RoboCo is a powerful platform that combines Domain-Driven Design with Multi-Agent Systems to create intelligent, collaborative AI teams. Built with a clean architecture that separates concerns into domain, application, infrastructure, and interface layers, RoboCo enables you to build sophisticated AI applications with minimal boilerplate.

## Key Features

- **Domain-Driven Design**: Clean architecture with proper separation of concerns and dependency injection
- **Multi-Agent Teams**: Specialized agents that collaborate to solve complex problems
- **Sprint Management**: Built-in project and sprint management for agile development
- **MCP Integration**: Model Context Protocol for enhanced agent communication and reasoning
- **Extensible Tools**: Plug-and-play tools for research, analysis, and interaction
- **REST API**: Comprehensive API with FastAPI for seamless integration
- **Workspace Management**: Organized workspaces for artifacts and project resources

## Quick Start

```bash
# Clone repository
git clone https://github.com/dustland/roboco.git
cd roboco

# Setup environment
./setup.sh  # On Unix/macOS
# or
setup.bat   # On Windows

# Configure API keys
cp .env.example .env
# Edit .env with your API keys

# Start the API server
./start.sh  # Uses default host (127.0.0.1) and port (8000)
# Or with custom options
./start.sh --host=0.0.0.0 --port=8080 --reload
```

## Architecture

RoboCo follows a clean, domain-driven architecture:

```
src/roboco/
├── api/                # REST API with FastAPI
│   ├── routers/        # API route handlers
│   ├── schemas/        # API data validation schemas
│   └── server.py       # FastAPI application
├── domain/             # Domain models and business logic
│   ├── models/         # Core domain entities
│   └── repositories/   # Repository interfaces
├── infrastructure/     # External systems and implementations
│   ├── repositories/   # Repository implementations
│   └── adapters/       # External service adapters
└── services/           # Application services
    ├── agent_service.py    # Agent management
    ├── api_service.py      # API facade
    ├── project_service.py  # Project management
    ├── sprint_service.py   # Sprint management
    ├── team_service.py     # Team management
    └── workspace_service.py # Workspace management
```

## Documentation

- [Domain-Driven Design](docs/domain_driven_design.md) - Architecture overview
- [Config-Based Design](docs/config_based_design.md) - Team configuration
- [Object Model](docs/object_model.md) - Core domain models
- [MCP](docs/mcp.md) - Multi-agent collaboration protocol

## Configuration

RoboCo uses environment variables for configuration with sensible defaults:

```
# .env
OPENAI_API_KEY=your_api_key_here
WORKSPACE_DIR=~/roboco_workspace
LOG_LEVEL=INFO
```

The `start.sh` script provides a convenient way to launch the API server with various configuration options:

```bash
# Basic usage
./start.sh

# Available options
./start.sh --host=0.0.0.0     # Bind to all interfaces
./start.sh --port=8080        # Use custom port
./start.sh --reload           # Enable auto-reload for development
./start.sh --workers=4        # Use multiple worker processes
./start.sh --help             # Show all available options
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details and our [Code of Conduct](CODE_OF_CONDUCT.md).

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
