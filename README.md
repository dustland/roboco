# Roboco - Multi-Agent Collaboration Framework

[![PyPI version](https://badge.fury.io/py/roboco.svg)](https://badge.fury.io/py/roboco)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Roboco is a production-ready framework for building collaborative AI agent teams. Built on AG2 (AutoGen) with a powerful configuration-based approach, it enables you to create sophisticated multi-agent workflows without writing complex code.

## 🚀 Key Features

- **Configuration-Based Teams**: Define agents, tools, and workflows in YAML files
- **Jinja2 Template System**: Dynamic prompt generation with template variables
- **Comprehensive Memory System**: Intelligent chunking, semantic search, and context management
- **Event-Driven Architecture**: Real-time monitoring and control of agent interactions
- **Tool Ecosystem**: Built-in tools plus extensible tool registry
- **Multi-Session Server**: Optional server component for multi-user scenarios
- **Production Ready**: Designed for scalability, reliability, and observability

## 📦 Installation

```bash
pip install roboco
```

### Development Installation

```bash
git clone https://github.com/dustland/roboco.git
cd roboco
pip install -e .
```

## 🏃‍♂️ Quick Start

### Simple Usage

```python
import asyncio
from roboco import collaborate

async def main():
    # One-line collaboration
    result = await collaborate(
        "config/team.yaml",
        "Write a brief report on renewable energy trends"
    )
    print(result.summary)

asyncio.run(main())
```

### Configuration-Based Teams

```python
from roboco import TeamBuilder

# Create a team from configuration
team = TeamBuilder.create_team("config/team.yaml")

# Run a task
result = await team.run("Analyze the competitive landscape for AI tools")
print(result.summary)
```

### Using Preset Teams

```python
from roboco import create_research_writing_team

# Create a specialized research team
team = create_research_writing_team(
    template_variables={
        "research_domain": "artificial intelligence",
        "target_audience": "technical professionals"
    }
)

result = await team.run("Research recent advances in large language models")
```

## 🎯 Configuration System

Roboco uses a powerful configuration system with Jinja2 templates for maximum flexibility.

### Team Configuration (`config/team.yaml`)

```yaml
name: "ResearchTeam"
description: "A team specialized in research and writing"

# Global variables for all templates
variables:
  project_name: "AI Research Project"
  expertise_level: "expert"

agents:
  - name: researcher
    class: "roboco.core.agents.Agent"
    llm_config:
      config_list:
        - model: "gpt-4"

  - name: writer
    class: "roboco.core.agents.Agent"

  - name: executor
    class: "roboco.core.agents.ToolExecutorAgent"

tools:
  - name: web_search
    module: "roboco.builtin_tools.search_tools"
    class_name: "WebSearchTool"
    allowed_agents: ["researcher"]

  - name: filesystem
    module: "roboco.builtin_tools.basic_tools"
    class_name: "FileSystemTool"
    allowed_agents: ["writer", "executor"]
```

### Role Configuration (`config/roles.yaml`)

```yaml
roles:
  researcher:
    template_file: "researcher.md"
    temperature: 0.7
    template_variables:
      specialization: "AI and machine learning"
      research_methods:
        ["literature review", "data analysis", "expert interviews"]

  writer:
    template_file: "writer.md"
    temperature: 0.8
    template_variables:
      writing_style: "academic"
      target_audience: "researchers and practitioners"
```

### Role Templates (`config/roles/researcher.md`)

```markdown
You are a {{ specialization }} researcher with {{ expertise_level }} level expertise.

Your primary role is to conduct thorough research on {{ project_name }} using these methods:
{% for method in research_methods %}

- {{ method }}
  {% endfor %}

Guidelines:

- Always verify information from multiple sources
- Provide citations for all claims
- Focus on recent developments (last 2-3 years)
- Maintain objectivity and identify potential biases

When researching, use the available tools to gather comprehensive information.
```

## 🧠 Memory System

Roboco integrates with [Mem0](https://mem0.ai) to provide state-of-the-art memory capabilities for AI agents:

### Key Features

- **26% Higher Accuracy** than OpenAI Memory
- **91% Faster Responses** than full-context approaches
- **90% Lower Token Usage** for cost-effective operations
- **Intelligent Memory Extraction** using LLMs
- **Semantic Search** with vector embeddings
- **Multi-level Memory**: User, Agent, and Session-based storage

```python
from roboco.memory import MemoryManager
from roboco.config.models import MemoryConfig

# Initialize memory manager with Mem0
config = MemoryConfig()
memory = MemoryManager(config)

# Add conversation memories (automatically extracts facts)
conversation = [
    {"role": "user", "content": "I love Italian food, especially pasta carbonara"},
    {"role": "assistant", "content": "Great choice! Carbonara is a classic Roman dish."}
]

memory.add_memory(
    content=conversation,
    user_id="user123",
    metadata={"topic": "food_preferences"}
)

# Search memories semantically
results = memory.search_memory(
    query="What food does the user like?",
    user_id="user123",
    limit=5
)

# List memories by user/agent/session
user_memories = memory.list_memories(user_id="user123")
agent_memories = memory.list_memories(agent_id="assistant")
session_memories = memory.list_memories(run_id="session_001")
```

### Memory Operations

- **Add**: Store conversations or facts with automatic extraction
- **Search**: Semantic similarity search across memories
- **List**: Filter memories by user, agent, or session
- **Update**: Modify existing memory content
- **Delete**: Remove specific memories
- **Clear**: Bulk delete with filtering options

## 🔧 Tool System

Built-in tools and easy extensibility:

```python
from roboco.tool import AbstractTool
from roboco.config.models import ToolParameterConfig

class CustomTool(AbstractTool):
    def __init__(self):
        self.name = "custom_analysis"
        self.description = "Performs custom data analysis"
        self.parameters_schema = [
            ToolParameterConfig(
                name="data_source",
                type="string",
                description="Path to data file",
                required=True
            )
        ]

    async def execute(self, **kwargs) -> str:
        data_source = kwargs.get("data_source")
        # Your custom logic here
        return f"Analysis complete for {data_source}"
```

## 🌐 Server Mode (Optional)

For multi-user scenarios:

```python
from roboco.server import create_app

# Create FastAPI server
app = create_app()

# Run with: uvicorn app:app --host 0.0.0.0 --port 8000
```

### API Usage

```bash
# Create a session
curl -X POST "http://localhost:8000/sessions" \
  -H "Content-Type: application/json" \
  -d '{"config_path": "config/team.yaml"}'

# Start collaboration
curl -X POST "http://localhost:8000/sessions/{session_id}/collaborate" \
  -H "Content-Type: application/json" \
  -d '{"task": "Analyze market trends in renewable energy"}'
```

## 📊 Event System

Monitor and control agent interactions:

```python
from roboco.event import InMemoryEventBus

# Create event bus
event_bus = InMemoryEventBus()

# Subscribe to events
@event_bus.subscribe("agent.message.sent")
async def on_agent_message(event):
    print(f"Agent {event.payload['agent_id']} sent: {event.payload['message']}")

# Use with team
team = TeamBuilder.create_team("config/team.yaml")
team.event_bus = event_bus
```

## 📚 Examples

Check out the `examples/` directory for complete working examples:

- **Research Writing Team**: Multi-agent research and report generation
- **Software Development Team**: Code generation and review workflow
- **Planning Team**: Strategic planning and task breakdown
- **Customer Support Team**: Multi-tier support with escalation

## 🔧 Development

### Requirements

- Python 3.11+
- OpenAI API key (set `OPENAI_API_KEY` environment variable)

### Testing

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=roboco
```

### Code Quality

```bash
# Format code
black src/

# Type checking
mypy src/

# Linting
flake8 src/
```

## 🏗️ Architecture

Roboco follows a modular architecture with four core subsystems:

1. **Execution Core**: TeamManager, Agents, and collaboration orchestration
2. **Config System**: YAML-based configuration with Jinja2 templating
3. **Memory System**: Intelligent storage and retrieval with chunking
4. **Event System**: Publish-subscribe architecture for observability
5. **Tool System**: Extensible tool registry with security controls

For detailed architecture information, see the [documentation](docs/).

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♀️ Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/dustland/roboco/issues)
- **Discussions**: [GitHub Discussions](https://github.com/dustland/roboco/discussions)

## 🚀 Roadmap

- [ ] Enhanced MCP (Model Context Protocol) support
- [ ] Vector database backends (Pinecone, Weaviate, Qdrant)
- [ ] Web-based team configuration UI
- [ ] Integration with more LLM providers
- [ ] Advanced workflow orchestration
- [ ] Production deployment templates

---

**Built with ❤️ by the Dustland team**
