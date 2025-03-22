# Configuration-Based Design

The RoboCo framework provides a flexible, configuration-based approach to defining and creating teams of AI agents. This document explains how to use this system to create custom teams without writing specialized agent or team classes.

## Overview

The configuration-based team system consists of three main components:

1. **Role Definitions**: Markdown files containing detailed prompts for each agent role
2. **Team Configurations**: YAML files defining team composition, workflow, and tools
3. **Team Builder**: A utility for loading and creating teams from configuration files

This approach offers several advantages:

- Easily create and modify teams without changing code
- Share and version team configurations as simple text files
- Separate agent behavior (prompts) from team structure (composition and workflow)
- Experiment with different team configurations without code changes

## Directory Structure

```
roboco/
├── config/
│   ├── prompts/                # Role-specific prompt files
│   │   ├── executive.md
│   │   ├── product_manager.md
│   │   └── ...
│   ├── config.yaml             # System-level configurations
│   ├── roles.yaml              # Role configuration mapping
│   └── teams.yaml              # Global team definitions
└── src/
    └── roboco/
        ├── core/
        │   └── team_builder.py # Team building functionality
        └── teams/              # Specialized team implementations
            ├── planning.py
            └── ...
```

## Role Definitions

Roles are defined in markdown files located in the `config/prompts/` directory. Each file contains a detailed prompt that defines an agent's behavior, capabilities, and responsibilities.

Example (`config/prompts/product_manager.md`):

```markdown
# Product Manager

You are the Product Manager agent, responsible for defining product requirements, creating roadmaps, and ensuring the team delivers value to users.

## Responsibilities

- Gather and analyze user requirements
- Define product vision and strategy
- Create and maintain product roadmaps
- Prioritize features based on business value
- Ensure the product meets user needs

## Communication

You should communicate clearly with team members, focusing on user needs and business value. Use the following guidelines:
...
```

## Team Configuration

Teams are defined in YAML files, with a global configuration in `config/teams.yaml` and individual role configurations in `config/roles.yaml`.

### Global Configuration

The global configuration in `config/teams.yaml` defines all available teams and their basic properties:

```yaml
teams:
  planning:
    name: "PlanningTeam"
    description: "A team that collaborates to create project planning documents"
    output_dir: "workspace/plan"
    roles:
      - executive
      - product_manager
      - software_engineer
      - report_writer
      - human_proxy
    workflow:
      - from: product_manager
        to: software_engineer
      - from: software_engineer
        to: report_writer
      - from: report_writer
        to: executive
      - from: executive
        to: product_manager
    tools:
      - filesystem
    tool_executor: human_proxy
```

### Role Configuration

Role configurations are defined in `config/roles.yaml` and specify the prompts and parameters for each agent role:

```yaml
# config/roles.yaml
roles:
  executive:
    prompt_file: "executive.md"
    temperature: 0.3
    max_tokens: 2000
  product_manager:
    prompt_file: "product_manager.md"
    temperature: 0.7
    max_tokens: 4000
  software_engineer:
    prompt_file: "software_engineer.md"
    temperature: 0.5
    max_tokens: 4000
```

## Using the Configuration-Based System

### Creating a Team with TeamBuilder

You can create a team directly using the `TeamBuilder`:

```python
from roboco.core import TeamBuilder

# Create a team from configuration
planning_team = TeamBuilder.create_team("planning")

# Get a list of available team configurations
available_teams = TeamBuilder.list_available_teams()
print(f"Available teams: {available_teams}")

# Use the team
result = await planning_team.run_swarm(
    initial_agent_name="product_manager",
    query="Create a project plan for a robot control system"
)
```

### Using Specialized Team Implementations

For common team types, you can use specialized team implementations that build on the configuration system:

```python
from roboco.teams import PlanningTeam

# Create a planning team
planning_team = PlanningTeam(
    name="MyPlanningTeam",
    output_dir="workspace/my_plans"  # Override output directory
)

# Use team-specific methods
result = await planning_team.create_planning_suite(
    vision="Create a robot control system that adapts to different environments"
)
```

## Creating Custom Team Configurations

To create a custom team configuration:

1. Add your team definition to `config/teams.yaml`:

```yaml
teams:
  my_custom_team:
    name: "MyCustomTeam"
    description: "My specialized team for task X"
    roles:
      - role1
      - role2
      - role3
    workflow:
      - from: role1
        to: role2
      - from: role2
        to: role3
      - from: role3
        to: role1
    tools:
      - filesystem
      - web_search
```

2. Add or update role entries in `config/roles.yaml` for each role:

```yaml
# config/roles.yaml
roles:
  role1:
    prompt_file: "role1.md"
    temperature: 0.5
  role2:
    prompt_file: "role2.md"
    temperature: 0.3
  role3:
    prompt_file: "role3.md"
    temperature: 0.7
```

