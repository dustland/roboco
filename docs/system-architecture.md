# RoboCo Multi-Agent Framework: Architecture Design

## 1. Introduction

This document outlines the v2 architecture of the RoboCo Multi-Agent Framework, a platform designed to support the development and orchestration of collaborative AI agents. RoboCo aims to provide a flexible, observable, and interruptible environment for complex tasks, with a particular emphasis on robust context management for applications like long-form document generation.

The key design goals influencing this architecture include:

- **Modularity**: Components (agents, tools, context store) should be well-defined and loosely coupled.
- **Extensibility**: The framework should be easily extendable with new agents, tools, and capabilities, and by adding new MCP servers for additional data sources or integrations.
- **Observability**: System operations and agent interactions should be transparent and traceable.
- **Interruptibility**: Users should be able to pause, resume, and redirect ongoing agent processes.
- **Scalable Context Management**: The system must handle large volumes of information exceeding typical LLM context windows.

This document details the core components, interaction patterns, and the specialized sub-systems that enable these goals. All agent interactions with context and external tools are mediated through Model Context Protocol (MCP) servers, which provide a unified and extensible interface for resource access.

## 2. Multi-agent Autonomous System

We use the term "multi-agent system" to refer to a system that consists of multiple agents that collaborate to achieve a common goal. The RoboCo framework is designed to facilitate such collaboration effectively.

Here is a high-level overview of the multi-agent autonomous system in RoboCo:

```mermaid
graph TD
    subgraph User Interaction
        User[Human User] --> UPA[UserProxyAgent]
    end

    subgraph Agent Core
        UPA --> OA["GroupChatManager"]
        OA --> GroupChat{GroupChat}
        GroupChat --> SA1[Specialized Agent 1]
        GroupChat --> SA2[Specialized Agent 2]
        GroupChat --> SAN[...]
        SA1 --> Tools
        SA2 --> Tools
        SAN --> Tools
    end

    subgraph Services & Context
        Tools[Agent Tools] --> MCP[MCP Servers]
        MCP --> Resource1["External Resource 1 (e.g., Web Search)"]
        MCP --> Resource2["External Resource 2 (e.g., Database)"]
        MCP --> FBCM[File-Based Context Management]
        FBCM --> DocStore[(Document Store: outline.json, sections/, metadata.json, _document_summary.json)]
    end

    classDef user fill:#D5F5E3,stroke:#2ECC71,stroke-width:2px;
    classDef agent fill:#D6EAF8,stroke:#3498DB,stroke-width:2px;
    classDef orchestrator fill:#FCF3CF,stroke:#F1C40F,stroke-width:2px;
    classDef group fill:#E8DAEF,stroke:#8E44AD,stroke-width:2px;
    classDef tool fill:#EBDEF0,stroke:#8E44AD,stroke-width:2px;
    classDef mcp fill:#FDEDEC,stroke:#E74C3C,stroke-width:2px;
    classDef context fill:#FEF9E7,stroke:#F39C12,stroke-width:2px;
    classDef resource fill:#E5E7E9,stroke:#808B96,stroke-width:2px;

    class User user;
    class UPA,SA1,SA2,SAN agent;
    class OA orchestrator;
    class GroupChat group;
    class Tools tool;
    class MCP mcp;
    class FBCM,DocStore context;
    class Resource1,Resource2 resource;
```

Key concepts in this system include:

- **`Agent`**: An autonomous unit, typically an LLM-backed entity, responsible for specific tasks or roles within the system (e.g., `PlannerAgent`, `WriterAgent`).
- **`UserProxyAgent`**: An agent that acts as the primary interface between the human user and the agent system.
- **`GroupChatManager`**: Coordinates the activities of other agents, manages conversation flow, and directs the overall task execution.
- **`Specialized Agents`**: Agents designed for particular functions (e.g., research, writing, planning) that contribute to the overall goal.
- **`GroupChat`**: A collaborative environment managed by the `GroupChatManager` where multiple agents can interact.
- **`Tools (via MCP)`**: Capabilities or functions (e.g., file I/O, web search, database access) that agents can invoke to perform actions or retrieve information. These are accessed via the Model Context Protocol (MCP).
- **`Context`**: Shared information and the state of the ongoing task, managed through mechanisms like the File-Based Context Management system.

