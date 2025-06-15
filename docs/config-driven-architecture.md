# Design Doc: Config-Driven Architecture

This document specifies the configuration schema for defining a `Team` and its agents. The goal is to make the entire system configurable through a single, declarative `team.json` file, enabling the **Agentok Studio** to act as a visual builder for this configuration.

## 1. The `team.json` Schema

The `team.json` file is the central configuration file. It defines everything about the team: the agents, the tools they can use, and how they collaborate.

### Top-Level Structure

```json
{
  "name": "Academic Research Team",
  "description": "A team designed to write academic papers.",
  "collaboration_model": {
    "type": "graph",
    "initial_agent": "researcher",
    "routing_graph": {
      "researcher": ["writer"],
      "writer": ["critic", "researcher"],
      "critic": ["writer"]
    }
  },
  "agents": [],
  "tools": []
}
```

- **`name`**: A human-readable name for the team.
- **`description`**: A brief explanation of the team's purpose.
- **`collaboration_model`**: Defines how the `Router` selects the next agent.
  - **`type`**: The routing strategy (e.g., `graph`, `sequential`, `manual`).
  - **`...`**: Additional parameters specific to the type (e.g., `initial_agent` and `routing_graph` for the `graph` type).
- **`agents`**: An array of `AgentConfig` objects.
- **`tools`**: An array of `ToolConfig` objects.

### 2. `AgentConfig` Schema

This object defines a single agent within the team.

```json
{
  "name": "researcher",
  "description": "An agent that performs web searches and synthesizes information.",
  "model": "claude-3-opus-20240229",
  "prompt": "You are a world-class researcher. Your goal is to find and summarize the most relevant information on a given topic.",
  "prompt_file": "prompts/researcher_prompt.md",
  "tools": ["web_search", "file_read"]
}
```

- **`name`**: A unique identifier for the agent within the team.
- **`description`**: A high-level description of the agent's role, used for both documentation and potentially by other agents or the `Router`.
- **`model`**: The specific LLM to be used for this agent (e.g., a LiteLLM model string).
- **`prompt`**: An inline system prompt for the agent.
- **`prompt_file`**: A path (relative to the `team.json` file) to a file containing the system prompt. If both `prompt` and `prompt_file` are provided, the `prompt_file` takes precedence.
- **`tools`**: An array of strings, where each string is the `name` of a tool defined in the top-level `tools` array. This specifies the subset of tools available to this agent.

### 3. `ToolConfig` Schema

This object defines a tool that can be made available to agents.

```json
{
  "name": "web_search",
  "description": "A tool to search the web for information.",
  "class": "roboco.tools.WebSearchTool",
  "args": {
    "api_key_env_var": "SERPAPI_API_KEY"
  }
}
```

- **`name`**: A unique identifier for the tool. This is the name used in an agent's `tools` array.
- **`description`**: A natural language description of what the tool does. This is critical, as it will be injected into the agent's prompt to help it decide when to use the tool.
- **`class`**: The fully qualified Python class name for the tool's implementation (e.g., `module.submodule.ClassName`). The framework will use this to dynamically import and instantiate the tool.
- **`args`**: An optional object of key-value pairs to be passed to the tool's constructor during instantiation. This allows for configuring tools with API keys, specific settings, etc.

## 4. Loading Logic: `Team.from_config()`

The framework will provide a class method, `Team.from_config(config_path: str) -> Team`, to load a `team.json` file and construct a `Team` object.

This process involves:

1.  **Reading and Validating**: Loading the JSON file and validating it against Pydantic models that mirror the schema defined above.
2.  **Tool Instantiation**: Iterating through the `tools` array, dynamically importing the specified `class`, and instantiating it with the provided `args`.
3.  **Agent Instantiation**: Iterating through the `agents` array and creating `Agent` objects. For each agent, the referenced tools (by name) are looked up from the already instantiated tool objects.
4.  **Team Creation**: Assembling the instantiated agents and tools into a final `Team` object, ready to be used by the `Orchestrator`.
