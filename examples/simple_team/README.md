# Simple Team Example - Enhanced with Memory & Task Resumption

This example demonstrates Roboco's multi-agent collaboration capabilities with intelligent memory integration and task resumption features.

## Features

- 🧠 **Memory Integration**: Agents can store and retrieve insights across tasks
- 🔄 **Task Resumption**: Continue interrupted tasks from where they left off
- 👥 **Multi-Agent Collaboration**: Planner, Writer, and Executor agents working together
- 📊 **Task Persistence**: All task progress is automatically saved
- 🔍 **Memory Search**: Semantic search across stored memories
- 📈 **Progress Tracking**: Monitor task completion and memory usage

## Quick Start

### Prerequisites

1. **Install Dependencies**:

   ```bash
   pip install mem0ai  # For memory features
   ```

2. **Set API Key**:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

### Running the Demo

1. **Interactive Demo** (Recommended):

   ```bash
   cd examples/simple_team
   python demo.py
   ```

   Choose option 2 for interactive mode to explore features step by step.

2. **Memory & Resumption Tests**:

   ```bash
   python test_memory_resume.py
   ```

3. **Automatic Demo**:
   ```bash
   python demo.py
   ```
   Choose option 1 to run all demos automatically.

## Memory Features

### Memory Operations

Agents can:

- **Store insights**: Save important decisions and findings
- **Search context**: Find relevant information from previous work
- **Build continuity**: Reference past work across different tasks

### Memory Usage Examples

```python
# Search for relevant context
search_memory(query="documentation style", limit=5)

# Store important decisions
add_memory(
    content="User prefers concise docs with examples",
    agent_id="writer",
    task_id="{task_id}",
    metadata={"topic": "style_guide"}
)

# List task-specific memories
list_memories(task_id="specific_task_id", limit=10)
```

## Task Resumption

### How It Works

1. **Automatic Saving**: All task progress is saved incrementally
2. **Task IDs**: Each task gets a unique identifier for resumption
3. **State Recovery**: Resume from exact conversation state
4. **Memory Continuity**: Access all memories from previous rounds

### Resumption Commands

```bash
# List all tasks
python -c "
import asyncio
from roboco.core.cli import list_tasks
asyncio.run(list_tasks())
"

# Show task details
python -c "
import asyncio
from roboco.core.cli import show_task_details
asyncio.run(show_task_details('TASK_ID_HERE'))
"

# Resume a task
python -c "
import asyncio
from roboco.core.cli import resume_task
asyncio.run(resume_task('TASK_ID_HERE', max_rounds=10))
"
```

## Configuration

### Team Configuration (`config/team.yaml`)

The team includes:

- **Planner**: Creates project plans and task breakdowns
- **Writer**: Produces documentation and content
- **Executor**: Handles tool execution and file operations

### Memory Configuration

Memory is configured to use:

- **ChromaDB**: Local vector database (no external services needed)
- **OpenAI Embeddings**: For semantic search
- **Local Storage**: `./workspace/memory_db`

## Example Workflows

### 1. Planning and Documentation

```python
# Start a planning task
result = await run_task(
    config_path="config/team.yaml",
    task_description="Create a project plan for a Python web API",
    max_rounds=15
)

# Resume with additional requirements
await resume_task(
    task_id=result.task_id,
    max_rounds=10
)
```

### 2. Research and Writing

```python
# Research task with memory storage
await run_task(
    config_path="config/team.yaml",
    task_description="""
    Research Python testing best practices.
    Store key insights in memory for future reference.
    Create comprehensive documentation.
    """,
    max_rounds=20
)
```

### 3. Building on Previous Work

```python
# Task that references previous memories
await run_task(
    config_path="config/team.yaml",
    task_description="""
    Create a code review checklist.
    Search memory for previous work on coding standards.
    Build upon existing knowledge about best practices.
    """,
    max_rounds=15
)
```

## File Structure

```
simple_team/
├── config/
│   ├── team.yaml              # Team configuration
│   └── prompts/               # Agent prompts with memory operations
│       ├── planner.md         # Enhanced with memory features
│       ├── writer.md          # Memory-aware writing
│       └── ...
├── workspace/
│   ├── memory_db/             # Local memory database
│   ├── task_sessions.json     # Task persistence
│   └── outputs/               # Generated content
├── demo.py                    # Interactive demo script
├── test_memory_resume.py      # Memory & resumption tests
└── README.md                  # This file
```

## Testing

### Memory Features Test

```bash
python test_memory_resume.py
```

Tests include:

- ✅ Memory storage and retrieval
- ✅ Task-specific memory isolation
- ✅ Semantic search functionality
- ✅ Task execution and resumption
- ✅ Memory persistence across sessions

### Interactive Testing

Use the interactive demo to:

1. Create tasks with memory storage
2. Resume interrupted tasks
3. Search and explore stored memories
4. Test cross-task knowledge sharing

## Troubleshooting

### Common Issues

1. **Memory Database Issues**:

   ```bash
   # Clear memory database if needed
   rm -rf workspace/memory_db
   ```

2. **Task Session Corruption**:

   ```bash
   # Reset task sessions
   rm workspace/task_sessions.json
   ```

3. **API Key Issues**:
   ```bash
   # Verify API key is set
   echo $OPENAI_API_KEY
   ```

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Advanced Usage

### Custom Memory Queries

```python
from roboco.memory.manager import MemoryManager

memory_manager = MemoryManager()

# Search across all tasks
results = memory_manager.search_memory(
    query="project planning strategies",
    limit=10
)

# Filter by agent
agent_memories = memory_manager.list_memories(
    agent_id="planner",
    limit=20
)

# Task-specific search
task_results = memory_manager.search_memory(
    query="documentation requirements",
    task_id="specific_task_id",
    limit=5
)
```

### Custom Team Configuration

Modify `config/team.yaml` to:

- Add new agents
- Configure different LLM models
- Adjust memory settings
- Add custom tools

## Next Steps

1. **Explore Prompts**: Check `config/prompts/` for memory-enhanced agent prompts
2. **Customize Configuration**: Modify `config/team.yaml` for your use case
3. **Build Custom Workflows**: Create task sequences that leverage memory
4. **Scale Up**: Use with larger, more complex multi-agent workflows

## Support

For issues or questions:

1. Check the main Roboco documentation
2. Review the test scripts for usage examples
3. Examine the configuration files for customization options
