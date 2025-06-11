# Configuration-Based Design

The Roboco framework provides a flexible, configuration-based approach to defining and creating a team of AI agents. This document explains how to use this system to create a custom agent team without writing specialized agent classes. All agent system prompts, tool selections, and workflows (including handoff rules) are fully defined in configuration files (YAML and Jinja2 templates), enabling visualization and monitoring of agent configurations and status.

## Overview

The configuration-based team system consists of four main components:

1. **Role Definitions**: Jinja2 template files containing detailed prompts for each agent role
2. **Team Configuration**: YAML files defining team composition, workflow, tool selections, and handoff rules
3. **Team Builder**: A utility for loading and creating a team from configuration files
4. **Visualization & Monitoring**: Tools for visualizing configurations and monitoring agent status

This approach offers several advantages:

- Easily create and modify the team without changing code
- Share and version team configuration as simple text files
- Separate agent behavior (prompts) from team structure (composition and workflow)
- Experiment with different configurations without code changes
- Integrate with external teams via MCP servers

## Directory Structure

```
roboco/
├── config/
│   ├── roles/                  # Role-specific template files
│   │   ├── executive.md
│   │   ├── product_manager.md
│   │   └── ...
│   ├── config.yaml             # System-level configurations
│   ├── roles.yaml              # Role configuration mapping
│   └── team.yaml               # Team configuration
└── src/
    └── roboco/
        ├── core/
        │   └── team_builder.py # Team building functionality
        └── presets/            # Preset team configurations
            ├── planning.py
            └── ...
```

## Role Definitions

Role definitions are stored as Jinja2 template files in the `roles` directory. Each file contains:

- **System Prompt**: The primary instructions for the agent with variable placeholders
- **Role-specific information**: Specialized knowledge or instructions
- **Interaction Guidelines**: How the agent should communicate
- **Variable Definitions**: Placeholders that will be filled at runtime

Example directory structure:

```
roles/
  programmer.md
  product_manager.md
  reviewer.md
  ...
```

Example template file (programmer.md):

```jinja
You are a {{ programming_language }} programmer with {{ experience_level }} experience.

Your task is to implement code for the {{ project_name }} project using best practices for {{ programming_language }}.

Current workspace: {{ workspace_path }}

{% if tools_available %}
You have access to the following tools:
{% for tool in tools_available %}
- {{ tool.name }}: {{ tool.description }}
{% endfor %}
{% endif %}

Follow these coding standards:
{{ coding_standards }}
```

### Jinja2 Template Rendering

The Roboco framework uses Jinja2 for dynamic prompt template rendering. This allows for:

1. **Variable Injection**: Insert runtime values like workspace paths, project details, and tool information
2. **Conditional Logic**: Include or exclude sections based on runtime conditions
3. **Loops and Iteration**: Generate content based on collections of data
4. **Template Inheritance**: Share common prompt components across multiple roles

At runtime, the system will render these templates with the appropriate context variables:

```python
from jinja2 import Environment, FileSystemLoader
import os

# Set up Jinja2 environment
templates_dir = os.path.join(os.environ.get("ROBOCO_DATA_PATH", "."), "roles")
env = Environment(loader=FileSystemLoader(templates_dir))

# Load a template
template = env.get_template("programmer.md")

# Render with context variables
system_prompt = template.render(
    programming_language="Python",
    experience_level="expert",
    project_name="Roboco",
    workspace_path="/Users/username/projects/roboco",
    tools_available=[
        {"name": "filesystem", "description": "Access and modify files"},
        {"name": "terminal", "description": "Run shell commands"}
    ],
    coding_standards="PEP 8 style guide for Python code"
)
```

## Team Configuration

The team is defined in YAML files, with the main configuration in `config/team.yaml` and individual role configurations in `config/roles.yaml`. These configuration files fully define agent system prompts, tool selections, and workflows (including handoff rules).

### Team Configuration

The configuration in `config/team.yaml` defines the team structure and its basic properties:

