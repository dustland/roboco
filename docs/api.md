# API Server

RoboCo includes a RESTful API server that allows you to interact with the system programmatically. The API server provides endpoints for:

1. Managing agent teams and jobs
2. Retrieving job status and results
3. Managing projects, todos, and sprints
4. Accessing generated artifacts

## Starting the API Server

You can start the API server using the provided CLI:

```bash
# Using the CLI directly
python -m roboco server

# With custom options
python -m roboco server --host 0.0.0.0 --port 9000 --reload

# Using the convenience script (for development)
./start.sh
```

By default, the server runs on `localhost:8000`.

## API Endpoints

### Team Management

- `GET /teams` - List all available teams
- `GET /teams/{team_key}` - Get details about a specific team

### Job Management

- `POST /jobs` - Create a new job
- `GET /jobs` - List all jobs
- `GET /jobs/{job_id}` - Get job status
- `GET /jobs/{job_id}/artifacts` - List job artifacts
- `GET /jobs/{job_id}/artifacts/{artifact_path}` - Get a specific artifact

### Project Management

See the [Project Management](projects.md) documentation for detailed information about project-related endpoints.

## Example API Usage

### Create a New Job

```python
import requests

# Create a new job
job_data = {
    "team": "research_team",
    "query": "What are the latest advances in transformer models?",
    "initial_agent": "ai_researcher"
}

response = requests.post("http://localhost:8000/jobs", json=job_data)
job = response.json()
job_id = job["job_id"]

print(f"Created job with ID: {job_id}")
```

### Check Job Status

```python
# Check job status
response = requests.get(f"http://localhost:8000/jobs/{job_id}")
status = response.json()

print(f"Job status: {status['status']}")
print(f"Progress: {status['progress']}")
```

### List Job Artifacts

```python
# List artifacts
response = requests.get(f"http://localhost:8000/jobs/{job_id}/artifacts")
artifacts = response.json()

for artifact in artifacts:
    print(f"Artifact: {artifact['name']} ({artifact['type']})")
    print(f"Path: {artifact['path']}")
    print(f"Size: {artifact['size']} bytes")
```

## Authentication

Currently, the API server does not include authentication. For production use, consider adding authentication middleware or using an API gateway.

## Webhooks (Future)

In future versions, the API may support webhooks for event-driven integrations, such as job completion notifications.

## Client Libraries

For a comprehensive example client implementation, see:

- [client_example.py](../examples/api/client_example.py) - Job management example
- [project_example.py](../examples/api/project_example.py) - Project management example

These examples demonstrate how to interact with the API in Python.
