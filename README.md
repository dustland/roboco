# RoboCo

> An advanced multi-agent system for humanoid robot development

RoboCo is a comprehensive platform designed to develop and adapt humanoid robots for specific occupations. Using the AutoGen framework, our system combines expertise in robotics, human behavior analysis, and occupation-specific knowledge to create effective robot workers that can naturally integrate into human workplaces.

## System Components

### Backend (roboco)

The core multi-agent system that powers robot adaptation:

- 🤖 Multi-agent architecture for robot development
- 🧠 Intelligent task delegation and coordination
- 📊 Built-in monitoring and logging
- 🔄 Asynchronous communication between agents
- ⚙️ Flexible configuration system

[Learn more about the backend →](roboco/README.md)

### Frontend (Studio)

A modern web interface for robot development and monitoring:

- 🎯 Intuitive robot task configuration
- 📈 Real-time monitoring and analytics
- 🔍 Detailed agent interaction visualization
- 🛠️ Development tools and debugging interfaces

## Quick Start

1. Clone the repository:

```bash
git clone <repository-url>
cd roboco
```

2. Set up the backend:

```bash
cd roboco
poetry install
uvicorn roboco.service:app --reload
```

3. Set up the frontend:

```bash
cd ../studio
pnpm install
pnpm dev
```

## Requirements

- Python >= 3.10, < 3.13
- Poetry for dependency management
- Node.js >= 18
- PNPM package manager
- CUDA-enabled GPU (recommended)
- Ubuntu 24.04 LTS (recommended)

## Documentation

- [Backend Documentation](roboco/README.md)
- [API Documentation](roboco/docs/api.md)
- [Architecture Overview](roboco/docs/design/arch.md)

## Development

Please refer to the component-specific documentation for detailed development instructions:

- [Backend Development Guide](roboco/README.md#development)
- [Frontend Development Guide](studio/README.md)

## License

[Apache 2.0](LICENSE)

## Contact

- Email: hi@dustland.ai

---

© 2024 Dustland AI. All rights reserved.