```yaml
# config/team.yaml
name: "ResearchWritingTeam"
description: "A team that collaborates to research topics and write documentation."
output_dir: "workspace/research_writing"
roles:
  - executive
  - product_manager
  - software_engineer
  - report_writer
  - human_proxy
workflow:
  - from: product_manager
    to: software_engineer
    condition: "{{ 'code_implementation' in message.content }}"
  - from: software_engineer
    to: report_writer
    condition: "{{ message.content | contains_keyword('documentation') }}"
  - from: report_writer
    to: product_manager
tools:
  - name: filesystem
    allowed_for:
      - software_engineer
      - report_writer
  - name: web_search
    allowed_for:
      - product_manager
      - software_engineer
  - name: terminal
    allowed_for:
      - software_engineer
tool_executor: human_proxy
external_mcp_servers:
  - name: "data_science_team"
    url: "http://data-science-team:8080"
    description: "External data science team for advanced analytics"
  - name: "security_team"
    url: "http://security-team:8080"
    description: "Security team for code review and vulnerability assessment"
```

### Role Configuration

Role configurations are defined in `config/roles.yaml` and specify the templates, parameters, and template variables for each agent role:

```yaml
# config/roles.yaml
roles:
  executive:
    template_file: "executive.md"
    temperature: 0.3
    max_tokens: 2000
    template_variables:
      experience_level: "senior"
      management_style: "strategic"
      reporting_format: "executive summary"
  product_manager:
    template_file: "product_manager.md"
    temperature: 0.7
    max_tokens: 4000
    template_variables:
      product_domain: "healthcare robotics"
      market_research: true
      user_personas:
        - name: "Hospital Administrator"
          needs: ["efficiency", "compliance", "cost management"]
        - name: "Nurse"
          needs: ["patient care support", "reduced workload"]
  software_engineer:
    template_file: "software_engineer.md"
    temperature: 0.5
    max_tokens: 4000
    template_variables:
      programming_language: "Python"
      experience_level: "expert"
      coding_standards: "PEP 8 style guide for Python code"
```

At runtime, the system will combine these role-specific template variables with global context variables (like workspace paths, available tools, etc.) when rendering the Jinja2 templates.

## Using the Configuration-Based System

### Creating a Team with TeamBuilder

You can create a team using the `TeamBuilder`, which loads configurations from YAML files and renders Jinja2 templates:

```python
from roboco.core import TeamBuilder

# Create a team from the default configuration
team = TeamBuilder.create_team()

# Create a team from a preset configuration for a specific business purpose
research_writing_team = TeamBuilder.create_team_from_preset("research_writing")

# Create a team with custom template variables
custom_team = TeamBuilder.create_team(
    template_variables={
        "project_name": "Hospital Assistant Robot",
        "workspace_path": "/path/to/project",
        "programming_language": "Python"
    }
)

# Use the team
result = await research_writing_team.run(
    initial_agent_name="product_manager",
    query="Create a project plan for a humanoid robot control system"
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

## Creating Your Own Team Configuration

To create a custom team configuration:

1. Define your team in `config/team.yaml`:

```yaml
# config/team.yaml
name: "MyCustomTeam"
description: "Description of your custom team"
output_dir: "workspace/custom"
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
  - name: filesystem
    allowed_for:
      - role1
      - role3
  - name: web_search
    allowed_for:
      - role2
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

The `config/config.yaml` file contains system-wide settings, including paths, LLM configuration, and monitoring settings:

```yaml
# Core settings
core:
  workspace_base: "./workspace"
  workspace_root: "workspace"
  data_path: "${ROBOCO_DATA_PATH}"
  template_path: "${ROBOCO_DATA_PATH}/roles"

# LLM settings
llm:
  model: "gpt-4o"
  api_key: "${OPENAI_API_KEY}"
  max_tokens: 8000
  temperature: 0.7
  base_url: "https://api.openai.com/v1"

# Visualization settings
visualization:
  enabled: true
  output_dir: "${ROBOCO_DATA_PATH}/visualizations"
  format: "png"

# Monitoring settings
monitoring:
  enabled: true
  metrics_collection_interval: 5 # seconds
  log_level: "info"
  agentok_integration: true
  agentok_url: "http://localhost:3000"
```

## Tool Registration

When creating a team with tool capabilities, you need to register tools with their executor agent:

