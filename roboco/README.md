# RoboCo

> Multi-Agent System for Humanoid Robot Development

RoboCo is an advanced multi-agent system designed to develop and adapt humanoid robots for specific occupations. Using the AutoGen framework, our system combines expertise in robotics, human behavior analysis, and occupation-specific knowledge to create effective robot workers that can naturally integrate into human workplaces.

## Features

- 🤖 Multi-agent architecture for robot development
- 🧠 Intelligent task delegation and coordination
- 📊 Built-in monitoring and logging
- 🔄 Asynchronous communication between agents
- ⚙️ Flexible configuration system
- 🛠️ CLI tools for service management

## Requirements

- Python >= 3.10, < 3.13
- Poetry for dependency management
- CUDA-enabled GPU (recommended for simulation)
- Ubuntu 24.04 LTS (recommended for ROS2 integration)

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd roboco
```

2. Install dependencies using Poetry:

```bash
poetry install
```

3. Create a configuration file (optional):

```bash
cp config/default.yaml config/local.yaml
```

## Usage

### Starting the Service

Run the RoboCo service using uvicorn:

```bash
# Basic usage
uvicorn roboco.service:app --host 127.0.0.1 --port 8000

# With custom host and port
uvicorn roboco.service:app --host 0.0.0.0 --port 8080

# Development mode with auto-reload
uvicorn roboco.service:app --reload

# With custom log level
uvicorn roboco.service:app --log-level debug
```

The service supports various uvicorn options:

- `--workers`: Number of worker processes
- `--log-level`: Logging level (debug, info, warning, error, critical)
- `--ssl-keyfile`: SSL key file path
- `--ssl-certfile`: SSL certificate file path
- `--proxy-headers`: Enable processing of proxy headers
- `--forwarded-allow-ips`: Allowed IPs for X-Forwarded-For header

### Environment Variables

The service can be configured using environment variables:

- `ROBOCO_CONFIG`: Path to configuration file
- `ROBOCO_LOG_LEVEL`: Logging level
- `ROBOCO_HOST`: Service host
- `ROBOCO_PORT`: Service port

### Validating Configuration

Validate your configuration file:

```bash
poetry run roboco validate --config config/local.yaml
```

### Running Examples

Try the basic example to see the system in action:

```bash
poetry run python examples/basic_usage.py
```

## Project Structure

```
roboco/
├── src/
│   └── roboco/
│       ├── __init__.py
│       ├── agents/         # Agent implementations
│       ├── config.py       # Configuration management
│       ├── cli.py         # Command-line interface
│       └── service.py     # FastAPI service
├── config/
│   └── default.yaml       # Default configuration
├── examples/
│   └── basic_usage.py     # Usage examples
├── tests/                 # Test suite
├── pyproject.toml         # Project metadata and dependencies
└── README.md             # This file
```

## Configuration

RoboCo uses YAML configuration files with the following structure:

```yaml
human:
  llm:
    model: gpt-4-turbo-preview
    temperature: 0.7
    timeout: 600
  additional_config:
    human_input_mode: "ALWAYS"

executive_board:
  llm:
    model: gpt-4-turbo-preview
    temperature: 0.7
    timeout: 600
  additional_config:
    human_input_mode: "NEVER"
# Additional agent configurations...
```

## API Endpoints

The service provides the following REST endpoints:

- `POST /agents/message` - Send messages between agents
- `GET /agents/roles` - List available agent roles
- `GET /agents/status` - Check agent status
- `GET /health` - Service health check

## Development

### Setting Up Development Environment

1. Install development dependencies:

```bash
poetry install --with dev
```

2. Set up pre-commit hooks:

```bash
pre-commit install
```

### Code Style

The project uses:

- Black for code formatting
- isort for import sorting
- mypy for type checking
- ruff for linting

Run all checks:

```bash
poetry run black .
poetry run isort .
poetry run mypy .
poetry run ruff check .
```

### Running Tests

```bash
poetry run pytest
```

## Logging

Logs are stored in the `logs/` directory:

- `roboco.log` - Service logs
- `roboco_cli.log` - CLI logs
- `example.log` - Example script logs

## License

[MIT License](LICENSE)

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
