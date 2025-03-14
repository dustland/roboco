# RoboCo Service

> Backend service for the RoboCo multi-agent system for humanoid robot development

## Overview

RoboCo service is the core backend component that powers the RoboCo platform. It provides a robust API for robot development, task management, and multi-agent coordination.

## Features

- 🤖 Multi-agent system architecture
- 🔄 Real-time robot task coordination
- 📊 Built-in monitoring and logging
- 🔐 Secure API endpoints
- ⚡ High-performance FastAPI backend

## Prerequisites

- Python >= 3.10, < 3.14
- Poetry for dependency management

## Installation

1. Install Poetry if you haven't already:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Install dependencies:

```bash
poetry install
```

3. Configure the system:

```bash
# Run the configuration utility to set up your config.toml
python configure.py

# Or manually copy the example config and edit it
cp config/config.example.toml config/config.toml
```

4. Configure OpenAI API (legacy method):

```bash
# Copy the example config and edit with your API key
cp OAI_CONFIG_LIST.example OAI_CONFIG_LIST
```

## Running the Service

### Development Mode

```bash
poetry run dev
```

### Production Mode

```bash
poetry run start
```

The service will start on `http://localhost:5004` by default (configurable via PORT in .env).

## Testing

1. Start the service in one terminal:

```bash
poetry run dev
```

2. In another terminal, run the test vision:

```bash
poetry run test
```

This will send a sample product vision to the team and show their analysis and specifications.

### Available Commands

- `poetry run dev` - Start the service in development mode
- `poetry run start` - Start the service in production mode
- `poetry run test` - Run a test vision through the team
- `poetry run embodied-research` - Run the embodied research example
- `poetry run config-example` - Run the configuration system example

### Available Endpoints

- Health Check: `GET /health`
- Root: `GET /`
- Process Vision: `POST /vision`
  ```json
  {
    "vision": "Your product vision here"
  }
  ```

## Configuration

Roboco uses a flexible TOML-based configuration system. The configuration is stored in `config/config.toml` and can be generated using the `configure.py` script.

### Configuration File Structure

The configuration file is organized into sections:

```toml
# Core settings
[core]
workspace_base = "./workspace"
debug = false

# LLM settings
[llm]
model = "claude-3-opus-20240229"
base_url = "https://api.anthropic.com/v1"
api_key = "${ANTHROPIC_API_KEY}"

# Agent settings
[agents.research_team]
enabled = true
llm = "llm"
```

### Environment Variables

Configuration values can reference environment variables using the `${VAR_NAME}` syntax. For example:

```toml
api_key = "${ANTHROPIC_API_KEY}"
```

This will use the value of the `ANTHROPIC_API_KEY` environment variable.

### Using the Configuration System

You can use the configuration system in your code as follows:

```python
from roboco.config import config

# Load the configuration
config.load()

# Get a configuration value
model_name = config.get('llm.model')

# Get a configuration value with a default
debug_mode = config.get('core.debug', False)

# Get an entire section
llm_config = config.get_section('llm')
```

To see a complete example, run:

```bash
poetry run config-example
```

### Legacy Configuration

Configuration is also managed through environment variables. Key settings in `.env`:

```bash
# Server Configuration
HOST=127.0.0.1
PORT=5004
LOG_LEVEL=info
RELOAD=true

# Development Settings
DEBUG=true
```

## Development

### Project Structure

```
roboco/
├── config/         # Configuration files
├── examples/       # Example usage and tests
└── src/roboco/
    ├── api/        # API endpoints and server configuration
    ├── agents/     # Multi-agent system implementation
    │   ├── roles/  # Agent role definitions
    │   └── team.py # Team coordination logic
    └── tools/      # Tools for agents to use
```

### Running Tests

```bash
poetry run test
```

## License

Apache 2.0

## Contact

- Email: hi@dustland.ai