3. Create role-specific prompts in `config/prompts/` for each role:

   - `config/prompts/role1.md`
   - `config/prompts/role2.md`
   - `config/prompts/role3.md`

4. Create and use your team:

```python
from roboco.core import TeamBuilder

my_team = TeamBuilder.create_team("my_custom_team")
```

## Advanced Configuration

### Conditional Handoffs

You can define conditional handoffs based on message content:

```yaml
workflow:
  - from: product_manager
    to: software_engineer
    condition:
      check: "content"
      contains: ["implementation", "code", "develop"]
  - from: product_manager
    to: executive
    condition:
      check: "content"
      contains: ["approve", "review", "budget"]
```

### Tool Configuration

Configure which tools are available to the team and which agent executes them:

```yaml
tools:
  - filesystem
  - browser_use
  - terminal
tool_executor: human_proxy
```

### System Configuration

The `config/config.yaml` file contains system-wide settings:

```yaml
# Core settings
core:
  workspace_base: "./workspace"
  workspace_root: "workspace"

# LLM settings
llm:
  model: "gpt-4o"
  api_key: "${OPENAI_API_KEY}"
  max_tokens: 8000
  temperature: 0.7
  base_url: "https://api.openai.com/v1"
```

## Tool Registration

When creating a team with tool capabilities, you need to register tools with their executor agent:

```python
from roboco.core import TeamBuilder
from roboco.tools import FileSystemTool, WebSearchTool

# Create a team
planning_team = TeamBuilder.create_team("planning")

# Get the executor agent (typically HumanProxy)
executor = planning_team.get_agent("human_proxy")

# Create and register tools
fs_tool = FileSystemTool()
web_tool = WebSearchTool()

# Register tools with the executor
executor.register_tool(fs_tool)
executor.register_tool(web_tool)

# Now other agents can use these tools through the executor
```

## Best Practices

1. **Keep prompts in markdown files**: This makes them easier to edit and share
2. **Use the roles.yaml file for agent parameters**: Define temperature, max_tokens, etc.
3. **Define clear handoff workflows**: Consider carefully which agent should work on what and when
4. **Make prompt files descriptive and focused**: Each role should have clear responsibilities
5. **Use descriptive role names**: Role names should clearly indicate the agent's purpose
6. **Specify a tool executor**: Make sure to designate which agent will execute tools
7. **Keep agent responsibilities focused**: Each agent should have a clear, specific role

## Combining with Custom Agent Implementations

While the configuration-based approach is recommended for most use cases, there are situations where you may need to create custom Agent subclasses for specialized behavior that can't be expressed through configuration alone.

### When to Use Custom Agent Implementations

Consider creating custom Agent classes when:

1. You need specialized processing logic that goes beyond what prompts can express
2. You want to integrate with external systems or APIs in a way specific to an agent role
3. You need to implement complex state management within an agent
4. You're extending the Agent functionality with new capabilities

### Registering Custom Agent Classes

Custom Agent classes can be registered with the AgentFactory and used in your configuration-based teams:

```python
from roboco.core.agent import Agent
from roboco.core.agent_factory import AgentFactory

# Create a custom Agent subclass
class MySpecializedAgent(Agent):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        # Custom initialization

    async def generate_response(self, messages):
        # Custom response generation logic
        return await super().generate_response(messages)

# Register with the AgentFactory
AgentFactory.register_agent_class("my_specialized_role", MySpecializedAgent)

# Now you can use "my_specialized_role" in your team configurations
```

### Mixed Approaches

It's perfectly valid to mix configuration-based agents with custom Agent subclasses in the same team:

```yaml
# In config/teams.yaml
teams:
  mixed_team:
    name: "MixedTeam"
    description: "Team with both config-based and custom agents"
    roles:
      - product_manager # Uses configuration
      - software_engineer # Uses configuration
      - my_specialized_role # Uses custom Agent subclass
    workflow:
      - from: product_manager
        to: software_engineer
      - from: software_engineer
        to: my_specialized_role
      - from: my_specialized_role
        to: product_manager
```

## Example: Creating a Planning Team

Here's a complete example of creating and using a planning team:

```python
import asyncio
from roboco.core import TeamBuilder
from roboco.tools import FileSystemTool

async def main():
    # Create a planning team
    planning_team = TeamBuilder.create_team("planning")

    # Get the human proxy agent
    human_proxy = planning_team.get_agent("human_proxy")

    # Register tools
    fs_tool = FileSystemTool()
    human_proxy.register_tool(fs_tool)

    # Run the team
    result = await planning_team.run_swarm(
        initial_agent_name="product_manager",
        query="Create a project plan for a humanoid robot that can assist in hospitals"
    )

    print(f"Team finished with result: {result}")

    # Results are typically saved to the team's output directory
    print(f"Check results in: {planning_team.output_dir}")

if __name__ == "__main__":
    asyncio.run(main())
```
