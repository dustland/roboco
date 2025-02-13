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
- CUDA-enabled GPU (recommended)

## Installation

1. Install Poetry if you haven't already:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Install dependencies:

```bash
poetry install
```

3. Configure environment variables:

```bash
cp .env.example .env
# Edit .env with your settings
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

The service will start on `http://127.0.0.1:5004` by default (configurable via PORT in .env).

### Available Endpoints

- Health Check: `GET /health`
- Root: `GET /`

## Configuration

Configuration is managed through environment variables. Key settings in `.env`:

```bash
# Server Configuration
HOST=127.0.0.1      # The host address to bind to
PORT=5004           # The port number to listen on
LOG_LEVEL=info      # Logging level (debug, info, warning, error, critical)
RELOAD=true         # Enable auto-reload for development

# Development Settings
DEBUG=true          # Enable debug mode
```

## Development

### Project Structure

```
src/roboco/
├── api/            # API endpoints and server configuration
├── core/           # Core business logic and multi-agent system
└── examples/       # Example configurations and usage
```

### Running Tests

```bash
poetry run pytest
```

## License

Apache 2.0

## Contact

- Email: hi@dustland.ai
