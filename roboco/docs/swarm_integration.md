# AG2 Swarm Integration in Roboco

This document explains how AG2's Swarm orchestration pattern has been integrated into the Roboco framework to enable more effective agent collaboration.

## Overview

The Swarm pattern allows multiple agents to collaborate on complex tasks with a shared context and intelligent handoffs between agents. This implementation follows our direct AG2 integration approach, avoiding unnecessary abstractions and leveraging AG2's native capabilities.

## Core Components

### 1. Team Class Enhancements

The `Team` base class has been enhanced with Swarm capabilities:

```python
# Enable swarm for a team
team.enable_swarm(shared_context={})

# Register conditional handoffs
team.register_handoff(
    agent_name="AgentA", 
    target_agent_name="AgentB",
    condition="When task X is complete"
)

# Register default handoffs
team.register_default_handoff(
    agent_name="AgentA",
    target_agent_name="AgentC"  # or None to terminate
)

# Configure all handoffs with AG2
team.configure_swarm_handoffs()

# Run a scenario with swarm orchestration
result = team.run_scenario(
    prompt="Initial message",
    use_swarm=True,
    context_variables={"key": "value"}
)
```

### 2. Specialized Agent Roles

The ResearchTeam implementation demonstrates how to create specialized agent roles:

- **ProductManager**: Coordinates research and defines objectives
- **Researcher**: Analyzes data and extracts insights
- **ReportWriter**: Creates structured, comprehensive reports
- **ToolUser**: Executes web searches and file operations

### 3. Conditional Handoffs

Agents can pass control to other agents based on natural language conditions:

```python
self.register_handoff(
    agent_name="ProductManager",
    target_agent_name="Researcher",
    condition="When search results need to be analyzed"
)
```

## Shared Context

All agents in the swarm share a common context dictionary, allowing them to:

1. Access shared data
2. Update research findings
3. Track the state of the workflow
4. Pass information between agents

## Implementation Details

### Key Methods

- `enable_swarm()`: Activates swarm capabilities for a team
- `register_handoff()`: Defines conditional transitions between agents
- `register_default_handoff()`: Sets default behavior when no conditions match
- `configure_swarm_handoffs()`: Finalizes handoff configuration
- `run_swarm()`: Executes a scenario using swarm orchestration

### Integration with AG2

This implementation directly uses AG2's swarm components:

```python
from autogen import (
    register_hand_off,
    OnCondition,
    AfterWork,
    AfterWorkOption,
    SwarmResult,
    initiate_swarm_chat
)
```

## Usage Example

The market research example demonstrates a complete workflow:

```python
# Create a team with swarm capabilities
team = ResearchTeam()

# Run a research scenario
result = team.run_scenario(
    "Research cutting-edge embodied AI applications"
)

# Access the research report
report_path = result.get("report_path")
```

## Benefits

1. **Specialized Expertise**: Each agent focuses on its strengths
2. **Efficient Collaboration**: Automatic handoffs based on task needs
3. **Shared Knowledge**: All agents work with the same context
4. **Flexible Workflow**: Natural language conditions determine transitions
5. **Maintainable Code**: Direct integration with AG2 without abstractions

## Next Steps

1. Add more specialized agent roles for different domains
2. Implement context-based handoffs for more complex workflows
3. Create visualization tools for swarm interactions
4. Add metrics collection for swarm performance analysis