## 3. Config-based Agents (AutoGen 2 Integration)

The foundation of RoboCo is built upon the `ag2` (AutoGen 2) library, leveraging its robust features for creating and managing conversational AI agents.

- **`Config-based Agents`**: Each agent in RoboCo is an instance of `ConversableAgent` (or a class derived from it). Agents are configured with a specific `system_message` defining their role, capabilities, and personality, along with an `llm_config`. This configuration-driven approach, detailed in [Config-based Design](./config_based_design.md), allows for flexible customization and easy definition of new agent types.
- **`GroupChatManager` for Orchestration**: In RoboCo, orchestration is handled by an `ag2.GroupChatManager`. It manages a `GroupChat` consisting of specialized agents and, potentially, the `UserProxyAgent`. The `GroupChatManager` is responsible for:
  - Receiving initial tasks and subsequent user inputs (often via the `UserProxyAgent`).
  - Determining the overall strategy and sequence of actions required to fulfill the task.
  - Selecting the appropriate specialized agent to speak or act next based on the current task state, conversation history, and predefined agent roles and capabilities.
- **Event-Driven Processing**: RoboCo employs manual iteration over the event stream generated by an agent's `run()` method (particularly the `GroupChatManager`'s `run()` call). Instead of relying on `ag2`'s default console output (`response.process()`), the RoboCo backend iterates event by event. This fine-grained control allows for:
  - **Observability**: Streaming progress updates, agent messages, and tool usage information to user interfaces or logging systems.
  - **State Management**: Tracking the progress of tasks and maintaining system state.
  - **Interruption Points**: Checking for user commands or other external signals between processing individual events, enabling responsive control.
- **User Command Queue**: To handle asynchronous user inputs and ensure interruptibility without blocking agent processing, a dedicated User Command Queue (e.g., `asyncio.Queue`) is utilized.
  - User commands from the UI (e.g., pause, resume, new instructions) are enqueued by the backend.
  - The main agent control loop checks this queue between processing events from the `ag2` event stream.
  - This mechanism allows the system to pause, resume, or redirect the agent workflow dynamically based on user commands.

## 4. File-Based Context Management

To address the limitations of LLM context windows and provide persistent, structured storage for tasks like long-form document generation, RoboCo incorporates a file-based context management sub-system. This system ensures that agents can work with large volumes of information effectively.

- **Rationale**:
  - **Scalability**: Enables agents to work with information volumes far exceeding typical prompt limits.
  - **Persistence**: Provides a persistent workspace for tasks, allowing for resumption and iterative refinement over extended periods.
  - **Structure**: Allows for structured organization of complex information, making it easier for agents to navigate and utilize relevant context.
- **Storage Structure**:
  - Contexts are stored under a configurable base path (defined by `ROBOCO_DATA_PATH`, e.g., `~/roboco_data/contexts/`).
  - Each document or task context has its own dedicated directory: `[document_id]/`.
  - Inside each `[document_id]/` directory, the following components are typically found:
    - `metadata.json`: Stores high-level information about the document or task, such as title, creation date, status, and other custom metadata.
    - `outline.json`: Defines the document's structure, including section order, hierarchy, and potentially section-specific goals, keywords, or instructions for agents.
    - `sections/`: A subdirectory containing the actual content of each section, typically as individual Markdown files (e.g., `01_introduction.md`, `02_main_body.md`).
    - `_document_summary.json`: A special file holding a running summary of key points, arguments, decisions, and data established across the entire document. This aids coherence, reduces redundancy, and helps agents maintain a consistent understanding as the document evolves.
