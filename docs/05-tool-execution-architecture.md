# Tool Execution Architecture

## Overview

AgentX uses a **task-centric architecture** with **centralized tool execution** for security and control. The primary user interface consists of two global functions: `start_task()` and `execute_task()`.

## Key Design Decisions

### Task-Centric API

Instead of directly instantiating agents, users interact with tasks. This provides a clean abstraction that handles multi-agent coordination, workspace management, and streaming automatically.

### Centralized Tool Execution

All tool execution happens through the orchestrator, not within individual agents. This ensures:

- **Security**: Single point of control for tool access and validation
- **Audit**: Complete logging of all tool usage across agents
- **Resource Management**: Centralized limits and monitoring
- **Consistency**: Uniform tool execution policies

## Module Responsibilities

### Task (`src/agentx/core/task.py`)

**Primary Interface**: The main entry point for all AgentX operations.

**Key Responsibilities**:

- Provides `start_task()` and `execute_task()` global functions
- Manages task lifecycle (initialization, execution, completion)
- Coordinates multi-agent workflows through internal orchestrator
- Handles workspace setup and artifact storage
- Manages conversation history persistence
- Supports both streaming and non-streaming execution

**Workspace Management**: Creates isolated workspace directories with Git-based artifact versioning.

### Orchestrator (`src/agentx/core/orchestrator.py`)

**Central Coordinator**: Handles both agent routing and tool execution.

**Key Responsibilities**:

- **Routing Decisions**: Determines when to complete, handoff, or continue with current agent
- **Agent Coordination**: Routes messages to appropriate agents for processing
- **Tool Execution**: Executes ALL tool calls for security (agents delegate to orchestrator)
- **Security Control**: Validates tool permissions and enforces resource limits
- **Intelligent Handoffs**: Uses LLM-based decision making for complex collaboration patterns

**Security Model**: Single entry point for all tool execution with centralized policies.

### Agent (`src/agentx/core/agent.py`)

**Autonomous Conversation Management**: Each agent manages its own conversation flow.

**Key Responsibilities**:

- Manages conversation rounds with LLM through private Brain
- Builds context-aware system prompts
- **Delegates** tool execution to orchestrator (does not execute tools directly)
- Maintains agent state and configuration
- Provides clean interface to orchestrator

**Autonomy Principle**: Agents are autonomous in conversation management but delegate tool execution for security.

### Brain (`src/agentx/core/brain.py`)

**Pure LLM Interface**: Private to each agent.

**Key Responsibilities**:

- Generates LLM responses (may include tool calls)
- Handles streaming responses
- Manages LLM provider communication
- Formats messages for different LLM providers

**Scope**: Does NOT execute tools or manage conversation state - purely LLM interaction.

### Team (`src/agentx/core/team.py`)

**Configuration Container**: Loads and manages team configurations.

**Key Responsibilities**:

- Loads team configuration from YAML files
- Initializes agent instances from configuration
- Manages handoff rules and collaboration patterns
- Renders agent prompts with Jinja2 templates

**Role**: Pure configuration management - does not handle execution.

## Key Workflows

### Single Agent Task Flow

1. User calls `start_task(prompt)` or `execute_task(prompt, config)`
2. Task creates workspace and loads team configuration
3. Task uses internal orchestrator to route to initial agent
4. Agent generates response through private Brain (may include tool calls)
5. If tool calls needed, agent delegates to orchestrator for execution
6. Orchestrator executes tools securely and returns results to agent
7. Agent continues conversation with tool results until completion
8. Task persists history and artifacts to workspace

### Multi-Agent Collaboration Flow

1. Task routes initial prompt to first agent through orchestrator
2. Agent processes request and returns response
3. Orchestrator makes routing decision (complete, handoff, or continue)
4. If handoff: Task routes to next agent with conversation context
5. Process repeats until orchestrator decides task is complete
6. Task persists final state and artifacts

### Tool Execution Security Flow

1. Agent receives tool calls from Brain (LLM response)
2. Agent calls `orchestrator.execute_tool_calls()` for security
3. Orchestrator validates tool permissions for the requesting agent
4. Orchestrator dispatches to ToolExecutor with resource limits
5. ToolExecutor executes tools and returns structured results
6. Orchestrator logs execution and returns results to agent
7. Agent formats results for next LLM conversation round

## Streaming Support

Both `start_task()` and `execute_task()` support streaming execution:

- **Content Streaming**: Token-by-token LLM responses
- **Event Streaming**: Handoff notifications, tool execution status, routing decisions
- **Progress Updates**: Real-time task progress and agent activity

## Configuration Integration

### Team Configuration (`team.yaml`)

Defines agents, tools, handoff rules, and execution parameters. See `src/agentx/config/` for configuration loading.

### Tool Registration

Tools are registered globally using `@register_tool` decorator. Built-in tools are in `src/agentx/builtin_tools/`.

### Workspace Structure

Each task creates an isolated workspace with:

- `history.jsonl`: Complete conversation log
- `artifacts/`: Git-managed generated files
- Task-specific tool registration

## Security Architecture

### Centralized Control

All tool execution flows through orchestrator, providing:

- Permission validation per agent
- Resource limit enforcement
- Complete audit trail
- Consistent security policies

### Agent Isolation

- Agents cannot execute tools directly
- Private Brain instances (no external access)
- Communication only through defined interfaces
- Independent agent state management

This architecture ensures security while maintaining agent autonomy in conversation management and clean separation of concerns across all components.
