# Configuration System

Roboco uses a configuration-based approach to define agents, teams, and workflows. This allows for greater flexibility and easier customization without having to modify code.

## Directory Structure

The default configuration structure is:

```
config/
  ├── roles.yaml       # Contains role definitions
  ├── prompts/         # Contains markdown prompt files for each role
  │   ├── executive.md
  │   ├── product_manager.md
  │   ├── software_engineer.md
  │   └── report_writer.md
  ├── teams.yaml       # Contains team definitions
  └── teams/           # Contains team-specific YAML files
      └── planning.yaml
```

## Role Configuration

Roles are defined in the `roles.yaml` file, which contains basic information about each role. For example:

```yaml
roles:
  executive:
    name: Executive
    system_prompt: You are an Executive who oversees the project.

  product_manager:
    name: Product Manager
    system_prompt: You are a Product Manager who defines requirements.
```

## Detailed Role Prompts

For more detailed and structured prompts, you can create Markdown files in the `config/prompts/` directory. These files should be named after the role key, such as `executive.md`, `product_manager.md`, etc.

When an agent is created, the system will:

1. First check for a detailed markdown prompt in the `prompts` directory
2. If not found, fall back to the compact prompt in `roles.yaml`
3. If neither exists, use a default prompt

Example markdown prompt for a Product Manager:

```markdown
# Product Manager

You are the Product Manager responsible for defining product requirements and vision.

## Your Responsibilities

- Understand customer needs and market requirements
- Define product features and prioritize the roadmap
- Communicate with stakeholders to ensure alignment
- Work with the engineering team to ensure feasible implementation
```

## Using Custom Prompts Directory

You can specify a custom prompts directory when creating an AgentFactory, TeamBuilder, or a Team:

```python
# Direct with AgentFactory
agent_factory = AgentFactory(prompts_dir="path/to/custom_prompts")

# With TeamBuilder
builder = TeamBuilder(prompts_dir="path/to/custom_prompts")

# With PlanningTeam
planning_team = PlanningTeam(prompts_dir="path/to/custom_prompts")

# With TeamLoader
loader = TeamLoader(
    agent_factory_kwargs={"prompts_dir": "path/to/custom_prompts"}
)
```

## Team Configuration

Teams are defined in the `teams.yaml` file:

```yaml
teams:
  planning:
    name: Planning Team
    roles:
      - executive
      - product_manager
      - software_engineer
      - report_writer
    tool_executor: human_proxy
    workflow:
      - from: product_manager
        to: software_engineer
      - from: software_engineer
        to: report_writer
      - from: report_writer
        to: executive
      - from: executive
        to: product_manager
```
