# Design Doc: Validation Scenarios

This document validates the proposed architecture against two complex, real-world scenarios. The goal is to ensure the design is robust and flexible enough to handle more than just simple Q&A tasks.

## Scenario 1: Writing an Academic Paper

**Goal**: A user wants the agent team to write a short academic paper on the "Impact of Large Language Models on Software Development Productivity."

**Team Configuration (`team.json`)**:

- **Agents**:
  - `researcher`: Finds academic papers and articles. Tools: `web_search`, `memory_search`.
  - `writer`: Drafts sections of the paper based on research. Tools: `file_write`, `file_read`, `memory_search`.
  - `critic`: Reviews drafted sections for clarity, accuracy, and style. Tools: `file_read`.
  - `user_proxy`: The user's entry point for providing feedback and direction.
- **Collaboration Model**: `graph`
  - `user_proxy` -> `researcher`
  - `researcher` -> `writer`
  - `writer` -> `critic`
  - `critic` -> `writer` (for revisions) OR `user_proxy` (for review)

### Architectural Stress Test:

1.  **Initial Prompt (User -> `user_proxy`)**: "Please write a 3-page paper on the impact of LLMs on developer productivity, including a literature review, methodology, and conclusion."
2.  **Orchestrator/Router**: The `Orchestrator` starts the task. The `Router` selects the `researcher` agent.
3.  **Tool Use (`researcher`)**: The `researcher` agent uses `web_search` multiple times to find relevant papers. The results are large text blobs.
    - **Data/Memory Validation**: Instead of stuffing these into the history, the `researcher` uses a `file_write` tool (or similar) to save them as artifacts. The `TaskStep` history only contains `ArtifactPart` references (e.g., `uri: "file://.../artifacts/paper1.txt"`), keeping the history lean.
4.  **Handoff (`researcher` -> `writer`)**: The `Router` sees the research is done and hands off to the `writer`.
5.  **Active Memory (`writer`)**: The `writer` doesn't have the full text of the research in its context. It uses `memory_search("literature review")` to find the `ArtifactPart` references from the researcher's turn and then uses `artifact_read(uri)` to get the content of the papers it needs to write the first section. It saves its draft as a new artifact.
    - **Data/Memory Validation**: This demonstrates the "active memory" pattern. The agent pulls information as needed, overcoming context window limits.
6.  **Review Loop (`writer` <-> `critic`)**: The `writer` finishes a draft. The `Router` sends it to the `critic`. The `critic` reads the artifact and provides feedback as a `TextPart`. The `Router` sends control back to the `writer` for revisions. This loop continues.
    - **Collaboration Validation**: The `graph` collaboration model correctly manages the iterative workflow.
7.  **User Interruption**: The user reviews a draft and wants to change the focus. They interrupt the process.
    - **Orchestrator Validation**: The `Orchestrator` handles the interruption, adds the user's feedback to the history, and the `Router` can then use this new information to re-route the task, perhaps back to the `researcher` to find new sources.

## Scenario 2: Generating a Software Project

**Goal**: A user wants to bootstrap a simple Python web application.

**Team Configuration (`team.json`)**:

- **Agents**:
  - `planner`: Breaks down the user request into a file structure and implementation plan.
  - `coder`: Writes Python code for individual files. Tools: `file_write`.
  - `tester`: Writes unit tests for the code. Tools: `file_read`, `run_tests`.
- **Collaboration Model**: `sequential` (`planner` -> `coder` -> `tester`)

### Architectural Stress Test:

1.  **Initial Prompt**: "Create a Flask web app with a single endpoint `/hello` that returns 'Hello, World!' and include a unit test."
2.  **Planning (`planner`)**: The `planner` agent receives the prompt. It generates a plan as a `TextPart`, outlining the files to be created (`app.py`, `test_app.py`, `requirements.txt`).
    - **TaskStep Validation**: The plan is a structured part of the history, visible to all subsequent agents.
3.  **Code Generation (`coder`)**: The `coder` agent sees the plan. It executes multiple `file_write` tool calls to create `app.py` and `requirements.txt`.
    - **Tool/Artifact Validation**: The generated code files are stored in the `Task Workspace`. This is a clear, auditable result of the task.
4.  **Testing (`tester`)**: The `tester` agent's turn. It uses `file_read` to see the code in `app.py` and then `file_write` to create `test_app.py`. Finally, it uses a hypothetical `run_tests` tool, which executes `pytest` in a sandboxed environment. The output of the test run is returned as a `ToolResultPart`.
    - **Observability Validation**: The `ExecutionEvent`s for the tool calls (`run_tests`) and the resulting `ToolResultPart` provide a clear, structured record of whether the project passed its tests. This is invaluable for debugging.
5.  **Final Output**: The task completes. The user is left with a fully functional, self-contained `Task Workspace` directory containing the generated project.

These scenarios confirm that the proposed architecture (Orchestrator, Router, Task Workspace, Active Memory, Structured History) is capable of handling complex, multi-step, and stateful tasks that go far beyond simple conversational AI.