- **Key MCP Tools for Context Interaction**: Agents interact with this file-based context via a set of specialized MCP tools:
  - `initialize_document_context_tool`: Creates the necessary directory structure and initial files for a new document context.
  - `get_document_outline_tool` / `update_document_outline_tool`: Read and modify the `outline.json` file.
  - `read_section_content_tool`: Reads content from section files, supporting chunking by token count to manage large sections.
  - `write_section_content_tool`: Writes or appends content to section files.
  - `list_document_sections_tool`: Lists available sections based on the `outline.json`.
  - `get_document_metadata_tool` / `update_document_metadata_tool`: Read and modify the `metadata.json` file.
  - `get_document_summary_tool` / `update_document_summary_tool`: Read and update the `_document_summary.json` file.
  - `search_document_context_tool`: Performs a keyword-based search across section content within the current document context.
  - `delete_document_context_tool`: Removes an entire document context and its associated files.

## 5. Core Interaction Workflow

A typical task execution in RoboCo follows this general pattern, emphasizing the event-driven nature and interruption handling:

1.  **Initiation**:
    - A user sends a request (e.g., "Write a research paper on AI ethics") via a user interface (e.g., WPS add-in, Streamlit web UI).
    - The RoboCo backend receives this request and typically passes it to the `UserProxyAgent`.
    - The `UserProxyAgent` initiates a chat with the `GroupChatManager`, sending the user's initial request.
    - The `GroupChatManager` starts its execution cycle: `chat_response_iterator = group_chat_manager.run(message=initial_user_request, ...)`.
2.  **Event-Driven Processing (RoboCo Backend Logic)**:
    - The backend iterates through the `chat_response_iterator` event by event: `for event in chat_response_iterator:`.
    - **Observability**: For each event, relevant information (e.g., which agent spoke, the content of the message, tool calls made, current status) is extracted. This information can be streamed to the UI for real-time progress monitoring or logged for later analysis.
    - **State Update**: The internal state tracking the task's progress is updated based on the event.
    - **Interruption Check**: Crucially, before fetching the next event from the iterator, the backend checks the User Command Queue for any pending user inputs.
3.  **Handling Interruptions**:
    - If a command exists in the User Command Queue (e.g., user issues a "Pause" command, or "Focus on section 2 instead"), the backend reacts:
      - It stops iterating the current `chat_response_iterator`, effectively pausing the ongoing agent interaction.
      - It processes the user's command. This might involve sending a new message to the `GroupChatManager` (e.g., conveying new instructions), modifying the task state directly, or triggering other system-level actions.
      - The `GroupChatManager`, upon receiving new input or detecting state changes, adapts its plan or instructs the specialized agents accordingly.
4.  **GroupChat Dynamics within Orchestration**:
    - The `GroupChatManager` manages the flow of conversation and action within the `GroupChat`.
    - It selects the next specialized agent to speak or act based on the overall plan, the current state of the conversation, and the defined capabilities of each agent.
    - Specialized agents perform their tasks, using their registered MCP tools as needed (e.g., accessing the file context, searching the web), and contribute their findings, drafted content, or results back to the group chat.
    - If an agent requires clarification or further input that only the human user can provide, the `GroupChatManager` can direct the conversation towards the `UserProxyAgent` to query the user.
5.  **Task Completion**:
    - The process of event iteration, agent interaction, and potential interruptions continues until the task is completed as defined by the `GroupChatManager`'s logic or a predefined termination condition (e.g., `max_turns` reached, all sections reviewed and approved).
    - The final result or output is then typically relayed to the user via the `UserProxyAgent`.

## 6. Extensibility with Model Context Protocol (MCP)

The **Model Context Protocol (MCP)** is an open standard that defines how AI agents (acting as clients) connect to and interact with external data sources, tools, and services (exposed by MCP servers) via a unified protocol. MCP is central to RoboCo's design, enabling modular, extensible, and secure integration of context and capabilities into agent workflows.

RoboCo leverages and extends MCP to provide a standardized interface for agents to access not only external resources (like web search or databases) but also the internal File-Based Context Management system (document outlines, sections, metadata, summaries).

