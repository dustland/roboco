# Quickstart

This guide will walk you through running your first AgentX applications, from a simple, single-agent chat to a more complex multi-agent team.

## Prerequisites

Before you begin, make sure you have AgentX installed and have configured your LLM API keys as environment variables (e.g., `DEEPSEEK_API_KEY`).

## Example 1: Simple Chat (Single Agent)

This example demonstrates the simplest use case: a direct conversation with a single, tool-equipped AI assistant. It uses the `start_task` and `task.step()` functions for an interactive, turn-by-turn conversation.

### 1. The Code (`examples/simple_chat/main.py`)

This Python script sets up an interactive chat loop.

```python
#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from agentx import start_task

async def main():
    print("🤖 AgentX Chat (type 'quit' to exit)\\n")
    task = start_task("hi")
    user_input = None

    while not task.is_complete:
        print("🤖 Assistant: ", end="", flush=True)

        async for chunk in task.step(user_input=user_input, stream=True):
            if chunk.get("type") == "content":
                print(chunk.get("content", ""), end="", flush=True)

        if not task.is_complete:
            user_input = input("👤 You: ").strip()

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. The Configuration (`examples/simple_chat/team.yaml`)

This YAML file defines the "team," which in this case is just a single agent. It defines the agent's prompt, gives it a web search tool, and configures the LLM.

```yaml
name: "simple_chat"
description: "A simple chat example with user, assistant, search, and memory"

agents:
  - name: "assistant"
    description: "Helpful AI assistant with search capabilities"
    prompt_template: "prompts/assistant.md"
    tools: ["web_search"]
    llm_config:
      provider: "deepseek"
      model: "deepseek-chat"

tools:
  - name: "web_search"
    type: "builtin"
```

### 3. Running the Example

Navigate to the `examples/simple_chat` directory and run the script:

```bash
cd examples/simple_chat
python main.py
```

You can now have an interactive conversation with the assistant.

---

## Example 2: Simple Team (Multi-Agent Collaboration)

This example showcases AgentX's multi-agent capabilities. A `Writer` agent drafts an article, and then a `Reviewer` agent provides feedback. The handoff between them is managed automatically by the `TaskExecutor` based on natural language conditions. It uses the "fire-and-forget" `execute_task` function.

### 1. The Code (`examples/simple_team/main.py`)

This script starts a task with a single prompt and streams the entire multi-agent collaboration to the console.

```python
#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from agentx import execute_task

async def main():
    config_path = str(Path(__file__).parent / "config" / "team.yaml")
    prompt = "Write a short article about remote work benefits."

    async for update in execute_task(prompt, config_path, stream=True):
        update_type = update.get("type")

        if update_type == "content":
            print(update["content"], end="", flush=True)
        elif update_type == "handoff":
            print(f"\\n\\n🔄 HANDOFF: {update['from_agent']} → {update['to_agent']}\\n")

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. The Configuration (`examples/simple_team/config/team.yaml`)

This configuration defines the two agents (`writer` and `reviewer`) and, most importantly, the `handoffs` rules that govern their collaboration.

```yaml
name: "WriterReviewerTeam"
agents:
  - name: writer
    description: "Professional content writer for creating high-quality articles"
    prompt_template: "prompts/writer.md"
    llm_config:
      model: deepseek/deepseek-chat

  - name: reviewer
    description: "Quality assurance specialist for reviewing and improving content"
    prompt_template: "prompts/reviewer.md"
    llm_config:
      model: deepseek/deepseek-chat

# Handoffs using natural language conditions
handoffs:
  - from_agent: "writer"
    to_agent: "reviewer"
    condition: "draft is complete and ready for review"

  - from_agent: "reviewer"
    to_agent: "writer"
    condition: "feedback has been provided and revisions are needed"
```

### 3. Running the Example

Navigate to the `examples/simple_team` directory and run the script:

```bash
cd examples/simple_team
python main.py
```

You will see the `Writer` generate a draft, followed by a `HANDOFF` message, and then the `Reviewer` providing its feedback.
