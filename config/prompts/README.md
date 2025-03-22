# Agent Prompts

This directory contains detailed prompt files for each agent role in the Roboco framework. Each prompt file is a markdown document that provides instructions and context for the agent.

## File Structure

- Each prompt is defined in a separate markdown file named after the role key (e.g., `executive.md`, `product_manager.md`)
- Use markdown formatting to organize the prompt into sections
- Prompts should follow a consistent structure for readability

## Prompt Structure

A well-structured prompt typically includes:

1. **Title/Role Definition**: Clearly state the agent's role
2. **Responsibilities**: Define the agent's primary tasks and responsibilities
3. **Approach**: Describe how the agent should approach problems
4. **Communication Style**: Define the agent's tone and communication pattern
5. **Optional Sections**: Add role-specific sections as needed

## Example Format

```markdown
# Product Manager

You are the Product Manager responsible for defining product requirements and vision.

## Your Responsibilities

- Understand customer needs and market requirements
- Define product features and prioritize the roadmap
- Communicate with stakeholders to ensure alignment
- Work with the engineering team to ensure feasible implementation

## Your Approach

You focus on creating detailed, actionable specifications that are clear and complete.
You prioritize features based on customer value and business impact.
You ensure all requirements are testable and measurable.

## Communication Style

You are concise, specific, and use examples to illustrate your points.
You ask clarifying questions when requirements are ambiguous.
You stay focused on user value and business outcomes.
```

## Loading Mechanism

When an agent is created, the system will:

1. First check for a detailed markdown prompt in this directory with a filename matching the role key (e.g., `executive.md`)
2. If no matching prompt file is found, a default prompt will be generated based on the role name

**Note:** System prompts are no longer defined in `roles.yaml`. All prompts should be placed in this directory as markdown files.

## File Naming

The prompt files must be named to match the role key in `roles.yaml`:

| Role Key             | Prompt File             |
| -------------------- | ----------------------- |
| `executive`          | `executive.md`          |
| `product_manager`    | `product_manager.md`    |
| `software_engineer`  | `software_engineer.md`  |
| `report_writer`      | `report_writer.md`      |
| `human_proxy`        | `human_proxy.md`        |
| `robotics_scientist` | `robotics_scientist.md` |

## Custom Prompt Directories

You can specify a custom prompts directory when creating an AgentFactory, TeamBuilder, or a Team:

```python
# With AgentFactory
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

## Best Practices

1. Make prompts comprehensive but concise
2. Use markdown formatting for readability
3. Be specific about the agent's role, responsibilities, and communication style
4. Avoid overly restrictive instructions that might limit the agent's effectiveness
5. Use consistent formatting and structure across all prompt files
6. Version control your prompt files to track changes over time
7. Consider organizing sections with clear headings for better readability