- **MCP Clients**: These are the AI agents or applications within RoboCo (e.g., those built with `ag2`) that require access to external data, context, or tools to perform their tasks.
- **MCP Servers**: These are dedicated, often lightweight, servers that expose access to specific resources or capabilities through the MCP protocol. Each MCP server implements a standard interface for a particular type of resource (e.g., a server for document context operations, a server for file system access, a server for web search, a server for a specific database or business tool).
- **MCP Registration**: In the RoboCo framework, all tools registered with agents are essentially MCP protocol clients. When an agent decides to use a tool, it communicates with the appropriate MCP server to fulfill its request. This abstraction decouples the agent's logic from the specific implementation of the tool or resource access.

## 7. MCP Design Principles

The adoption of MCP in RoboCo is guided by several key design principles:

- **Modularity**: Each distinct resource, tool, or capability is encapsulated within its own MCP server. This promotes separation of concerns and makes the system easier to manage and update.
- **Extensibility**: Integrating new tools, data sources, or capabilities into RoboCo primarily involves developing a new MCP server for that resource and registering the corresponding client-side tool with the agents. This makes the framework highly extensible.
- **Security & Observability**: Since all external access is mediated through MCP servers, this provides a natural point for implementing security policies (authentication, authorization) and for comprehensive logging and auditing of resource access and tool usage.
- **Uniformity**: Agents interact with all diverse resources (file context, web search, databases, etc.) through the same MCP protocol. This simplifies the agent's reasoning process and the code required for tool integration, as they don't need to handle multiple different APIs or access methods.

The MCP server architecture ensures that agent workflows in RoboCo are robust, maintainable, and future-proof. It makes all context interactions explicit and protocol-driven, enhancing the overall reliability and transparency of the system.

## 8. Scenario: Document Generation

The RoboCo architecture is particularly well-suited for building sophisticated, multi-step document generation services. Here's how the components align in such a scenario:

### Agents

| Agent                | Role                  | Key MCP Tools Used                                                                                                                                  | Function                                                                                                |
| -------------------- | --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| **PlannerAgent**     | Document structuring  | `update_document_outline_tool`                                                                                                                      | Creates detailed document structure in `outline.json`, defining sections, subsections, and their order  |
| **ResearcherAgent**  | Information gathering | `search_web_tool`, `search_document_context_tool`, `write_section_content_tool`                                                                     | Gathers external information and existing context; saves findings to research notes or content sections |
| **WriterAgent**      | Content creation      | `get_document_outline_tool`, `read_section_content_tool`, `write_section_content_tool`, `get_document_summary_tool`, `update_document_summary_tool` | Drafts section content based on outline and research; maintains document coherence                      |
| **ReviewerAgent**    | Quality control       | `read_section_content_tool`, `get_document_outline_tool`, `get_document_summary_tool`                                                               | Reviews for accuracy, coherence, style, and adherence to outline; suggests revisions                    |
| **GroupChatManager** | Workflow management   | N/A (coordinates other agents)                                                                                                                      | Sequences tasks between agents; ensures dependencies are met; routes information                        |
| **UserProxyAgent**   | User interface        | N/A (interfaces with user)                                                                                                                          | Presents drafts for review; collects feedback; relays to GroupChatManager                               |

### MCP Tools (File Context Focused)

| Tool                                                           | Function                                               | Data Managed               |
| -------------------------------------------------------------- | ------------------------------------------------------ | -------------------------- |
| `initialize_document_context_tool`                             | Sets up workspace for a new document                   | Initial folder structure   |
| `get_document_outline_tool` / `update_document_outline_tool`   | Retrieve or modify document structure                  | `outline.json`             |
| `read_section_content_tool`                                    | Reads content from section files with chunking support | Section content files      |
| `write_section_content_tool`                                   | Writes content to section files (overwrite or append)  | Section content files      |
| `list_document_sections_tool`                                  | Lists sections based on the outline                    | N/A (reads `outline.json`) |
| `get_document_metadata_tool` / `update_document_metadata_tool` | Retrieve or modify document metadata                   | `metadata.json`            |
| `get_document_summary_tool` / `update_document_summary_tool`   | Retrieve or modify document summary                    | `_document_summary.json`   |
| `search_document_context_tool`                                 | Performs keyword search within document sections       | N/A (searches all files)   |
| `delete_document_context_tool`                                 | Archives or removes a document context                 | All document files         |

