# AgentX REST API

A simple FastAPI-based REST API for task execution and memory management in the AgentX framework.

## Overview

The AgentX server provides a straightforward RESTful interface for:

- Creating and managing tasks
- Accessing task and agent memory
- Monitoring task execution status

## Quick Start

```python
from agentx.server import run_server

# Start the server
run_server(host="0.0.0.0", port=8000)
```

## API Endpoints

### Health Check

**GET** `/health`

Returns server health status and active task count.

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "version": "0.4.0",
  "active_tasks": 5
}
```

### Task Management

#### Create Task

**POST** `/tasks`

Create and start a new task.

Request body:

```json
{
  "config_path": "path/to/config.yaml",
  "task_description": "Write a research report on AI",
  "context": {
    "topic": "artificial intelligence",
    "length": "5000 words"
  }
}
```

Response:

```json
{
  "task_id": "task_123",
  "status": "pending",
  "created_at": "2024-01-01T12:00:00"
}
```

#### List Tasks

**GET** `/tasks`

List all tasks with their current status.

Response:

```json
[
  {
    "task_id": "task_123",
    "status": "running",
    "config_path": "path/to/config.yaml",
    "task_description": "Write a research report on AI",
    "context": { "topic": "artificial intelligence" },
    "created_at": "2024-01-01T12:00:00",
    "completed_at": null
  }
]
```

#### Get Task

**GET** `/tasks/{task_id}`

Get detailed information about a specific task.

Response:

```json
{
  "task_id": "task_123",
  "status": "completed",
  "result": {
    "output": "Research report content...",
    "agents_used": ["planner", "researcher", "writer"]
  },
  "error": null,
  "created_at": "2024-01-01T12:00:00",
  "completed_at": "2024-01-01T12:30:00"
}
```

#### Delete Task

**DELETE** `/tasks/{task_id}`

Delete a task and all its associated memory.

Response:

```json
{
  "message": "Task deleted successfully"
}
```

### Memory Management

#### Add Memory

**POST** `/tasks/{task_id}/memory`

Add content to task or agent memory.

Request body:

```json
{
  "task_id": "task_123",
  "agent_id": "researcher", // Optional: for agent-specific memory
  "content": "Important research finding about AI safety"
}
```

Response:

```json
{
  "task_id": "task_123",
  "agent_id": "researcher",
  "success": true
}
```

#### Search Memory

**GET** `/tasks/{task_id}/memory?query=search_term&agent_id=agent_name`

Search task or agent memory.

Query parameters:

- `query` (optional): Search term
- `agent_id` (optional): Agent ID for agent-specific memory

Response:

```json
{
  "task_id": "task_123",
  "agent_id": "researcher",
  "success": true,
  "data": [
    {
      "content": "Research finding about AI safety",
      "timestamp": "2024-01-01T12:15:00"
    }
  ]
}
```

#### Clear Memory

**DELETE** `/tasks/{task_id}/memory?agent_id=agent_name`

Clear task or agent memory.

Query parameters:

- `agent_id` (optional): Agent ID for agent-specific memory clearing

Response:

```json
{
  "message": "Memory cleared successfully"
}
```

## Task Status Values

- `pending`: Task created but not yet started
- `running`: Task is currently executing
- `completed`: Task finished successfully
- `failed`: Task encountered an error

## Usage Examples

### Python Client

```python
import requests

# Create a task
response = requests.post("http://localhost:8000/tasks", json={
    "config_path": "config/team.yaml",
    "task_description": "Analyze market trends",
    "context": {"market": "technology"}
})
task_id = response.json()["task_id"]

# Check task status
status = requests.get(f"http://localhost:8000/tasks/{task_id}")
print(status.json())

# Search task memory
memory = requests.get(f"http://localhost:8000/tasks/{task_id}/memory?query=trends")
print(memory.json())
```

### cURL Examples

```bash
# Create task
curl -X POST "http://localhost:8000/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "config_path": "config/team.yaml",
    "task_description": "Write a blog post",
    "context": {"topic": "AI trends"}
  }'

# Get task status
curl "http://localhost:8000/tasks/task_123"

# Add memory
curl -X POST "http://localhost:8000/tasks/task_123/memory" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "task_123",
    "agent_id": "writer",
    "content": "Key insight about AI trends"
  }'

# Search memory
curl "http://localhost:8000/tasks/task_123/memory?query=trends&agent_id=writer"
```

## Configuration

The server can be configured when starting:

```python
from agentx.server import run_server

run_server(
    host="0.0.0.0",      # Host to bind to
    port=8000,           # Port to bind to
    reload=True,         # Enable auto-reload for development
    log_level="info"     # Logging level
)
```

## Error Handling

The API returns standard HTTP status codes:

- `200`: Success
- `400`: Bad request (invalid parameters)
- `404`: Resource not found (task doesn't exist)
- `500`: Internal server error

Error responses include details:

```json
{
  "detail": "Task not found"
}
```
