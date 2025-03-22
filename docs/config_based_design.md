# CBD: Configuration-Based-Design

The Roboco framework provides a flexible, configuration-based approach to defining and creating teams of AI agents. This document explains how to use this system to create custom teams without writing specialized agent or team classes.

## Overview

The configuration-based team system consists of three main components:

1. **Role Definitions**: Markdown files containing detailed prompts for each agent role
2. **Team Configurations**: YAML files defining team composition, workflow, and tools
3. **Team Loader**: A utility for loading and creating teams from configuration files

This approach offers several advantages:

- Easily create and modify teams without changing code
- Share and version team configurations as simple text files
- Separate agent behavior (prompts) from team structure (composition and workflow)
- Experiment with different team configurations without code changes

## Directory Structure

```
roboco/
├── config/
│   ├── roles/                  # Role-specific prompt files
│   │   ├── executive.md
│   │   ├── product_manager.md
│   │   └── ...
│   ├── roles.yaml              # Legacy role mapping
│   ├── teams/                  # Team-specific configuration files
│   │   ├── planning.yaml
│   │   ├── development.yaml
│   │   └── ...
│   └── teams.yaml              # Global team definitions
└── src/
    └── roboco/
        ├── core/
        │   ├── team_builder.py
        │   └── team_loader.py
        └── teams/              # Simplified team implementations
            ├── planning.py
            └── ...
```

## Role Definitions

Roles are defined in markdown files located in the `config/roles/` directory. Each file contains a detailed prompt that defines an agent's behavior, capabilities, and responsibilities.

Example (`config/roles/product_manager.md`):

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

Teams are defined in YAML files, with a global configuration in `config/teams.yaml` and team-specific configurations in `config/teams/`.

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

### Team-Specific Configuration

Team-specific configurations can override or extend the global configuration:

```yaml
# config/teams/planning.yaml
description: "Enhanced planning team that creates comprehensive project planning documents"
output_dir: "workspace/enhanced_plan"

agent_configs:
  executive:
    temperature: 0.3
    max_tokens: 2000
  product_manager:
    temperature: 0.7
    max_tokens: 4000

tasks:
  create_planning_suite:
    description: "Creates a complete suite of planning documents"
    initial_agent: "product_manager"
    prompt_template: >
      Based on this vision: "{vision}"
      ...
```

## Using the Configuration-Based System

### Creating a Team with TeamBuilder

You can create a team directly using the `TeamBuilder`:

```python
from roboco.core import TeamBuilder

# Get the TeamBuilder singleton instance
builder = TeamBuilder.get_instance()

# List available team configurations
available_teams = builder.list_available_teams()
print(f"Available teams: {available_teams}")

# Create a team
planning_team = TeamBuilder.create_team("planning")

# Use the team
result = await planning_team.run_swarm(
    initial_agent_name="ProductManager",
    query="Create a project plan for a robot control system"
)
```

### Using Specialized Team Classes

For common team types, you can use specialized team classes that build on the configuration system:

```python
from roboco.teams.planning import PlanningTeam

# Create a planning team
planning_team = PlanningTeam(
    name="MyPlanningTeam",
    team_key="planning",  # Which configuration to use
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
```

2. Optionally create a team-specific configuration at `config/teams/my_custom_team.yaml`

3. Create role-specific prompts in `config/roles/` if needed

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

Configure which tools are available and which agent executes them:

```yaml
tools:
  - filesystem
  - browser_use
  - code_interpreter
tool_executor: human_proxy
```

### Task Definitions

Define task-specific configurations with prompt templates and settings:

```yaml
tasks:
  create_document:
    description: "Creates a document based on a template"
    initial_agent: "writer"
    max_rounds: 5
    prompt_template: >
      Create a {document_type} document about {topic}.
      Include the following sections: {sections}
```

## Best Practices

1. **Keep prompts in markdown files**: This makes them easier to edit and share
2. **Use team-specific configs for variations**: Override only what changes in team-specific configs
3. **Define clear handoff workflows**: Consider carefully which agent should work on what and when
4. **Define task templates**: For common tasks, define reusable prompt templates
5. **Use descriptive role keys**: Role keys should clearly indicate the agent's purpose

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
        return "My specialized response"

# Register with the AgentFactory
factory = AgentFactory()
factory.register_agent_class("my_specialized_role", MySpecializedAgent)

# Now you can use "my_specialized_role" in your team configurations
```

### Using in TeamBuilder

You can also use custom Agent classes in your TeamBuilder:

```python
from roboco.core.team_builder import TeamBuilder

builder = TeamBuilder()
builder.with_roles("my_specialized_role")
team = builder.build(name="MyTeam")
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

### Best Practices for Custom Agents

When creating custom Agent subclasses:

1. **Inherit from the base Agent class**: This ensures compatibility with the framework
2. **Follow the AG2 conventions**: Respect the established patterns for agent communication
3. **Focus on the specialized behavior**: Implement only what's truly unique to this agent
4. **Register your agent class**: Make it available to the AgentFactory for configuration use
5. **Document the agent's capabilities**: Make it clear what your agent does differently
