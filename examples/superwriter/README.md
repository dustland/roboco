# SuperWriter Multi-Agent Collaboration System

A comprehensive writing system powered by multiple AI agents working together with task session management and continuation capabilities.

## Features

- 🤖 **Multi-Agent Collaboration**: Planner, Researcher, Writer, Reviewer, and Tool Executor agents
- 📝 **Memory-Driven Workflow**: Agents share context and build upon previous work
- 🔄 **Task Continuation**: Resume tasks from where they left off
- 🆔 **Short Task IDs**: URL-friendly 8-character task identifiers
- 📊 **Progress Tracking**: Monitor rounds, duration, and completion status
- 🔍 **Task Management**: List, search, and manage multiple writing projects

## Quick Start

### Prerequisites

Set up your environment variables:

```bash
export OPENAI_API_KEY="your_openai_api_key"
export SERPAPI_KEY="your_serpapi_key"
```

### Basic Usage

```bash
# Start a new writing task
python main.py "Write a comprehensive guide on sustainable energy"

# List all tasks
python main.py --list

# Resume a specific task
python main.py --resume B5cD8fGh

# Show task details
python main.py --details B5cD8fGh

# Find similar tasks
python main.py --find "energy guide"
```

## Command Reference

### Starting New Tasks

```bash
# Basic task
python main.py "Your task description here"

# With custom round limit
python main.py "Your task description" --max-rounds 30
```

### Task Management

```bash
# Detailed task listing
python main.py --list

# Compact table view
python main.py --list-compact

# Show specific task details
python main.py --details <TASK_ID>

# Find similar tasks
python main.py --find "keyword or description"
```

### Resuming Tasks

```bash
# Resume with default rounds (25)
python main.py --resume <TASK_ID>

# Resume with custom round limit
python main.py --resume <TASK_ID> --max-rounds 10
```

## Task Status Types

- 🟢 **Active**: Currently running or can be resumed
- ⏸️ **Paused**: Manually paused, can be resumed
- ✅ **Completed**: Successfully finished
- ❌ **Failed**: Encountered errors during execution

## Example Workflow

1. **Start a new project**:

   ```bash
   python main.py "Create a business plan for a sustainable tech startup"
   ```

2. **Check progress**:

   ```bash
   python main.py --list-compact
   ```

3. **Resume if needed**:

   ```bash
   python main.py --resume f3THoi5x --max-rounds 20
   ```

4. **View final results**:
   ```bash
   python main.py --details f3THoi5x
   ```

## Agent Roles

- **Planner**: Breaks down tasks and coordinates workflow
- **Researcher**: Gathers information and conducts research
- **Writer**: Creates content based on research and requirements
- **Reviewer**: Reviews and improves written content
- **Tool Executor**: Handles tool calls and external integrations

## Memory System

The system uses a sophisticated memory system where:

- Each task has isolated memory using the task ID as `task_id`
- Agents can store and retrieve context across rounds
- Memory persists between task resumptions
- Shared knowledge builds up throughout the collaboration

## Configuration

The system uses `config/default.yaml` for agent configuration. You can customize:

- Agent prompts and roles
- Tool configurations
- Workflow parameters
- Memory settings

## Output

Results are saved in the `workspace/` directory:

- Task sessions: `workspace/task_sessions.json`
- Memory database: `workspace/memory.db`
- Generated content and artifacts

## Tips

- Use descriptive task descriptions for better results
- Monitor progress with `--list` to see round usage
- Resume tasks that hit round limits to continue work
- Use `--find` to locate related previous work
- Short task IDs (like `B5cD8fGh`) are easy to copy and use

## Troubleshooting

**Task not found**: Check available tasks with `--list`
**Memory errors**: Ensure proper environment variables are set
**Tool executor loops**: This is a known issue being addressed

For more help: `python main.py --help`
