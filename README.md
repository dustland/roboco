<div align="center">
  <img src="https://dustland.github.io/agentx/logo.png" alt="AgentX Logo" width="120">
  <h1 align="center">AgentX</h1>
</div>

<p align="center">
  <b>An open-source framework for building autonomous AI agent teams.</b>
  <br />
  <a href="https://dustland.github.io/agentx"><strong>Explore the docs »</strong></a>
  <br />
  <br />
  <a href="https://pypi.org/project/agentx-py/"><img src="https://img.shields.io/pypi/v/agentx-py.svg" alt="PyPI version" /></a>
  <a href="https://pypi.org/project/agentx-py/"><img src="https://img.shields.io/pypi/dm/agentx-py.svg" alt="PyPI downloads" /></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-blue.svg" /></a>
  <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg"/></a>
  <a href="https://github.com/dustland/agentx/issues/new?assignees=&labels=bug&template=bug_report.md&title="><img src="https://img.shields.io/badge/Report%20an%20Issue-d73a4a?style=flat-square" alt="Report an Issue"/></a>
  <a href="https://github.com/dustland/agentx/issues/new?assignees=&labels=enhancement&template=feature_request.md&title="><img src="https://img.shields.io/badge/Request%20a%20Feature-0366d6?style=flat-square" alt="Request a Feature"/></a>
</p>

AgentX provides the backbone for creating, orchestrating, and observing sophisticated multi-agent systems. It moves beyond simple agent-to-agent communication to a robust, task-driven framework where teams of specialized agents collaborate to achieve complex goals.

## ✨ Key Features

Based on a refined and modular architecture, AgentX is built around a few core concepts:

- **🤖 Multi-Agent Teams**: Define teams of specialized agents in simple YAML files. Each agent can have its own role, tools, and configuration.
- **🗣️ Natural Language Orchestration**: Agents hand off tasks to each other using natural language. A central `TaskExecutor` interprets these handoffs and routes work to the appropriate agent, enabling complex, dynamic workflows.
- **🛠️ Secure & Extensible Tools**: Tools are defined with Python decorators and their schemas are automatically generated. Shell commands are executed in a secure Docker sandbox, providing safety and isolation. A flexible `ToolExecutor` manages the entire lifecycle.
- **🧠 Stateful & Context-Aware Memory**: Agents maintain long-term memory, enabling them to recall past interactions and context. The memory system supports semantic search, ensuring agents have the information they need, when they need it.
- **📡 Streamable Communication**: The entire lifecycle of a task, from agent thoughts to tool calls and results, is available as a real-time stream of events. This allows you to build rich, observable UIs like the Vercel AI SDK.
- **🎯 Task-Centric API**: Interact with the system through a simple, powerful API. Kick off complex workflows with `execute_task()` or manage interactive sessions with `start_task()`.

## 🚀 Getting Started

