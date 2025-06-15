# Roboco Framework: Core Design Principles

1.  **File-Based Configuration:** The entire multi-agent team structure and collaboration workflow are defined in and loaded from static, file-based configurations (e.g., `team.yaml`). These configurations serve as the complete, declarative definition of a team.

2.  **User-Facing Agent:** The primary entry point for any user interaction is a `UserAgent`. This agent is responsible for accepting initial user messages and for delivering all intermediate and final results from the collaboration, supporting both streaming and non-streaming modes of communication.

3.  **Central Orchestrator:** The `UserAgent` communicates with a central `Orchestrator`. The `Orchestrator` holds the `Team` data object, which represents the full state of the collaboration, including all agents. The `Team` object is constructed from the file-based configuration.

4.  **Agent Internals (Brain & Prompts):** Each agent possesses a "Brain" sub-component that acts as a dedicated LLM gateway. The Brain manages LLM configuration (provider, model, parameters), which is loaded from the team config file. Agent prompts are maintained in separate files and processed as Jinja2 templates to allow for dynamic variable rendering at runtime.

5.  **Orchestrator's Role:** The `Orchestrator`'s responsibilities are strictly limited to managing the _flow_ of the collaboration, not its content. Its sole duties are to determine the next agent to speak and to terminate the collaboration based on predefined conditions, such as exceeding a maximum number of rounds.

6.  **Decoupled Tool Execution:** Agents do not execute tools directly. When an agent needs to use a tool, it generates a structured `ToolCall` message. This message is sent to a specialized `ToolExecutorAgent` which acts as a worker to execute the requested tool, code, or shell command.

7.  **Sandboxed Execution Environment:** The `ToolExecutorAgent` can be the `UserAgent` itself or a dedicated virtual agent managed by the `Orchestrator`. For security, all tool and code execution **must** occur within a sandboxed environment. The mandatory and sole choice for this sandbox is **Daytona**, following the model of production-grade systems like Suna.

8.  **Durable and Auditable Context:** All conversation context (messages) and generated artifacts (files, images, etc.) are automatically persisted to the file system. The context history must be stored in a transparent, text-based format (e.g., JSON Lines) to be fully auditable. Agents must be equipped with mechanisms to search and retrieve data from this persisted context.

9.  **Flexible LLM Configuration:** The default LLM for all components is `deepseek-chat`. However, the configuration system must allow the `Orchestrator` and each individual agent to override this default and specify its own unique LLM provider and model.

10. **Universal Tool Support:** Agents must support a variety of tools through a universal interface. This includes: (a) built-in tools provided by the framework, (b) extended custom tools (user-provided Python functions or shell scripts), and (c) extensibility via the MCP (Metaprotocol for Cognitive Processors) protocol.

11. **End-to-End Streaming:** All message passing between the `UserAgent`, `Orchestrator`, and individual agents must support streaming. This ensures that the client connected to the `UserAgent` can receive real-time, token-by-token progress updates from any part of the system.

12. **Extensible Routing Patterns:** The default orchestration logic is `AutoPattern`, where the `Orchestrator` always decides the next speaker. While this is the only pattern that needs to be supported initially, the design must remain open to allow for the future addition of custom routing patterns.

13. **Multimodal-Ready Message Structure:** The conversation history must be persisted using a structured message format that is inherently ready to support multimodal data (text, images, code snippets, etc.), not just plain text strings.

14. **Step-Through Execution and Debugging:** The `Orchestrator` must support a "step" or "paused" execution mode. This allows a user to inspect the state of the task at each turn and provides an opportunity to interject with new messages or instructions to adjust the ongoing execution.

15. **Backend First, UI Friendly:** The framework is a backend-only system and must not contain any UI-specific terminology or components. However, its APIs and data structures (especially regarding streaming and observability) must be designed with the explicit goal of enabling a smooth, responsive, and informative client-side UI.

16. **LLM-Agnostic Tool Use:** The framework must assume that the underlying LLMs do not support native function/tool calling. The agent's "Brain" is responsible for formatting the prompt in a way that allows a standard chat model to reason about, select, and specify the parameters for tools. This process must also support requesting the parallel execution of multiple tools for performance.

17. **Flexible Deployment Models:** The framework must be packaged and designed to run in two distinct modes: (a) as a single-use command-line tool that executes one task and then exits, and (b) as a long-running online service capable of managing multiple, concurrent tasks in isolation.
