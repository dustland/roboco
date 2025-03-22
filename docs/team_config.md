# Team Configuration Guide

This guide explains how to configure teams and roles in Roboco, including the role-based LLM configuration approach.

## Configuration Files

Roboco's team system relies on three main configuration sources:

- `config/roles.yaml`: Defines individual agent roles and their LLM configurations
- `config/teams.yaml`: Defines team compositions, workflows, and shared resources
- `config/prompts/*.md`: Contains detailed system prompts for each role in markdown format

## Role Configuration

Each role is defined in `roles.yaml` with the following structure:

```yaml
roles:
  role_key:
    name: "RoleName"
    description: "Role description"
    type: "agent" # or "human_proxy"
    llm:
      provider: "llm" # Provider name (llm, openai, deepseek, etc.)
      model: "gpt-4" # Model name
      temperature: 0.7 # Temperature for text generation
      max_tokens: 4000 # Max tokens to generate
```

### System Prompts

Instead of including system prompts directly in `roles.yaml`, all prompts are now stored as markdown files in the `config/prompts/` directory. The files should be named to match the role key, for example:

- `config/prompts/executive.md` - System prompt for the executive role
- `config/prompts/product_manager.md` - System prompt for the product manager role

This approach allows for more detailed, well-formatted prompts and makes it easier to version and update them separately from the role configurations.

The system will automatically load the appropriate prompt file for each role. If a prompt file is not found, a default prompt will be generated based on the role's name.

### LLM Configuration

The `llm` section in each role definition specifies which language model configuration to use for that role. This allows you to:

- Use different models for different roles based on their strengths
- Customize temperature, token limits, and other parameters per role
- Create specialized combinations like high-temperature creative roles and low-temperature analytical roles

Available providers include:

- `llm`: Default LLM configuration from config.yaml
- `openai`: OpenAI models (GPT-4, etc.)
- `deepseek`: DeepSeek models (optimized for coding tasks)
- `ollama`: Local models via Ollama
- Others as configured in your `config.yaml`

## Team Configuration

Teams are defined in `teams.yaml` with the following structure:

```yaml
teams:
  team_key:
    name: "TeamName"
    description: "Team purpose and function"
    output_dir: "workspace/team_output"
    roles:
      - role_key1
      - role_key2
      - role_key3
    workflow:
      - from: role_key1
        to: role_key2
      - from: role_key2
        to: role_key3
      - from: role_key3
        to: role_key1
    tools:
      - tool_name1
      - tool_name2
    tool_executor: role_key3
    agent_configs:
      role_key1:
        param1: value1
      role_key2:
        param2: value2
```

### Team Parameters

- `name`: Display name for the team
- `description`: Purpose and function of the team
- `output_dir`: Directory for team output files
- `roles`: List of role keys to include in the team
- `workflow`: Handoff sequence between agents
- `tools`: Tools available to the team
- `tool_executor`: Role that executes tools on behalf of other agents
- `agent_configs`: Additional agent-specific configuration parameters

Note that LLM configuration is handled at the role level in `roles.yaml`, not in the team configuration.

## Creating a Team

Teams can be created programmatically using the `TeamBuilder` class:

```python
from roboco.core import TeamBuilder

# Get the TeamBuilder singleton
builder = TeamBuilder.get_instance()

# Configure roles - these will use their LLM configurations from roles.yaml
# and their system prompts from the prompts/ directory
builder.with_roles("executive", "product_manager", "software_engineer", "report_writer")

# Configure tool executor
builder.with_tool_executor("human_proxy")

# Configure workflow
builder.with_circular_workflow(
    "product_manager",
    "software_engineer",
    "report_writer",
    "executive"
)

# Build the team
team = builder.build(name="ProjectPlanningTeam")
```

Or by using existing team classes that encapsulate specific team configurations:

```python
from roboco.teams.planning import PlanningTeam

# Create a planning team - each role will use its LLM configuration from roles.yaml
# and its system prompt from the matching markdown file
planning_team = PlanningTeam(
    name="ProjectPlanningTeam",
    output_dir="workspace/plan"
)
```

## Example

For a complete example of using role-based LLM configurations, see `examples/team/role_llm_config.py`.
