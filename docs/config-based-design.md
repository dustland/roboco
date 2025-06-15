# Roboco: Core Data & Streaming Model

This document specifies the core data structures and streaming workflow for the Roboco framework. It is a language-agnostic design focused on a streaming-first, production-ready architecture.

## 1. Core Principles

1.  **Streaming-First**: All interactions, including text generation and tool usage, should be consumable as a stream. This enables real-time, token-by-token UI updates, which is essential for a production-grade user experience.
2.  **Rich Data Payloads**: A `TaskStep` is not just text. It is a structured object that can carry complex data, including multiple content types (text, tool calls, tool results) within a single message. This avoids assumptions about display logic and supports advanced use cases.
3.  **Explicit Tool Steps**: Tool usage is a first-class citizen in the execution history. Tool calls and their corresponding results are represented as explicit, structured `parts` within a `TaskStep`, making the reasoning process transparent and easy to handle for developers.

## 2. Core Data Structures

### 2.1. TaskStep

The `TaskStep` is the fundamental unit of the execution history. It is a structured object, not just a string of text.

| Field        | Type              | Required | Description                                                     |
| :----------- | :---------------- | :------- | :-------------------------------------------------------------- |
| `id`         | `string`          | Yes      | A unique identifier for the step.                               |
| `parent_id`  | `string`          | No       | The ID of the parent step, for hierarchical execution.          |
| `agent_name` | `string`          | Yes      | The name of the agent that generated the step.                  |
| `parts`      | `array[StepPart]` | Yes      | The payload of the step, as a collection of rich content parts. |
| `created_at` | `datetime`        | Yes      | The time the step was created. Defaults to now.                 |
| `metadata`   | `object`          | No       | A key-value object for arbitrary metadata.                      |

### 2.2. Step Parts

A `TaskStep`'s `parts` field is an array of `StepPart` objects. This allows a single step to carry multiple types of information.

**Types of Step Parts:**

1.  **`text`**: A part containing a standard text string.

    - `type`: "text"
    - `text`: The string content.

2.  **`tool_call`**: A part representing a request from the AI to execute one or more tools.

    - `type`: "tool_call"
    - `tool_call`: A `ToolCall` object.

3.  **`tool_result`**: A part representing the results from one or more tool executions.
    - `type`: "tool_result"
    - `tool_result`: A `ToolResult` object.

### 2.3. Tool Call & Result

These structures define the request and response shapes for tool interactions, and are contained within the `tool_call` and `tool_result` parts.

**`ToolCall` Schema:**

| Field       | Type     | Required | Description                                           |
| :---------- | :------- | :------- | :---------------------------------------------------- |
| `id`        | `string` | Yes      | A unique ID for this specific invocation request.     |
| `tool_name` | `string` | Yes      | The name of the tool to execute (e.g., `web_search`). |
| `args`      | `object` | Yes      | A key-value object of arguments for the tool.         |

**`ToolResult` Schema:**

| Field          | Type     | Required | Description                                                                            |
| :------------- | :------- | :------- | :------------------------------------------------------------------------------------- |
| `tool_call_id` | `string` | Yes      | The ID of the `ToolCall` this is a result for.                                         |
| `result`       | `any`    | Yes      | The output from the tool. This can be a string, object, array, or any other data type. |
| `is_error`     | `bool`   | No       | Indicates if the result is an error. Defaults to `false`.                              |

## 3. Core Workflow: Streaming Interaction

The workflow defined in `collaboration-with-tools.md` provides the canonical sequence diagram and steps for the framework's streaming interaction model. This section serves as a high-level conceptual reference.

When a client runs a task via the `Orchestrator`, they can iterate over a generator that yields structured "chunks" of data as they become available. The client's responsibility is to interpret these chunks to build the UI and conversation state in real-time.

**Conceptual Stream Chunk Types:**

| Chunk Type         | Data Payload     | Description                                                                                     |
| :----------------- | :--------------- | :---------------------------------------------------------------------------------------------- |
| `text_part_delta`  | `string`         | A token-by-token piece of a `TextPart` response.                                                |
| `tool_call_part`   | `ToolCallPart`   | A complete `ToolCallPart` object, sent atomically.                                              |
| `tool_result_part` | `ToolResultPart` | A complete `ToolResultPart` object, sent atomically.                                            |
| `step_final`       | `TaskStep`       | The fully-formed `TaskStep` object at the end of a turn (e.g., after all text deltas are sent). |

This design provides a clear, conceptual foundation for the data models and streaming patterns used in the Roboco framework.

```

```
