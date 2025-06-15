# 02: Collaboration & Planning Model

This document specifies the dynamic aspects of the Roboco framework: how agents collaborate to achieve a goal and how that work is planned and tracked. It builds on the components defined in `01-architecture.md`.

## 1. The Execution Plan: `plan.json`

A robust execution plan is the key to successfully completing complex, multi-step tasks. The framework elevates the plan to a first-class, structured artifact.

- **(Req #18)** At the start of a task, a `plan.json` file is created in the `Task Workspace`.
- This file is a structured list of tasks, not a simple markdown file. This allows agents to interact with it programmatically.

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
      "metadata": {
        "completed_at": "2023-10-27T10:00:00Z"
      }
    },
    {
      "task_id": "task_002",
      "description": "Write the main application logic in app.py.",
      "status": "in_progress",
      "metadata": {
        "started_at": "2023-10-27T10:05:00Z"
      }
    },
    {
      "task_id": "task_003",
      "description": "Create unit tests for app.py.",
      "status": "pending",
      "metadata": {}
    }
  ]
}
```

### 1.2. Plan Interaction Tools

Agents will be provided with built-in tools to manage the plan, for example:

- `plan_add_task(description: str)`: Adds a new task to the plan with `pending` status.
- `plan_update_task(task_id: str, status: str, metadata: dict)`: Updates the status and metadata of an existing task.
- `plan_read()`: Returns the full content of `plan.json`.

## 2. The Collaboration Model: Handoffs

The framework uses **Handoffs** to manage the flow of control between agents, a concept inspired by the OpenAI Agents SDK. A handoff is a specific type of tool call that signals the `Orchestrator` to switch the active agent.

- **(Req #4)** Handoffs enable dynamic, intelligent routing that can be determined by the agent at runtime based on the task's progress.

### 2.1. The `handoff` Tool

A built-in tool named `handoff` will be available to all agents.

- **Signature:** `handoff(destination_agent: str, reason: str)`
- When an agent calls this tool, it is signaling that its work for the current turn is complete and that the specified `destination_agent` should act next.

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
          "reason": "Code implementation is complete, ready for testing."
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
3.  **Switch Context:** It sets the `active_agent` to the `destination_agent`.
4.  **Continue Loop:** It proceeds with the main execution loop, now preparing to invoke the new active agent in the next turn.

This model allows for powerful and flexible workflows. For example, a `tester` agent could examine the results of a test run and decide to either `handoff` back to the `coder` (if tests fail) or `handoff` to a `deployer` agent (if tests pass).

## 3. Next Steps

This document defines the core collaboration logic. The final design document, **`03-data-and-events.md`**, will specify the detailed schemas for all data structures (like `TaskStep` and its `Part`s) and the end-to-end eventing and streaming mechanism.