```python
from roboco.core import TeamBuilder
from roboco.tools import FileSystemTool, WebSearchTool

# Create a team from a preset
team = TeamBuilder.create_team_from_preset("research_writing")

# Get the executor agent (typically HumanProxy)
executor = team.get_agent("human_proxy")

# Create and register tools
fs_tool = FileSystemTool()
web_tool = WebSearchTool()

# Register tools with the executor
executor.register_tool(fs_tool)
executor.register_tool(web_tool)

# Now other agents can use these tools through the executor
```

## Visualization and Monitoring

The configuration-based design system supports visualization and monitoring of agent configurations and status. This enables real-time insights into team behavior and performance.

### Configuration Visualization

The Roboco framework provides built-in tools to visualize team configurations:

```python
from roboco.core import TeamBuilder, TeamVisualizer

# Create a team from a preset
team = TeamBuilder.create_team_from_preset("research_writing")

# Generate a visualization of the team structure
TeamVisualizer.generate_team_diagram(team, output_path="team_diagram.png")

# Generate a visualization of the workflow
TeamVisualizer.generate_workflow_diagram(team, output_path="workflow_diagram.png")

# Generate a visualization of tool assignments
TeamVisualizer.generate_tool_diagram(team, output_path="tool_diagram.png")
```

### Status Monitoring

Roboco integrates with monitoring tools to provide real-time insights into agent status and performance:

```python
from roboco.core import TeamBuilder
from roboco.monitoring import AgentMonitor

# Create a team from a preset
team = TeamBuilder.create_team_from_preset("research_writing")

# Create a monitor
monitor = AgentMonitor(team)

# Start monitoring
monitor.start()

# Run the team
await team.run(
    initial_agent_name="product_manager",
    query="Create a project plan for a humanoid robot that can assist in hospitals"
)

# Get monitoring data
status_report = monitor.get_status_report()
performance_metrics = monitor.get_performance_metrics()

# Stop monitoring
monitor.stop()
```

### Integration with AgentOK

Roboco can integrate with AgentOK for real-time UI-based configuration and monitoring:

```python
from roboco.core import TeamBuilder
from roboco.integrations import AgentOKIntegration

# Create a team
team = TeamBuilder.create_team_from_preset("research_writing")

# Connect to AgentOK
agentok = AgentOKIntegration()
agentok.connect_team(team)

# Start UI server (accessible at http://localhost:3000)
agentok.start_ui_server()

# Run the team (status will be visible in the AgentOK UI)
await team.run_swarm(
    initial_agent_name="product_manager",
    query="Create a project plan for a humanoid robot that can assist in hospitals"
)
```

## Best Practices

1. **Use Jinja2 templates for prompts**: This enables dynamic content and variable injection
2. **Structure template variables in roles.yaml**: Define role-specific variables for template rendering
3. **Define conditional handoff workflows**: Use conditions to create dynamic agent interactions
4. **Specify tool permissions per role**: Control which agents can access which tools
5. **Use descriptive role names**: Role names should clearly indicate the agent's purpose
6. **Specify a tool executor**: Make sure to designate which agent will execute tools
7. **Keep agent responsibilities focused**: Each agent should have a clear, specific role
8. **Leverage visualization tools**: Use diagrams to understand team structure and workflow
9. **Monitor agent performance**: Track metrics to identify bottlenecks and improve efficiency

## Example: Using a Research Writing Preset

Here's a complete example of creating and using a research and writing team from a preset configuration:

```python
import asyncio
from roboco.core import TeamBuilder
from roboco.tools import FileSystemTool

async def main():
    # Create a team from a preset
    team = TeamBuilder.create_team_from_preset("research_writing")

    # Get the human proxy agent
    human_proxy = team.get_agent("human_proxy")

    # Register tools
    fs_tool = FileSystemTool()
    human_proxy.register_tool(fs_tool)

    # Run the team
    result = await team.run(
        initial_agent_name="product_manager",
        query="Create a project plan for a humanoid robot that can assist in hospitals"
    )

    print(f"Team finished with result: {result}")

    # Results are typically saved to the team's output directory
    print(f"Check results in: {team.output_dir}")

if __name__ == "__main__":
    asyncio.run(main())
```

```

```
