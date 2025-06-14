# Roboco Observability

Built-in observability features for monitoring, debugging, and analyzing multi-agent framework operations.

## Quick Start

Start the observability system:

```bash
# CLI interface (default)
roboco monitor

# Web dashboard interface
roboco monitor --web
```

The web dashboard launches a modern FastAPI + Preline UI interface at `http://localhost:8501` with real-time monitoring capabilities.

## Features

### 🎯 Modern Web Dashboard

- **Dashboard**: System overview with metrics cards and recent activity
- **Tasks**: Task conversation history viewer with export functionality
- **Events**: Real-time event monitoring with filtering and auto-refresh
- **Memory**: Memory browser with categories, search, and detailed views
- **Messages**: Agent conversation history during task execution
- **Configuration**: System configuration viewer showing LLM models, agents, tools

### 📊 Metrics Collection

- **Brain Metrics**: Thinking time, reasoning steps, model usage
- **Tool Metrics**: Execution time, success rates, usage patterns
- **Memory Metrics**: Operations, search performance, storage stats
- **Team Metrics**: Collaboration patterns, speaker changes
- **Task Metrics**: Execution time, completion rates, failures

### 🔍 Event Tracking

- **Comprehensive Events**: All agent, brain, tool, and team activities
- **Real-time Streaming**: Live event feed with Server-Sent Events
- **Event History**: Searchable history with filtering capabilities
- **Custom Events**: Support for application-specific events

### 📈 Performance Analysis

- **Health Monitoring**: System status with degradation detection
- **Performance Summaries**: Key metrics and trends
- **Error Tracking**: Failure rates and error patterns
- **Resource Usage**: Memory and processing insights

## Architecture

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Dashboard │    │   Monitor       │    │   Collectors    │
│   (FastAPI +    │◄───┤   (Core)        │◄───┤   (Data)        │
│   Preline UI)   │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Event Bus     │    │   CLI Interface │
                       │   (Global)      │    │   (Terminal)    │
                       └─────────────────┘    └─────────────────┘
```

### Event System Integration

The observability system integrates seamlessly with Roboco's event system:

- **Automatic Collection**: Events are automatically captured from all framework components
- **Zero Configuration**: Works out-of-the-box with existing agents and teams
- **Non-intrusive**: No code changes required in your agents or workflows

## Usage Examples

### Basic Monitoring

```python
from roboco.observability.monitor import get_monitor

# Get the global monitor instance
monitor = get_monitor()
monitor.start()

# Your agent code runs normally
# Events are automatically captured

# Get dashboard data
dashboard_data = monitor.get_dashboard_data()
print(f"Mode: {dashboard_data['mode']}")
print(f"Tasks: {dashboard_data['total_tasks']}")
print(f"Memory items: {dashboard_data['total_memory_items']}")

# Get recent tasks
recent_tasks = monitor.get_recent_tasks(10)
print(f"Recent tasks: {recent_tasks}")
```

### Custom Event Tracking

```python
from roboco.core.event import global_events

# Emit custom events
global_events.emit("custom.workflow.started", {
    "workflow_id": "analysis_001",
    "user": "researcher"
}, source="workflow_manager")

global_events.emit("custom.workflow.completed", {
    "workflow_id": "analysis_001",
    "duration_ms": 5000,
    "results_count": 42
}, source="workflow_manager")
```

### Web Dashboard API

The web dashboard provides HTMX API endpoints:

```bash
# Dashboard statistics
curl http://localhost:8501/api/dashboard-stats

# Task conversation history
curl http://localhost:8501/api/task/{task_id}/conversation

# Events with filtering
curl http://localhost:8501/api/events?event_type=tool&limit=50

# Memory search
curl http://localhost:8501/api/memory/search?q=search_term

# Memory by category
curl http://localhost:8501/api/memory/category/user_preferences

# Messages tasks
curl http://localhost:8501/api/messages/tasks

