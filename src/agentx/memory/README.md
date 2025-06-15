# Memory Backend System

The memory backend system provides a pluggable architecture for sophisticated memory management in AgentX agents. It separates the simple memory interface used by agents from complex backend implementations.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Core Memory   │───▶│  Memory Backend  │───▶│  Mem0 Backend   │
│   (Simple API)  │    │   (Interface)    │    │ (Implementation)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Key Components

### MemoryBackend Interface

Abstract interface defining clean, concise methods:

```python
from agentx.memory import MemoryBackend, MemoryQuery, MemoryType

class MemoryBackend(ABC):
    async def add(self, content: str, memory_type: MemoryType,
                  agent_name: str, metadata: dict = None,
                  importance: float = 1.0) -> str

    async def query(self, query: MemoryQuery) -> MemorySearchResult
    async def search(self, query: MemoryQuery) -> MemorySearchResult
    async def get(self, memory_id: str) -> Optional[MemoryItem]
    async def update(self, memory_id: str, **kwargs) -> bool
    async def delete(self, memory_id: str) -> bool
    async def clear(self, agent_name: str = None) -> int
    async def count(self, **filters) -> int
    async def stats(self) -> MemoryStats
    async def health(self) -> Dict[str, Any]
```

### Method Names

The methods use clean, concise names without redundant prefixes:

- `add()` instead of `add_memory()`
- `query()` instead of `query_memory()`
- `search()` instead of `search_memory()`
- `get()` instead of `get_memory()`
- `update()` instead of `update_memory()`
- `delete()` instead of `delete_memory()`
- `clear()` instead of `clear_memory()`
- `count()` instead of `count_memory()`
- `stats()` instead of `get_stats()`
- `health()` instead of `health_check()`

This makes the methods suitable for direct registration as agent functions without redundant naming.

### Mem0Backend Implementation

Full-featured implementation using Mem0 for:

- **Semantic Search**: Vector-based content retrieval
- **Intelligent Storage**: Automatic fact extraction and relationship mapping
- **Multi-modal Support**: Text, conversations, insights, learnings
- **Metadata Filtering**: Rich query capabilities
- **Performance Monitoring**: Query timing and statistics
- **Health Checks**: Backend connectivity and status

### Data Models

Rich type system for memory operations:

```python
@dataclass
class MemoryItem:
    content: str
    memory_type: MemoryType
    agent_name: str
    timestamp: datetime
    memory_id: str
    metadata: Dict[str, Any]
    importance: float
    version: Optional[int] = None
    parent_id: Optional[str] = None

@dataclass
class MemoryQuery:
    query: str
    agent_name: str
    limit: int = 10
    memory_type: Optional[MemoryType] = None
    metadata_filter: Optional[Dict[str, Any]] = None
    importance_threshold: Optional[float] = None
    include_content: bool = True
```

## Usage Examples

### Basic Usage

```python
from agentx.memory import create_memory_backend, MemoryQuery, MemoryType
from agentx.config.models import MemoryConfig

# Create backend
config = MemoryConfig()
backend = create_memory_backend(config)

# Add memory
memory_id = await backend.add(
    content="Tesla's market share is growing",
    memory_type=MemoryType.TEXT,
    agent_name="researcher",
    metadata={"topic": "tesla", "source": "report"},
    importance=0.9
)

# Query for content
query = MemoryQuery(
    query="Tesla market trends",
    agent_name="researcher",
    limit=5
)
results = await backend.query(query)

# Search with filters
search_query = MemoryQuery(
    query="technology",
    metadata_filter={"topic": "technology"},
    limit=10
)
search_results = await backend.search(search_query)
```

### Core Memory Integration

```python
from agentx.core.memory import Memory
from agentx.config.models import MemoryConfig

# Create memory with backend
agent = MyAgent("researcher")
config = MemoryConfig()
memory = Memory(agent, config)

# Use async methods for backend features
memory_id = await memory.save_async(
    "AI agents need sophisticated memory",
    metadata={"type": "insight"},
    importance=0.9
)

results = await memory.search_async("AI memory", limit=5)
```

### Agent Function Registration

The clean method names make them suitable for direct agent function registration:

```python
# Register memory functions with agent
agent.register_function("add", backend.add)
agent.register_function("query", backend.query)
agent.register_function("search", backend.search)
agent.register_function("get", backend.get)
agent.register_function("update", backend.update)
agent.register_function("delete", backend.delete)
agent.register_function("count", backend.count)
agent.register_function("stats", backend.stats)

# Agent can now call: add(), query(), search(), etc.
```

## Query vs Search Operations

- **`query()`**: Content-focused retrieval for LLM consumption

  - Returns full content with token limits
  - Optimized for semantic similarity
  - Used when agent needs actual content

- **`search()`**: Discovery and filtering operations
  - Returns metadata and references
  - Used for navigation and organization
  - Lighter weight for exploration

## Configuration

Memory backends are configured through `MemoryConfig`:

```python
from agentx.config.models import MemoryConfig

config = MemoryConfig(
    backend_type="mem0",
    vector_store={
        "provider": "chroma",
        "config": {"path": "./memory_db"}
    },
    llm={
        "provider": "openai",
        "config": {"model": "gpt-4"}
    },
    embedder={
        "provider": "openai",
        "config": {"model": "text-embedding-ada-002"}
    }
)
```

## Benefits

1. **Clean Interface**: Simple methods without redundant naming
2. **Pluggable Architecture**: Easy to swap backend implementations
3. **Backward Compatibility**: Existing code continues to work
4. **Rich Functionality**: Full Mem0 capabilities when needed
5. **Performance**: Async operations with monitoring
6. **Type Safety**: Rich data models and type hints
7. **Agent Integration**: Methods suitable for direct function registration

## Installation

```bash
# Install with Mem0 support
pip install mem0ai

# Or install basic version
pip install agentx
```
