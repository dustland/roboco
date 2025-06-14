# DeepSeek Optimization

## Simple and Elegant Solution

You're absolutely right! Since we already separate tool callers and tool executors (following AG2 patterns), we just need to ensure tool executors don't use `deepseek-reasoner`. This is much simpler than complex hybrid architectures.

## How It Works

### Automatic Model Selection

The system automatically chooses the right DeepSeek model:

- **DeepSeek-Reasoner**: For pure reasoning tasks (best thinking)
- **DeepSeek-Chat**: For tool execution tasks (tool calling support)

### Detection Logic

Agents automatically switch from `deepseek-reasoner` to `deepseek-chat` if they:

1. **Have code execution enabled** (`enable_code_execution=True`)
2. **Have tool-indicating names** (contains: "executor", "tool", "search", "web", "code", "browser")

### Configuration

```python
from roboco.core import Agent, AgentConfig, AgentRole
from roboco.core.brain import BrainConfig

# Default: Use deepseek-reasoner for best reasoning
brain_config = BrainConfig(
    model="deepseek-reasoner",           # Default reasoning model
    tool_executor_model="deepseek-chat"  # Fallback for tool execution
)

# Reasoning agent - keeps deepseek-reasoner
philosopher = Agent(AgentConfig(
    name="philosopher",
    brain_config=brain_config
))
# Result: Uses deepseek-reasoner ✅

# Tool executor - automatically switches to deepseek-chat
executor = Agent(AgentConfig(
    name="executor",
    brain_config=brain_config,
    enable_code_execution=True
))
# Result: Uses deepseek-chat ✅
```

## Benefits

### 1. **Automatic Optimization**

- No manual configuration needed
- Intelligent model selection based on agent capabilities
- Maintains backward compatibility

### 2. **Best of Both Worlds**

- **DeepSeek-Reasoner**: Superior reasoning for thinking tasks
- **DeepSeek-Chat**: Tool calling support for execution tasks

### 3. **Simple Implementation**

- Single check in agent initialization
- No complex routing logic
- Leverages existing AG2 separation patterns

## Usage Examples

### Team Configuration

```yaml
# config/team.yaml
agents:
  - name: planner
    class: "roboco.core.Agent"
    brain_config:
      model: "deepseek-reasoner" # Will use reasoner for planning

  - name: executor
    class: "roboco.core.Agent"
    brain_config:
      model: "deepseek-reasoner" # Will auto-switch to deepseek-chat
    enable_code_execution: true

  - name: web_searcher
    class: "roboco.core.Agent"
    brain_config:
      model: "deepseek-reasoner" # Will auto-switch to deepseek-chat
```

### Result

- **planner**: Uses `deepseek-reasoner` (pure reasoning)
- **executor**: Uses `deepseek-chat` (has code execution)
- **web_searcher**: Uses `deepseek-chat` (name indicates tools)

## Implementation Details

### Agent Initialization Check

```python
# In Agent.__init__()
if (brain_config.model == "deepseek-reasoner" and
    (config.enable_code_execution or self._has_tools_configured())):
    logger.info(f"Agent {self.name} has tools - switching to deepseek-chat")
    brain_config.model = brain_config.tool_executor_model
```

### Tool Detection Heuristics

```python
def _has_tools_configured(self) -> bool:
    """Check if agent likely needs tool calling."""
    tool_indicators = ["executor", "tool", "search", "web", "code", "browser"]
    return any(indicator in self.name.lower() for indicator in tool_indicators)
```

## Why This Works

1. **Separation of Concerns**: Tool calling and reasoning are separate responsibilities
2. **AG2 Pattern**: We already separate callers and executors
3. **Automatic Detection**: No manual configuration burden
4. **Optimal Performance**: Each model used for its strengths

## Migration

Existing configurations work without changes:

- Agents using `deepseek-chat` continue working
- Agents using `deepseek-reasoner` get automatic optimization
- Tool executors automatically get tool calling support

This elegant solution maximizes DeepSeek's capabilities while maintaining simplicity and compatibility.
