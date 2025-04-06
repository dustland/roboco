<img src="./assets/logo.png" alt="logo" width="80px" height="80px">

# RoboCo

A **Robo**t-driven **Co**mpany built with Multi-Agent Platform.

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0+-00a393?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Built on AG2](https://img.shields.io/badge/Built%20on-AG2-orange)](https://github.com/ag2ai/ag2)

## Overview

RoboCo is a powerful platform that combines Domain-Driven Design with Multi-Agent Systems to create intelligent, collaborative AI teams. Built with a clean architecture that separates concerns into domain, application, infrastructure, and interface layers, RoboCo enables you to build sophisticated AI applications with minimal boilerplate.

## Key Features

- **Configuration-Based Multi-Agent Teams**: Specialized agents that collaborate to solve complex problems including Lead, Researcher, Developer, Evaluator etc, and also with prompts configurable
- **Project Management**: Built-in project and task tracking with markdown integration
- **MCP Integration**: Model Context Protocol for enhanced agent communication and reasoning
- **Extensible Tools**: Plug-and-play tools for research, analysis, and code generation
- **Multi-Language Support**: Code generation and execution in multiple programming languages
- **REST API**: Comprehensive API with FastAPI for seamless integration, easier for visualization of the execution

## Quick Start

```bash
# Clone repository
git clone https://github.com/dustland/roboco.git
cd roboco

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Unix/macOS
# OR
# venv\Scripts\activate  # On Windows

# Install dependencies with uv (faster, modern approach)
pip install uv
uv pip install -e .

# Install UI dependencies (optional)
uv pip install ".[ui]"

# OR install with standard pip
# pip install -e .
# pip install -e ".[ui]"  # With UI dependencies

# Configure API keys
cp .env.example .env
# Edit .env with your API keys

# Run the simple chat example (simplest way to get started)
python examples/services/chat_example.py

# Or use the integrated UI (recommended)
# First, start the API server in one terminal:
roboco-api-dev
# Then, in another terminal, start the UI:
roboco-ui

# Additional commands available after installation
roboco-api  # Starts the API server using installed package
roboco-api-dev  # Starts the API server in development mode with auto-reload
roboco-db-api  # Starts a minimal database API server
roboco-ui  # Starts the web UI (requires the API server to be running)
```

## Documentation

- [Config-Based Design](docs/config_based_design.md) - Team configuration
- [Object Model](docs/object_model.md) - Core domain models
- [Tool System](docs/tool.md) - Tool system
- [MCP](docs/mcp.md) - Model-Context-Protocol support

## Web Interface

RoboCo includes a built-in web interface for interacting with the system and monitoring project execution:

<img src="./assets/ui-screenshot.png" alt="RoboCo UI" width="700px">

### Features

- **Chat Interface**: Communicate with RoboCo agents through a familiar chat UI
- **Execution Monitoring**: Track project progress and task completion in real-time
- **File Explorer**: Browse and view files generated during project execution
- **Execution Control**: Stop running processes when needed
- **Project Management**: Load existing conversations and manage projects

### Running the UI

The UI requires the API server to be running. Launch them in separate terminals:

```bash
# Terminal 1: Start the API server
roboco-api-dev

# Terminal 2: Start the UI
roboco-ui
```

Then open your browser to http://localhost:8501 to access the interface.

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details and our [Code of Conduct](CODE_OF_CONDUCT.md).

## Acknowledgments

- Built on top of [AG2](https://github.com/ag2ai/ag2)
- Inspired by [Manus](https://manus.im/) and [OpenManus](https://github.com/mannaandpoem/OpenManus/)
- Thanks to Anthropic for MCP(Model Context Protocol) design
- Logo generated with [GPT-4o](https://chatgpt.com)

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
