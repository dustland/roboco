# Roboco Framework: Implementation Plan & Requirements Checklist

This document tracks the implementation progress against the authoritative requirements.

- [ ] **1. File-Based Configuration:** The entire multi-agent team structure and collaboration workflow are defined in a static `team.yaml` file. The framework will provide robust loading and validation for this configuration.

- [ ] **2. Central Orchestrator & User Entrypoint:** A central `Orchestrator` serves as the primary entry point and controller for all tasks. It is responsible for initializing the team from a config file, accepting the initial user message, and streaming all intermediate and final results back to the client.

- [ ] **3. Agent Internals (Brain & Prompts):** Each agent possesses a "Brain" (LLM Gateway) to manage LLM interactions. The framework **must** support **Jinja2** templates for agent prompts, allowing for dynamic runtime rendering of variables. All configurations (LLM provider, model, prompt path) are loaded from the team config.

- [ ] **4. Handoffs for Agent Collaboration:** The collaboration model is managed via **Handoffs**, a concept inspired by the OpenAI Agents SDK. A handoff is a specialized tool call that an agent makes to transfer control to another agent. The `Orchestrator` intercepts these handoff calls and switches the active agent accordingly, enabling dynamic and intelligent routing.

- [ ] **5. Decoupled Tool Execution:** Agents do not execute tools directly. They generate `ToolCall` messages which are dispatched by the `Orchestrator` to a specialized `ToolExecutorAgent`.

- [ ] **6. Sandboxed Execution Strategy:** For security, the architecture must support a sandboxed execution environment for all untrusted code and commands. While the end-goal is a secure **Daytona** integration, the initial implementation will focus on a local, non-sandboxed executor for trusted, built-in tools. The legacy `autogen` dependency will be removed.

- [ ] **7. Durable and Auditable Workspace:** All conversation context and artifacts for a task are automatically persisted to a file-based `Task Workspace`. The history must be stored in a transparent, text-based format (e.g., JSON Lines). Agents must be provided with tools to query their own workspace history.

- [ ] **8. Flexible LLM Configuration:** `deepseek-chat` is the default LLM, but this can be overridden per-agent in the configuration.

- [ ] **9. Universal Tool Support:** The framework must provide a universal interface for built-in, custom (Python/bash), and MCP-based tools.

- [ ] **10. End-to-End Streaming:** All message passing, including token-by-token LLM responses, must support streaming all the way back to the client via the `Orchestrator`.

- [ ] **11. Multimodal-Ready Message Structure:** The persisted message structure must be inherently capable of supporting multimodal data (e.g., `TextPart`, `ToolCallPart`, `ArtifactPart`).

- [ ] **12. Step-Through Execution & Debugging:** The `Orchestrator` must support a "step" mode, allowing a user to inspect the state and intervene at each turn.

- [ ] **13. Deployment Model Enablement:** The framework's components must be designed to enable developers to easily build applications on top of it, such as single-run CLI tools or long-running, concurrent services. The framework may provide a reference `roboco` CLI for convenience.

- [ ] **14. LLM-Agnostic Tool Use:** The framework must provide prompting strategies for tool selection on LLMs that lack native function calling, including support for parallel execution requests.

- [ ] **15. Resilient Tool Execution:** The framework must have a defined strategy for handling tool failures. A `ToolResult` indicating failure must be sent back to the calling agent, giving it the opportunity to self-correct.

- [ ] **16. Structured Execution Plan (`plan.json`):** The framework must treat the "Execution Plan" as a first-class, structured JSON artifact within the `Task Workspace`. This `plan.json` file should contain a list of tasks with fields for `task_id`, `description`, `status` (e.g., `pending`, `in_progress`, `completed`), and `metadata`. Agents must have tools to read, add, and update the status of items in this plan, making it the central, shared strategy document for the team.