# Messages conversation
curl http://localhost:8501/api/messages/conversation/{task_id}
```

## Dashboard Features

### Dashboard Page

- **System Metrics**: Total tasks, memory items, events, and data directory status
- **Recent Activity**: Latest task executions and system events
- **Quick Actions**: Start/stop monitor, refresh data, export functionality
- **Professional UI**: Modern Preline UI components with light/dark theme toggle

### Tasks Page

- **Task History**: Complete list of executed tasks with timestamps
- **Conversation Export**: Download task conversation history as JSON
- **Task Details**: View individual task execution details
- **Search & Filter**: Find specific tasks by ID or content

### Events Page

- **Real-time Events**: Live event stream with auto-refresh (integrated mode only)
- **Event Filtering**: Filter by event type (tool, memory, system, etc.)
- **Event History**: Browse historical events with pagination
- **Event Details**: Detailed view of event data and metadata

### Memory Page

- **Memory Categories**: Browse memory by category (user_preferences, facts, etc.)
- **Memory Search**: Full-text search across all memory items
- **Memory Details**: View individual memory items with metadata
- **Memory Statistics**: Count and distribution of memory items

### Messages Page

- **Task Conversations**: View agent-to-agent conversations during task execution
- **Message Filtering**: Filter by message type (messages, tools, errors, system)
- **Conversation Export**: Export conversation history as JSON
- **Auto-scroll**: Automatic scrolling to latest messages

### Configuration Page

- **System Information**: Runtime environment and configuration details
- **LLM Models**: Configured language models and API key status
- **Agent Configuration**: Active agents and their settings
- **Tools & Memory**: Available tools and memory configuration

## Configuration

### Command Line Options

```bash
# Start CLI monitor
roboco monitor

# Start web dashboard
roboco monitor --web

# Custom port for web dashboard
roboco monitor --web --port 8502

# Custom host for web dashboard
roboco monitor --web --host 127.0.0.1

# Start API server with observability
roboco start --port 8000 --host 0.0.0.0
```

### Programmatic Configuration

```python
from roboco.observability.monitor import get_monitor, ObservabilityMonitor

# Get the global monitor instance
monitor = get_monitor()

# Create custom monitor (advanced usage)
custom_monitor = ObservabilityMonitor()
custom_monitor.start()

# Access monitor data
dashboard_data = monitor.get_dashboard_data()
recent_tasks = monitor.get_recent_tasks(limit=20)
memory_categories = monitor.get_memory_categories()
```

## Data Export

### Built-in Export Features

- **Task Conversations**: Export individual task conversation history as JSON
- **Messages History**: Export agent conversation history as JSON
- **Dashboard Data**: Export complete dashboard state via CLI
- **Memory Data**: Export memory items by category

### Export Examples

```python
from roboco.observability.monitor import get_monitor
import json
from datetime import datetime

# Get monitor instance
monitor = get_monitor()

# Export task conversation
task_id = "task_123"
conversation = monitor.get_task_conversation(task_id)
with open(f"conversation_{task_id}.json", 'w') as f:
    json.dump(conversation, f, indent=2, default=str)

# Export all dashboard data
dashboard_data = monitor.get_dashboard_data()
export_data = {
    "dashboard": dashboard_data,
    "tasks": {task_id: monitor.get_task_conversation(task_id)
             for task_id in monitor.get_recent_tasks(50)},
    "memory_categories": {cat: monitor.get_memory_by_category(cat)
                         for cat in monitor.get_memory_categories()},
    "exported_at": datetime.now().isoformat()
}

filename = f"roboco_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(filename, 'w') as f:
    json.dump(export_data, f, indent=2, default=str)
```

## CLI Interface

### Monitor Commands

The CLI monitor provides an interactive interface for observability:

```bash
# Start CLI monitor
roboco monitor

# Available commands in CLI:
monitor> status    # Show monitor status
monitor> tasks     # Show recent tasks
monitor> memory    # Show memory categories
monitor> search <query>  # Search memory
monitor> export    # Export all data to JSON
monitor> refresh   # Refresh data from API
monitor> web       # Start web interface
monitor> quit      # Stop monitor and exit
```

### Integration with Roboco Server

```python
# The observability system integrates with the main API server
# Start server with integrated observability
roboco start

# Server provides observability endpoints at:
# http://localhost:8000/monitor - Redirect to dashboard
# http://localhost:8000/monitor/status - Monitor status
# http://localhost:8000/monitor/tasks/{task_id}/conversation - Task conversation
# http://localhost:8000/monitor/events - Events API
# http://localhost:8000/monitor/memory - Memory API
```

### Custom Event Integration

```python
from roboco.core.event import global_events

# Custom event handler
@global_events.on("tool.completed")
def handle_tool_completion(event):
    print(f"Tool {event.data['tool_name']} completed in {event.data['duration_ms']}ms")

# Emit custom events
global_events.emit("custom.workflow.started", {
    "workflow_id": "analysis_001",
    "user": "researcher"
}, source="workflow_manager")
```

## Troubleshooting

### Common Issues

**Web dashboard not starting:**

```bash
# Check if FastAPI and dependencies are installed
uv add fastapi uvicorn jinja2 python-multipart

# Check port availability
lsof -i :8501

# Start with custom port
roboco monitor --web --port 8502
```

**No data appearing:**

```python
# Ensure monitor is started
from roboco.observability.monitor import get_monitor
monitor = get_monitor()
monitor.start()  # Don't forget this!