### Key Workflow: Document Generation Example

The document generation workflow can be broken down into two main parts: initial planning/research and content creation/review. The following diagrams illustrate this process:

#### Part 1: Planning and Research

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UPA as UserProxyAgent
    participant OA as GroupChatManager
    participant PA as PlannerAgent
    participant ResA as ResearcherAgent
    participant Tools as MCP Tools

    User->>UPA: Generate document on AI Ethics
    UPA->>OA: Forward request

    Note over OA,PA: PLANNING PHASE
    OA->>PA: Plan document structure
    PA->>Tools: update_document_outline_tool
    PA-->>OA: Outline created

    Note over OA,ResA: RESEARCH PHASE
    OA->>ResA: Research Key Issues section
    ResA->>Tools: search_document_context_tool
    ResA->>Tools: search_web_tool
    ResA->>Tools: write_section_content_tool
    ResA-->>OA: Research complete
```

#### Part 2: Writing and Review

```mermaid
sequenceDiagram
    autonumber
    participant OA as GroupChatManager
    participant WA as WriterAgent
    participant RevA as ReviewerAgent
    participant Tools as MCP Tools
    participant UPA as UserProxyAgent
    actor User

    Note over OA,WA: WRITING PHASE
    OA->>WA: Draft Key Issues section
    WA->>Tools: get_document_outline_tool
    WA->>Tools: read_section_content_tool
    WA->>Tools: write_section_content_tool
    WA->>Tools: update_document_summary_tool
    WA-->>OA: Section drafted

    Note over OA,RevA: REVIEW PHASE
    OA->>RevA: Review drafted section
    RevA->>Tools: read_section_content_tool
    RevA->>Tools: get_document_outline_tool
    RevA->>Tools: get_document_summary_tool
    RevA-->>OA: Feedback/Approval

    Note right of OA: Process iterates for all sections<br/>User can provide feedback via UPA

    OA-->>UPA: Document complete
    UPA-->>User: Present final document
```

This workflow is iterative. For instance, the `ReviewerAgent` might request revisions, leading the `GroupChatManager` to re-engage the `WriterAgent`. The `UserProxyAgent` can also inject user feedback at various stages.

## 9. Deployment and Maintenance

In a typical RoboCo deployment:

- **MCP Servers**: Each MCP server (for file context, web search, etc.) is deployed as an independent service. These can be containerized (e.g., using Docker) and managed by an orchestrator like Kubernetes for scalability and resilience, or run as simple processes depending on the scale.
- **RoboCo Backend**: The core RoboCo application, which includes the agent definitions, orchestration logic (including the `GroupChatManager` and `UserProxyAgent`), and the event loop processing, is deployed as a central service. This backend communicates with the various MCP servers.
- **Agents**: The agents themselves are part of the RoboCo backend's execution environment. They are instantiated and run as processes or threads within the backend application.
- **Configuration**: Agent configurations, system messages, LLM API keys, and `ROBOCO_DATA_PATH` are managed through configuration files or environment variables.

Maintenance involves updating individual MCP servers (if their underlying tools or resources change), updating the RoboCo backend with new agent logic or orchestration strategies, and managing the LLM configurations and dependencies.

## 10. Conclusion

The RoboCo v2 architecture, built on `ag2` and significantly enhanced with a robust Model Context Protocol (MCP) tool system and a dedicated file-based context management sub-system, provides a powerful and flexible platform for developing sophisticated multi-agent applications. Its core emphasis on modularity, extensibility, observability, interruptibility, and scalable context handling makes it particularly suitable for complex, iterative tasks such as automated document generation, research synthesis, and other knowledge-intensive workflows.

By clearly defining agent roles, providing them with standardized access to tools and context via MCP, and orchestrating their collaboration effectively through `ag2`'s `GroupChatManager` and an event-driven backend, RoboCo enables the creation of advanced AI-driven solutions that can tackle challenges beyond the scope of single-agent systems.
