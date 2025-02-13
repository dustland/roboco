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

3. Configure OpenAI API:

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

Configuration is managed through environment variables. Key settings in `.env`:

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
src/roboco/
├── api/            # API endpoints and server configuration
├── agents/         # Multi-agent system implementation
│   ├── roles/      # Agent role definitions
│   └── team.py     # Team coordination logic
└── examples/       # Example usage and tests
```

### Running Tests

```bash
poetry run test
```

## License

Apache 2.0

## Contact

- Email: hi@dustland.ai
