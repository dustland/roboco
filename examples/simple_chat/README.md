# Simple Chat Example

This example demonstrates AgentX's clean and minimal configuration structure with:

- **User agent** for human input
- **Assistant agent** with search capabilities and memory
- **Simplified team configuration** (no nested collaboration config)
- **Prompt file loading** system
- **Memory integration** with vector storage
- **Clean AG2-consistent API** with `Team.from_config()`

## Structure

```
simple_chat/
├── team.yaml              # Team configuration (simplified structure)
├── prompts/
│   └── assistant.md       # Assistant prompt file
├── main.py           # Example script
└── README.md             # This file
```

## Configuration Features Demonstrated

### 1. Simplified Team Config

```yaml
# team.yaml
name: "simple_chat"

# Team collaboration settings (directly in team config, no nesting)
speaker_selection_method: "auto"
max_rounds: 10
termination_condition: "TERMINATE"

# Agents with prompt file support
agents:
  - name: "assistant"
    role: "assistant"
    prompt_file: "prompts/assistant.md" # Loaded automatically
    tools: ["web_search"]
    enable_memory: true
```

### 2. Clean AG2-Consistent API

```python
from agentx.core.team import Team

# One-line team creation (like AG2)
team = Team.from_config("examples/simple_chat")

# AG2-consistent conversation API
await team.run("Hello, can you help me research something?")
```

**No more complicated multi-step setup!** Compare to the old way:

```python
# OLD: Complicated multi-step setup
config = load_team_config("team.yaml")
loader = TeamLoader(config_dir)
agents = loader.create_agents(config)
# ... more steps to create team

# NEW: Simple one-line creation
team = Team.from_config("config_dir")
```

## Running the Example

1. **Set environment variable:**

   ```bash
   export DEEPSEEK_API_KEY="your-api-key"
   ```

2. **Run the example:**

   ```bash
   cd examples/simple_chat
   python main.py
   ```

3. **Test the configuration:**
   - The script will create a team using `Team.from_config(".")`
   - Shows all agents and settings
   - Provides interactive chat using `await team.run()`

## What This Example Validates

✅ **Clean API Design:**

- One-line team creation: `Team.from_config()`
- AG2-consistent conversation: `await team.run()`
- No unnecessary intermediate classes

✅ **Simplified Configuration:**

- No nested collaboration config (fields directly in TeamConfig)
- Prompt file loading works automatically
- Memory configuration is properly parsed

✅ **AG2 Consistency:**

- `Team.from_config()` class method pattern
- `run()` method for conversations (not `start_conversation()`)
- Familiar API for AG2 users

## Expected Output

```bash
🤖 Simple Chat Example
==================================================
🚀 Creating team from config...
✅ Team created: simple_chat
👥 Agents: user, assistant
🔢 Max rounds: 10
🔄 Speaker selection: auto

==================================================
✅ Configuration loaded successfully!
🎯 Team ready to run conversations.

💬 Simple Chat Interface:
Type your message to start a conversation
Type 'quit' to exit

👤 You: Hello, can you help me?
🤖 Starting team conversation...
```

## Key Benefits

1. **Simplicity**: One line to create a team
2. **Consistency**: Follows AG2 patterns users expect
3. **Power**: Full configuration support under the hood
4. **Clarity**: No confusing intermediate loader classes

This demonstrates that our configuration system is now as simple as it should be!
