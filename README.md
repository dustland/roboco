<p align="center">
  <img src="./assets/logo.png" alt="roboco-logo" width="100"/>
</p>

<h1 align="center">RoboCo: A Robot-driven Company powered by Multi-agent System</h1>

<p align="center">
  <strong>Build, orchestrate, and operate sophisticated AI agent teams.</strong>
</p>

<p align="center">
    <a href="https://github.com/dustland/roboco/blob/main/LICENSE"><img src="https://img.shields.io/github/license/dustland/roboco.svg" alt="License"></a>
    <a href="https://github.com/dustland/roboco/pulls"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome"></a>
    <a href="https://docs.roboco.dev"><img src="https://img.shields.io/badge/documentation-latest-blue.svg" alt="Documentation"></a>
</p>

---

**RoboCo** is a powerful, config-driven framework for creating and managing multi-agent systems. It provides a robust abstraction layer over foundational agent frameworks like [AutoGen](https://github.com/microsoft/autogen), enabling developers to define complex agent teams and workflows through simple configuration files.

Whether you're building a collaborative writing team, a software development crew, or a complex data analysis pipeline, RoboCo provides the tools to make your agents work together seamlessly.

## Key Features

- **Config-Based Design**: Define your entire agent team—their roles, tools, and collaboration patterns—in a single, easy-to-read YAML file.
- **Extensible Tool System**: Integrate any capability into your agent's toolkit, from simple functions to remote enterprise APIs, all within a secure and observable framework.
- **Advanced Context Management**: Overcome LLM context window limitations with a powerful system that provides persistent memory and state management for your agents.
- **Full Observability**: A built-in event system provides real-time visibility into every action, message, and tool call within your system, making debugging and monitoring effortless.
- **Framework Agnostic**: While built on AutoGen, RoboCo is designed to be an abstraction layer, allowing for future integration with other agent backends.

## Getting Started

### Prerequisites

- Python 3.10+

### Installation

Clone the repository and install the required dependencies:

```bash
git clone https://github.com/dustland/roboco.git
cd roboco
pip install -e .
```

## Quick Start: Writing a Blog Post

This example demonstrates a multi-agent team collaborating to write a blog post. A `Planner` agent creates an outline, a `Writer` agent drafts the content, and a `Reviewer` agent polishes the final text.

Run the scenario from the root of the project:

```bash
python examples/scenarios/writing_a_blog_post.py
```

You will see the team in action as they collaborate to produce the final article.

## Documentation

For a deeper dive into the architecture and design of the framework, please refer to our detailed documentation:

- [**System Architecture**](docs/system-architecture.md): A high-level overview of the entire framework.
- [**Config-Based Design**](docs/config-based-design.md): Learn how to define agent teams using YAML.
- [**Context Management**](docs/context-management.md): Understand how agents manage state and memory.
- [**Tool System**](docs/tool-system.md): See how to extend agent capabilities with custom tools.
- [**Event System**](docs/event-system.md): Explore the observability and control plane of the framework.

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to get started.

## Acknowledgments

- Built on top of [AG2](https://github.com/ag2ai/ag2)
- Inspired by [Manus](https://manus.im/) and [OpenManus](https://github.com/mannaandpoem/OpenManus/)
- Thanks to Anthropic for the MCP (Model Context Protocol) design.

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
