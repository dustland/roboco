# Configuration-Based Design

Simple configuration system for Roboco teams. Each task gets one YAML team config file that references prompt files.

## Core Concept

```
task_name/
├── team.yaml          # Single team configuration
└── prompts/           # Prompt files referenced by team.yaml
    ├── researcher.md
    ├── writer.md
    └── coordinator.md
```

## Team Configuration

### Basic Structure

```yaml
# research_task/team.yaml
name: "research_team"

# Global LLM provider settings (or use .env)
llm_provider:
  base_url: "https://api.deepseek.com"
  api_key: "${DEEPSEEK_API_KEY}"
  model: "deepseek-chat"

agents:
  - name: "researcher"
    role: "assistant"
    prompt_file: "prompts/researcher.md"
    llm_config:
      temperature: 0.3 # Lower for factual research
      max_tokens: 4000
    tools: ["search", "web_extraction", "memory"]

  - name: "writer"
    role: "assistant"
    prompt_file: "prompts/writer.md"
    llm_config:
      temperature: 0.8 # Higher for creative writing
      max_tokens: 6000
    tools: ["memory"]

  - name: "coordinator"
    role: "system"
    prompt_file: "prompts/coordinator.md"
    llm_config: null # System agents may not need LLM
    tools: []

# Team collaboration controls (essential to avoid infinite loops)
collaboration:
  speaker_selection_method: "auto" # auto, round_robin, manual
  max_rounds: 10 # Hard limit to prevent infinite loops
  termination_condition: "TERMINATE" # What message ends the conversation

# Tool configurations
tools:
  search:
    provider: "serpapi"
    max_results: 10

  memory:
    provider: "mem0"
    max_memories: 1000

  web_extraction:
    provider: "firecrawl"
    format: "markdown"
```

### Essential Configuration Items

**Global Level:**

- `llm_provider`: Base URL, API key, default model (can be in .env instead)
- `collaboration`: Speaker selection, max rounds, termination controls
- `tools`: Tool provider configurations

**Agent Level:**

- `name`: Agent identifier
- `role`: "assistant", "user", or "system"
- `prompt_file`: Path to prompt file (relative to team config)
- `llm_config`: Model settings (temperature, max_tokens, etc.)
- `tools`: List of tool names this agent can use

**Team Level:**

- `name`: Team identifier
- `agents`: List of agent configurations

### LLM Configuration Options

```yaml
# Option 1: Global provider + per-agent settings
llm_provider:
  base_url: "https://api.deepseek.com"
  api_key: "${DEEPSEEK_API_KEY}"
  model: "deepseek-chat"

agents:
  - name: "researcher"
    llm_config:
      temperature: 0.2
      max_tokens: 4000
      top_p: 0.9
  - name: "writer"
    llm_config:
      temperature: 0.8
      max_tokens: 6000
      model: "deepseek-coder"  # Override global model

# Option 2: All in .env (cleaner)
# .env file:
# DEEPSEEK_BASE_URL=https://api.deepseek.com
# DEEPSEEK_API_KEY=sk-...
# DEEPSEEK_MODEL=deepseek-chat

agents:
  - name: "researcher"
    llm_config:
      temperature: 0.2
      max_tokens: 4000
```

### Team Collaboration Controls

```yaml
team:
  # Speaker selection methods
  speaker_selection_method: "auto" # LLM decides next speaker
  # speaker_selection_method: "round_robin"  # Fixed order
  # speaker_selection_method: "manual"       # Human selects

  # Loop prevention (CRITICAL)
  max_rounds: 15 # Hard limit on conversation rounds
  timeout_minutes: 30 # Time limit for entire task

  # Termination conditions
  termination_condition: "TERMINATE" # Message that ends conversation
  auto_terminate_keywords: ["DONE", "COMPLETE", "FINISHED"]

  # Speaker transitions (for round_robin)
  speaker_order: ["researcher", "writer", "coordinator"]
```

### Tool and Subsystem Configurations

```yaml
tools:
  search:
    provider: "serpapi"
    api_key: "${SERP_API_KEY}"
    max_results: 10
    timeout: 30

  memory:
    provider: "mem0"
    api_key: "${MEM0_API_KEY}"
    max_memories: 1000
    cleanup_threshold: 0.8

  web_extraction:
    provider: "firecrawl"
    api_key: "${FIRECRAWL_API_KEY}"
    format: "markdown"
    include_links: true

  code_execution:
    provider: "local" # or "daytona"
    timeout: 60
    memory_limit: "1GB"
    allowed_languages: ["python", "bash"]
```

### Prompt Files

```markdown
<!-- prompts/researcher.md -->

You are a research specialist focused on AI and technology trends.

Your responsibilities:

- Search for current information using web search
- Extract detailed content from relevant sources
- Analyze findings and identify key insights
- Store important information in memory for team access

Always cite your sources and provide comprehensive analysis.

When your research is complete, end your message with "RESEARCH_COMPLETE".
```

## Loading and Usage

```python
from roboco.config import load_team_config
from roboco.core import Team

# Load team from config
config = load_team_config("research_task/team.yaml")
team = Team.from_config(config)

# Run task with collaboration controls
result = await team.run("Research latest AI agent frameworks")
```

## Directory Structure

```
projects/
├── market_research/
│   ├── team.yaml
│   └── prompts/
│       ├── researcher.md
│       ├── analyst.md
│       └── writer.md
├── content_creation/
│   ├── team.yaml
│   └── prompts/
│       ├── researcher.md
│       ├── writer.md
│       └── editor.md
└── code_review/
    ├── team.yaml
    └── prompts/
        ├── reviewer.md
        └── tester.md
```

## Configuration Validation

Essential validation:

- Agent names are unique within team
- Prompt files exist and are readable
- Tool names are valid (from global tool registry)
- Roles are valid ("assistant", "user", "system")
- LLM config values are within valid ranges
- Max rounds > 0 (prevent infinite loops)
- Required API keys are available

```python
from roboco.config import validate_team_config

errors = validate_team_config("research_task/team.yaml")
if errors:
    print(f"Config errors: {errors}")
```

## Environment Variables (.env approach)

```bash
# LLM Provider
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_MODEL=deepseek-chat

# Tool APIs
SERPAPI_KEY=...
FIRECRAWL_API_KEY=...

# Global limits
ROBOCO_MAX_ROUNDS=20
ROBOCO_TIMEOUT_MINUTES=60
```

Clean, essential, focused - with the critical configurations restored.

```

```