# Check if data exists
dashboard_data = monitor.get_dashboard_data()
print(f"Tasks: {dashboard_data['total_tasks']}")
print(f"Memory items: {dashboard_data['total_memory_items']}")
```

**CLI commands not working:**

```bash
# Check if roboco CLI is properly installed
roboco --help

# Check monitor status
roboco status

# Try starting monitor in CLI mode
roboco monitor
```

### Data Directory Location

The observability system intelligently locates the data directory using this search order:

1. **Current directory**: `./roboco_data`
2. **Parent directories**: Searches up to 3 levels for existing `roboco_data`
3. **User home**: `~/.roboco/data` (if exists)
4. **Default**: Creates `./roboco_data` in current directory

This means you can run `roboco monitor --web` from any subdirectory of your project and it will find the correct data directory.

**Manual data directory specification:**

```bash
# Specify custom data directory
roboco monitor --data-dir /path/to/your/roboco_data
roboco monitor --web --data-dir /path/to/your/roboco_data
```

**Web Interface Data Directory Management:**

The web dashboard includes a comprehensive data directory management interface:

- **Current Directory Display**: Shows the active data directory path with copy and open buttons
- **Directory Information**: Real-time stats including file count, size, and last modified time
- **Change Directory**: Interactive form to specify a new data directory path
- **Directory Validation**: Automatic validation and creation of new directories
- **Live Updates**: Refresh functionality to update directory information

Access this feature at: `http://localhost:8501/configuration` → Data Directory Management section.

### Performance Considerations

- **Memory Usage**: Monitor stores task conversations and memory data in memory
- **Data Persistence**: Data is persisted to `roboco_data/` directory as JSON files
- **Web Dashboard**: Uses HTMX for efficient partial page updates
- **Real-time Events**: Only available in integrated mode (when using `roboco start`)

### Best Practices

1. **Use integrated mode** (`roboco start`) for real-time event monitoring
2. **Export data regularly** using CLI export or web dashboard export features
3. **Monitor memory usage** in long-running applications
4. **Use CLI interface** for automated monitoring and scripting
5. **Leverage web dashboard** for interactive analysis and debugging

## API Reference

### ObservabilityMonitor

```python
class ObservabilityMonitor:
    def start() -> None
    def stop() -> None
    def get_dashboard_data() -> Dict[str, Any]
    def get_recent_tasks(limit: int = 10) -> List[str]
    def get_task_conversation(task_id: str) -> List[Dict[str, Any]]
    def get_memory_categories() -> List[str]
    def get_memory_by_category(category: str) -> List[Dict[str, Any]]
    def search_memory(query: str) -> Dict[str, Any]
    def get_events(event_type: str = None, limit: int = 100) -> List[Dict[str, Any]]
    def get_event_summary() -> Dict[str, Any]
    def get_configuration_data() -> Dict[str, Any]
```

### Global Monitor Access

```python
from roboco.observability.monitor import get_monitor

# Get the singleton monitor instance
monitor = get_monitor()

# Get monitor with custom data directory
monitor = get_monitor(data_dir="/path/to/custom/data")
```

### Data Directory Management API

```python
# Get data directory information
GET /api/data-directory/info
# Returns: {"exists": bool, "path": str, "file_count": int, "size_mb": float, "last_modified": str, "files": []}

# Change data directory
POST /api/data-directory/change
# Body: {"path": "/new/data/directory"}
# Returns: {"success": bool, "message": str, "new_path": str}

# Browse directories (for future file picker implementation)
GET /api/data-directory/browse?path=/some/path
# Returns: {"current_path": str, "parent_path": str, "directories": []}
```

### Event System

```python
# Global event bus
from roboco.core.event import global_events

global_events.emit(event_type: str, data: Dict[str, Any], source: str)
global_events.on(event_type: str, callback: Callable[[Event], None])
```

## Contributing

The observability system is designed to be extensible:

1. **Custom Event Handlers**: Add new event processing logic
2. **Dashboard Pages**: Extend the FastAPI + Preline UI interface
3. **CLI Commands**: Add new monitor CLI commands
4. **Data Exporters**: Support additional output formats
5. **Memory Viewers**: Custom memory data visualization

### File Structure

```
src/roboco/observability/
├── monitor.py          # Core monitoring logic
├── web_app.py          # FastAPI web dashboard
├── memory_viewer.py    # Memory data access
├── templates/          # Jinja2 templates
│   ├── base.jinja2     # Base template with Preline UI
│   ├── dashboard.jinja2 # Main dashboard
│   ├── tasks.jinja2    # Task history
│   ├── events.jinja2   # Event monitoring
│   ├── memory.jinja2   # Memory browser
│   ├── messages.jinja2 # Agent conversations
│   └── configuration.jinja2 # System config
└── static/             # Static assets (logo, etc.)
```

See the source code in `src/roboco/observability/` for implementation details.
