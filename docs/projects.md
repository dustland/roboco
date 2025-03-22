# Project Management

RoboCo includes a comprehensive project management system that allows you to organize your agent teams and job runs into structured projects. Each project can include:

- **Goals and descriptions** - Define what the project aims to accomplish
- **Sprints** - Time-boxed periods with specific objectives
- **Todo items** - Tasks to be completed within the project or sprint
- **Team assignments** - Connect teams with projects
- **Job tracking** - Link job runs to projects for better organization

## Project Structure

A project in RoboCo is represented by a directory containing:

- `todo.md` - A Markdown file showing all todos and their status
- `sprints/` - Directory of sprint-specific files and artifacts
- Custom directories for source code and documentation

## Using the Project API

The project management system is accessible through the RoboCo API server. Here are the key endpoints:

### Project Endpoints

- `GET /projects` - List all projects
- `POST /projects` - Create a new project
- `GET /projects/{project_id}` - Get project details
- `PATCH /projects/{project_id}` - Update a project
- `DELETE /projects/{project_id}` - Delete a project
- `GET /projects/{project_id}/todo.md` - Get project todo markdown

### Todo Endpoints

- `POST /projects/{project_id}/todos` - Create a todo item
- `PATCH /projects/{project_id}/todos/{todo_title}` - Update a todo item

### Sprint Endpoints

- `POST /projects/{project_id}/sprints` - Create a sprint
- `PATCH /projects/{project_id}/sprints/{sprint_name}` - Update a sprint

## Example Usage

You can reference the [project_example.py](../examples/api/project_example.py) script for a complete demonstration of:

1. Creating a project
2. Setting up sprints
3. Managing todo items
4. Associating jobs with the project

```python
# Example: Create a new project
project_data = {
    "name": "ML Research Project",
    "description": "Research and development of machine learning models",
    "teams": ["research_team"],
    "tags": ["machine-learning", "research"]
}
response = requests.post("http://localhost:8000/projects", json=project_data)
project_id = response.json()["id"]

# Example: Create a todo item
todo_data = {
    "title": "Review latest papers",
    "description": "Review recent papers on transformer models",
    "status": "TODO",
    "priority": "high"
}
requests.post(f"http://localhost:8000/projects/{project_id}/todos", json=todo_data)

# Example: Create a job linked to the project
job_data = {
    "team": "research_team",
    "query": "What are the latest advances in transformer models?",
    "project_id": project_id
}
requests.post("http://localhost:8000/jobs", json=job_data)
```

## Integrating with Teams

Projects can be associated with one or more teams, allowing the same team to work on multiple projects or multiple teams to collaborate on a single project. When creating a job, you can specify both a team and a project, connecting the work being done to the broader project structure.

## Todo Markdown Format

The `todo.md` file generated for each project follows a structured format:

```markdown
# Project: My Project Name

## Current Sprint: Sprint Name

Start Date: 2023-05-15 | End Date: 2023-05-29 | Status: active

## Todo Items

### In Progress

- [ ] Task name (Priority: high, Assigned: agent_name)
      Description of the task

### Todo

- [ ] Another task (Priority: medium)
      Description of the task

### Done

- [x] Completed task (Priority: low, Completed: 2023-05-18)
      Description of the task

## Upcoming Sprints

### Sprint Name 2

Start Date: 2023-05-30 | End Date: 2023-06-13 | Status: planned

- [ ] Future task (Priority: medium)
      Description of the task
```

This format makes it easy to track progress and is automatically updated when changes are made through the API.
