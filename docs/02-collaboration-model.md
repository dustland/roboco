# 02: Collaboration & Planning Model

This document specifies the dynamic aspects of the Roboco framework: how agents collaborate to achieve a goal and how that work is planned and tracked. It builds on the components defined in `01-architecture.md`.

## 1. The Execution Plan: `plan.json`

A robust execution plan is the key to successfully completing complex, multi-step tasks. The framework elevates the plan to a first-class, structured artifact.

- **(Req #18)** At the start of a task, a `plan.json` file is created in the `Task Workspace`.
- This file is a structured list of tasks, not a simple markdown file. This allows agents to interact with it programmatically.
- **(Req #18)** The plan supports autonomous execution with minimal human intervention.

### 1.1. `plan.json` Schema

The file will contain a JSON object with a single key, `tasks`, which is a list of task objects.

**Example `plan.json`:**

```json
{
  "tasks": [
    {
      "task_id": "task_001",
      "description": "Analyze the project requirements and create a file structure.",
      "status": "completed",
      "assigned_agent": "analyst",
      "priority": "high",
      "dependencies": [],
      "estimated_duration": "15m",
      "metadata": {
        "completed_at": "2023-10-27T10:00:00Z",
        "artifacts_created": ["project_structure.md"]
      }
    },
    {
      "task_id": "task_002",
      "description": "Write the main application logic in app.py.",
      "status": "in_progress",
      "assigned_agent": "coder",
      "priority": "high",
      "dependencies": ["task_001"],
      "estimated_duration": "30m",
      "metadata": {
        "started_at": "2023-10-27T10:05:00Z",
        "progress_percentage": 60
      }
    },
    {
      "task_id": "task_003",
      "description": "Create unit tests for app.py.",
      "status": "pending",
      "assigned_agent": "tester",
      "priority": "medium",
      "dependencies": ["task_002"],
      "estimated_duration": "20m",
      "metadata": {}
    }
  ],
  "execution_mode": "autonomous",
  "human_intervention_points": ["before_deployment", "on_error"],
  "success_criteria": ["all_tests_pass", "code_coverage_80_percent"]
}
```

### 1.2. Plan Interaction Tools

Agents will be provided with built-in tools to manage the plan, for example:

- `plan_add_task(description: str, priority: str, dependencies: List[str])`: Adds a new task to the plan with `pending` status.
- `plan_update_task(task_id: str, status: str, metadata: dict)`: Updates the status and metadata of an existing task.
- `plan_read()`: Returns the full content of `plan.json`.
- `plan_assign_task(task_id: str, agent_name: str)`: Assigns a task to a specific agent.
- `plan_estimate_duration(task_id: str, duration: str)`: Sets estimated duration for a task.
- `plan_set_dependencies(task_id: str, dependencies: List[str])`: Defines task dependencies.

## 2. The Collaboration Model: Handoffs

**(Req #11)** The framework uses **Handoffs** to manage the flow of control between agents, a concept inspired by the OpenAI Agents SDK. A handoff is a specific type of tool call that signals the `Orchestrator` to switch the active agent.

- **(Req #4)** Handoffs enable dynamic, intelligent routing that can be determined by the agent at runtime based on the task's progress.
- **(Req #23)** The design supports advanced collaboration patterns including parallel execution and hierarchical teams.

### 2.1. The `handoff` Tool

A built-in tool named `handoff` will be available to all agents.

- **Signature:** `handoff(destination_agent: str, reason: str, context: Optional[Dict[str, Any]] = None)`
- When an agent calls this tool, it is signaling that its work for the current turn is complete and that the specified `destination_agent` should act next.
- **(Req #20)** The context parameter allows passing relevant memory and state information.

**Example `TaskStep` for a handoff:**

```json
{
  "step_id": "step_abc",
  "agent_name": "coder",
  "parts": [
    {
      "type": "text",
      "text": "I have finished writing the code for app.py. Handing off to the tester."
    },
    {
      "type": "tool_call",
      "tool_call": {
        "id": "tc_123",
        "tool_name": "handoff",
        "args": {
          "destination_agent": "tester",
          "reason": "Code implementation is complete, ready for testing.",
          "context": {
            "files_modified": ["app.py"],
            "test_requirements": ["unit_tests", "integration_tests"],
            "priority": "high"
          }
        }
      }
    }
  ]
}
```

### 2.2. Orchestrator Logic for Handoffs

When the `Orchestrator` receives a `TaskStep` containing a `handoff` tool call, it will:

1.  **Intercept:** It will _not_ send this tool call to the `Tool Executor`.
2.  **Validate:** It checks that the `destination_agent` exists in the current team configuration.
3.  **Memory Update:** **(Req #20)** Updates the memory manager with handoff context and reasoning.
4.  **Switch Context:** It sets the `active_agent` to the `destination_agent`.
5.  **Continue Loop:** It proceeds with the main execution loop, now preparing to invoke the new active agent in the next turn.

This model allows for powerful and flexible workflows. For example, a `tester` agent could examine the results of a test run and decide to either `handoff` back to the `coder` (if tests fail) or `handoff` to a `deployer` agent (if tests pass).

## 3. Advanced Collaboration Patterns

**(Req #23)** The framework supports sophisticated collaboration models beyond simple handoffs:

### 3.1. Parallel Execution

Multiple agents can work simultaneously on different aspects of a task:

```yaml
# Example team configuration for parallel execution
collaboration_patterns:
  parallel_groups:
    - name: "development_team"
      agents: ["frontend_dev", "backend_dev", "database_dev"]
      coordination_agent: "tech_lead"
      sync_points: ["design_review", "integration_testing"]
```

**Parallel Handoff Tool:**

- `parallel_handoff(agents: List[str], tasks: List[str], coordination_strategy: str)`

### 3.2. Dynamic Team Formation

Runtime creation and modification of agent teams:

**Dynamic Team Tools:**

- `create_team(team_name: str, agents: List[str], purpose: str)`
- `modify_team(team_name: str, add_agents: List[str], remove_agents: List[str])`
- `dissolve_team(team_name: str, reason: str)`

### 3.3. Consensus Building

Mechanisms for agents to reach agreement on decisions:

**Consensus Tools:**

- `propose_decision(decision: str, rationale: str, stakeholders: List[str])`
- `vote_on_proposal(proposal_id: str, vote: str, reasoning: str)`
- `finalize_consensus(proposal_id: str)`

### 3.4. Custom Collaboration Patterns

Teams can define custom collaboration workflows through configuration:

```yaml
# Example custom collaboration pattern
collaboration_patterns:
  - name: "code_review_cycle"
    type: "custom"
    workflow:
      - step: "code_generation"
        agent: "coder"
        next_on_success: "code_review"
        next_on_failure: "error_handler"
      - step: "code_review"
        agent: "reviewer"
        next_on_approve: "testing"
        next_on_reject: "coder"
      - step: "testing"
        agent: "tester"
        next_on_pass: "deployment"
        next_on_fail: "coder"
```

## 4. Autonomous Execution Capabilities

**(Req #18)** The framework enables fully autonomous multi-step task execution:

### 4.1. Autonomous Planning

- Agents can create and modify execution plans without human intervention
- Automatic task decomposition based on complexity analysis
- Dynamic replanning when obstacles or new requirements are encountered

### 4.2. Self-Monitoring and Adaptation

- Continuous progress monitoring against success criteria
- Automatic error detection and recovery strategies
- Performance optimization based on execution metrics

### 4.3. Resource Management

- Automatic allocation of agents to tasks based on capabilities and availability
- Load balancing across parallel execution streams
- Deadline-aware task prioritization and scheduling

## 5. Human-in-the-Loop (HITL) Integration

**(Req #19)** The framework provides configurable human intervention points:

### 5.1. Intervention Triggers

- **Approval Gates**: Require human approval before critical actions
- **Error Escalation**: Automatically involve humans when errors exceed thresholds
- **Quality Checkpoints**: Pause for human review at specified milestones
- **Decision Points**: Involve humans in complex decision-making scenarios

### 5.2. HITL Tools

**Human Interaction Tools:**

- `request_approval(action: str, context: Dict[str, Any], timeout: int)`
- `escalate_to_human(issue: str, urgency: str, required_expertise: List[str])`
- `request_feedback(artifact: str, questions: List[str])`

### 5.3. Intervention Modes

- **Synchronous**: Execution pauses until human response is received
- **Asynchronous**: Execution continues on other tasks while waiting for human input
- **Advisory**: Human input is requested but not required for continuation

## 6. Universal Tool Support

**(Req #9)** The framework supports a variety of tools through a universal interface:

### 6.1. Built-in Tools

Core tools provided by the framework:

- `handoff`: Agent-to-agent routing
- `parallel_handoff`: Multi-agent coordination
- `plan_add_task`, `plan_update_task`, `plan_read`: Plan management
- `create_artifact`, `read_artifact`: File system operations
- `web_search`, `code_search`: Information retrieval
- `request_approval`, `escalate_to_human`: HITL integration
- `store_memory`, `retrieve_memory`, `search_memory`: Memory management
- `create_team`, `modify_team`, `dissolve_team`: Dynamic team formation
- `propose_decision`, `vote_on_proposal`, `finalize_consensus`: Consensus building

### 6.2. Custom Tools

User-defined tools loaded from the team configuration:

- Python functions with type annotations
- Shell scripts with parameter definitions
- Docker containers with standardized interfaces

### 6.3. MCP-Based Tools

**(Req #9)** Model Context Protocol (MCP) tools:

- External tool servers following MCP specification
- Dynamic tool discovery and registration
- Secure communication through MCP protocol

### 6.4. Tool Registration and Discovery

Tools are registered in the team configuration and made available to agents based on their role:

```yaml
tools:
  - name: "web_search"
    type: "builtin"
    config: {}
  - name: "custom_analyzer"
    type: "custom"
    path: "./tools/analyzer.py"
    function: "analyze_code"
  - name: "external_api"
    type: "mcp"
    server_url: "http://localhost:8080/mcp"
  - name: "approval_gateway"
    type: "hitl"
    config:
      timeout: 3600
      escalation_policy: "manager"
```

## 7. Memory-Enhanced Collaboration

**(Req #20)** Advanced memory systems enhance agent collaboration:

### 7.1. Shared Memory

- Cross-agent memory sharing for consistent context
- Collaborative knowledge building across multiple tasks
- Shared artifact and decision history

### 7.2. Memory-Driven Handoffs

- Handoff decisions based on historical performance data
- Context-aware agent selection using memory insights
- Learning from previous collaboration patterns

### 7.3. Memory Tools

**Memory Management Tools:**

- `store_memory(key: str, value: Any, scope: str, ttl: Optional[int])`
- `retrieve_memory(key: str, scope: str)`

## 8. LLM-Agnostic Tool Use

**(Req #15, #17)** The framework assumes LLMs do not support native function calling, with DeepSeek models preferred:

### 8.1. Tool Use Prompt Format

The Brain formats available tools in the system prompt:

```
Available Tools:
- handoff(destination_agent: str, reason: str, context: Optional[Dict]): Transfer control to another agent
- web_search(query: str): Search the web for information
- create_artifact(path: str, content: str): Create a file in the workspace
- request_approval(action: str, context: Dict, timeout: int): Request human approval

To use a tool, respond with:
TOOL_CALL: {"tool_name": "tool_name", "args": {"param": "value"}}
```

### 8.2. DeepSeek Optimization

**(Req #17)** Special optimizations for DeepSeek models:

- Prompt templates optimized for DeepSeek's reasoning capabilities
- Context formatting that leverages DeepSeek's strengths
- Tool use patterns that align with DeepSeek's output format preferences

### 8.3. Tool Call Parsing

The Brain parses LLM responses to extract tool calls:

1. Identifies `TOOL_CALL:` markers in the response
2. Parses JSON tool call specifications
3. Validates tool names and parameters
4. Creates `ToolCallPart` objects for the `TaskStep`

### 8.4. Error Handling

When tool calls fail:

- Invalid JSON: Agent receives error message and can retry
- Unknown tool: Agent is informed of available tools
- Parameter errors: Detailed validation errors are provided
- **(Req #24)** Automatic retry with exponential backoff for transient failures

## 9. Step-Through Execution Integration

**(Req #13, #19)** The collaboration model supports step-through execution:

### 9.1. Execution Modes

- **Continuous**: Normal execution without pauses
- **Step**: Pause after each agent turn, wait for user approval
- **Breakpoint**: Pause at specific conditions (tool calls, handoffs, errors)
- **HITL**: Human-in-the-loop intervention points for approval, review, or redirection

### 9.2. User Intervention Points

During paused execution, users can:

- Inspect current task state and history
- Modify the execution plan
- Inject new instructions or context
- Override the next agent selection
- Terminate or restart the task
- Modify team composition or agent assignments

### 9.3. State Preservation

All execution state is preserved in the Task Workspace:

- Current active agent
- Execution mode settings
- Breakpoint conditions
- User intervention history
- Collaboration pattern state
- Memory snapshots

## 10. Cross-Framework Compatibility

**(Req #22)** The collaboration model provides compatibility with existing frameworks:

### 10.1. Framework Translation

- **LangChain**: Maps chains to handoff sequences
- **AutoGen**: Translates group chat patterns to parallel execution
- **CrewAI**: Converts crew structures to flat team configurations

### 10.2. Migration Tools

**Framework Migration Tools:**

- `import_langchain_chain(chain_config: str)`
- `import_autogen_group(group_config: str)`
- `import_crewai_crew(crew_config: str)`

## 11. Next Steps

This document defines the core collaboration logic and tool integration. The final design document, **`03-data-and-events.md`**, will specify the detailed schemas for all data structures (like `TaskStep` and its `Part`s) and the end-to-end eventing and streaming mechanism.