The best way to get started is by following our **[Getting Started](https://dustland.github.io/agentx/docs/getting-started/)**, which will walk you through building a simple chat application and a multi-agent writer/reviewer team.

### 1. Installation

Install AgentX from PyPI:

```sh
pip install agentx-py
```

Or for development, clone the repository:

```sh
git clone https://github.com/dustland/agentx.git
cd agentx
uv sync
```

### 2. Usage Examples

AgentX can be run directly from the command line or via its Python API. You can find complete, working examples in the `examples/` directory.

#### Running an Example

This demonstrates a basic multi-agent collaboration:

```bash
# Navigate to an example directory
cd examples/simple_team

# Run the demo script
python demo.py
```

#### Using the CLI

The framework includes a powerful CLI for managing your agent system:

```bash
# Start the API server
agentx start

# Monitor tasks and events in your terminal
agentx monitor

# Launch the web dashboard for rich observability
agentx monitor --web

# Run a named example directly
agentx example superwriter
```

#### Using the Python API

Here is a simple example of an autonomous run:

```python
import asyncio
from agentx import execute_task

async def main():
    # Execute a task with a simple prompt
    result = await execute_task("Write a brief report on renewable energy trends")

    print(f"Success: {result.success}")
    print(f"Summary: {result.summary}")
    print(f"Conversation rounds: {len(result.conversation_history)}")

asyncio.run(main())
```

_The script above shows a simple autonomous run. For more advanced patterns like message streaming and interactive sessions, please see the complete scripts in the `/examples` directory._

## 📊 Observability & Monitoring

AgentX includes a comprehensive observability system for monitoring and debugging multi-agent workflows.

Launch a modern web dashboard built with FastAPI and Preline UI:

```bash
# Start web dashboard
agentx monitor --web
```

- **Dashboard**: System overview with metrics and recent activity.
- **Tasks**: Task conversation history viewer with export.
- **Events**: Real-time event monitoring with filtering.
- **Memory**: Memory browser with search and categories.
- **Messages**: Agent conversation history during execution.
- **Configuration**: System configuration and status viewer.

You can also use the observability features in CLI mode without the option `--web`.

## 🛠️ Tech Stack

AgentX is built on a robust foundation of modern Python technologies and AI services:

### 🧠 **AI & LLM Integration**

- **[LiteLLM](https://github.com/BerriAI/litellm)** - Unified interface for 100+ LLM providers (OpenAI, Anthropic, DeepSeek, etc.)
- **[Pydantic](https://pydantic.dev/)** - Data validation and settings management with type hints

### 🧠 **Memory & Knowledge**

- **[Mem0](https://github.com/mem0ai/mem0)** - Intelligent memory layer for long-term context retention
- **[ChromaDB](https://www.trychroma.com/)** - Vector database for semantic search and embeddings

### 🔧 **Core Framework**

- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern web framework for APIs and observability dashboard
- **[Asyncio](https://docs.python.org/3/library/asyncio.html)** - Asynchronous programming for concurrent agent execution
- **[YAML](https://pyyaml.org/)** - Human-readable configuration files for teams and agents

### 🛡️ **Security & Isolation**

- **[Docker](https://www.docker.com/)** - Containerized execution environment for secure tool execution
- **[Subprocess](https://docs.python.org/3/library/subprocess.html)** - Isolated process execution with security controls

### 📊 **Observability & Monitoring**

- **[Preline UI](https://preline.co/)** - Modern UI components for the web dashboard
- **[Jinja2](https://jinja.palletsprojects.com/)** - Template engine for dynamic web interfaces
- **Event-driven architecture** - Real-time streaming and monitoring capabilities

### 🔍 **Search & Web**

- **[SerpAPI](https://serpapi.com/)** - Web search capabilities for agents
- **[BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)** - Web scraping and content extraction

### 📦 **Development & Packaging**

- **[UV](https://github.com/astral-sh/uv)** - Fast Python package installer and resolver
- **[Pytest](https://pytest.org/)** - Testing framework with comprehensive test coverage

You can discover more architectural details in our documentation:

- **[System Architecture](docs/arch/01-architecture.md)** - Overall design and system architecture
- **[State and Context Management](docs/arch/02-state-and-context.md)** - State and Context management
- **[Tool Calling](docs/arch/03-tool-call.md)** - Invoke tools for actual tasks
- **[Communication and Message](docs/arch/04-communication.md)** - Message format for composite content and streaming

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 🙏 Acknowledgments

This project was initially inspired by and built upon concepts from [AG2 (AutoGen)](https://github.com/ag2ai/ag2), an excellent multi-agent conversation framework. While AgentX has evolved into its own distinct architecture and approach, we're grateful for the foundational ideas and patterns that AG2 provided to the multi-agent AI community.

## 📄 License

Licensed under the Apache License 2.0 - see [LICENSE](LICENSE) for details.

---

**Built with ❤️ by the [Dustland](https://github.com/dustland) team**
