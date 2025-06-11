# RoboCo Server

Multi-user server implementation with session management and context isolation.

## Overview

The RoboCo server provides a REST API for running multi-agent collaborations with complete session isolation. Each session gets its own:

- Context store (isolated memory)
- Event bus (isolated events)
- Team instances (isolated agents)
- Collaboration history

This makes it perfect for:

- **Multi-user environments** - Each user gets isolated sessions
- **Web applications** - Easy HTTP API integration
- **Concurrent collaborations** - Multiple teams can work simultaneously
- **Session management** - Automatic cleanup and resource management

## Quick Start

### 1. Start the Server

```bash
# Using uv (recommended)
uv run dev server

# Or using the server command directly
uv run server

# Or programmatically
python -c "from roboco.server.api import run_server; run_server()"
```

The server starts on `http://localhost:8000` by default.

### 2. Create a Session

```bash
curl -X POST "http://localhost:8000/sessions" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123"}'
```

Response:

```json
{
  "session_id": "uuid-here",
  "status": "active",
  "created_at": "2024-01-01T12:00:00Z",
  "user_id": "user123",
  "total_requests": 0,
  "total_collaborations": 0,
  "context_entries": 0
}
```

### 3. Save Context Data

```bash
curl -X POST "http://localhost:8000/context" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "operation": "save",
    "key": "project_info",
    "data": {"name": "My Project", "version": "1.0"}
  }'
```

### 4. Start a Collaboration

```bash
curl -X POST "http://localhost:8000/collaborations" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "team_config_path": "examples/superwriter/config/team.yaml",
    "task": "Write a blog post about AI collaboration",
    "context": {"style": "professional", "length": "medium"}
  }'
```

## API Endpoints

### Session Management

- `POST /sessions` - Create new session
- `GET /sessions` - List sessions (with optional filtering)
- `GET /sessions/{id}` - Get session info
- `DELETE /sessions/{id}` - Delete session
- `GET /sessions/{id}/stats` - Get session statistics

### Context Operations

- `POST /context` - Save/load/list/delete context data

### Collaborations

- `POST /collaborations` - Start collaboration (async)
- `GET /collaborations/{id}` - Get collaboration status
- `POST /collaborations/stream` - Start streaming collaboration

### Health & Monitoring

- `GET /health` - Health check and server stats

## Configuration

### Session Configuration

```python
from roboco.server import SessionConfig
from datetime import timedelta

config = SessionConfig(
    max_idle_time=timedelta(hours=2),    # Session expires after 2h idle
    max_session_time=timedelta(hours=8), # Max 8h total session time
    auto_cleanup=True,                   # Auto-cleanup expired sessions
    context_limit=1000                   # Max context entries per session
)
```

### Server Configuration

```python
from roboco.server import create_app

app = create_app(
    title="My RoboCo Server",
    description="Custom multi-agent server",
    enable_cors=True  # Enable CORS for web apps
)
```

## Direct Python Usage

You can also use the server components directly in Python:

```python
import asyncio
from roboco.server import SessionManager, SessionConfig

async def main():
    # Create session manager
    config = SessionConfig(max_idle_time=3600)
    manager = SessionManager(config)
    await manager.start()

    try:
        # Create session
        session_info = await manager.create_session(user_id="python_user")

        # Use session with context manager
        async with manager.session_context(session_info.session_id) as session:
            # Save context
            await session.context_store.save("key", {"data": "value"})

            # Start collaboration
            result = await session.team_manager.collaborate(
                "path/to/team.yaml",
                "Generate a haiku about coding"
            )
            print(f"Result: {result}")

    finally:
        await manager.stop()

asyncio.run(main())
```

## Examples

### Web Integration

```javascript
// Create session
const sessionResponse = await fetch("/sessions", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ user_id: "web_user_123" }),
});
const session = await sessionResponse.json();

// Start collaboration
const collabResponse = await fetch("/collaborations", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    session_id: session.session_id,
    team_config_path: "config/creative_team.yaml",
    task: "Write a product description for our new app",
  }),
});
const collaboration = await collabResponse.json();

// Poll for results
const checkResult = async () => {
  const result = await fetch(
    `/collaborations/${collaboration.collaboration_id}?session_id=${session.session_id}`
  );
  return await result.json();
};
```

### Streaming Collaboration

```python
import aiohttp
import asyncio

async def stream_collaboration():
    async with aiohttp.ClientSession() as session:
        # Start streaming collaboration
        data = {
            'session_id': 'your-session-id',
            'team_config_path': 'config/team.yaml',
            'task': 'Generate creative content'
        }

        async with session.post('/collaborations/stream', json=data) as resp:
            async for line in resp.content:
                if line.startswith(b'data: '):
                    event_data = line[6:].decode().strip()
                    print(f"Event: {event_data}")

asyncio.run(stream_collaboration())
```

## Demo Script

Run the included demo to see the server in action:

```bash
# Start server in one terminal
uv run dev server

# Run demo in another terminal
python examples/server_demo.py

# Or run direct Python API demo
python examples/server_demo.py direct
```

## Architecture

```
┌─────────────────┐
│   FastAPI App   │
├─────────────────┤
│ Session Manager │
├─────────────────┤
│   Session 1     │ ← Isolated context, events, agents
│   Session 2     │ ← Isolated context, events, agents
│   Session N     │ ← Isolated context, events, agents
└─────────────────┘
```

Each session contains:

- `InMemoryContextStore` - Isolated context storage
- `InMemoryEventBus` - Isolated event handling
- `TeamManager` - Isolated agent teams
- Session metadata and statistics

## Benefits

✅ **Complete Isolation** - Sessions don't interfere with each other  
✅ **Automatic Cleanup** - Expired sessions are cleaned up automatically  
✅ **Resource Management** - Configurable limits and timeouts  
✅ **RESTful API** - Easy integration with any language/framework  
✅ **Streaming Support** - Real-time collaboration events  
✅ **Optional** - Use direct framework if you don't need multi-user support

Perfect for building:

- Multi-user web applications
- API services
- Microservices architectures
- Development environments
- Production deployments
