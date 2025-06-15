# AgentX Test Suite

This directory contains comprehensive tests for the AgentX framework, organized following pytest best practices.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests
│   └── core/               # Core component tests
│       ├── test_brain.py   # Brain and message handling (22 tests)
│       ├── test_task.py    # Task lifecycle and management (17 tests)
│       ├── test_memory.py  # Memory operations and storage (27 tests)
│       ├── test_event.py   # Event system and bus (20 tests)
│       ├── test_team.py    # Team conversation management (29 tests)
│       └── test_agent.py   # Agent coordination (15 tests - needs update)
├── integration/            # Integration tests (planned)
└── performance/            # Performance tests (planned)
```

## Current Test Status

✅ **115 tests passing** across core components:

- **Brain & Message System**: 22/22 tests passing
- **Task Management**: 17/17 tests passing
- **Memory System**: 27/27 tests passing
- **Event System**: 20/20 tests passing
- **Team Management**: 29/33 tests passing (4 minor fixes needed)
- **Agent System**: 0/15 tests passing (needs API update)

## Running Tests

### All Tests

```bash
uv run pytest tests/
```

### Core Component Tests (Working)

```bash
uv run pytest tests/unit/core/test_brain.py tests/unit/core/test_task.py tests/unit/core/test_memory.py tests/unit/core/test_event.py
```

### Specific Component

```bash
uv run pytest tests/unit/core/test_brain.py -v
```

### With Coverage

```bash
uv run pytest tests/ --cov=src/agentx --cov-report=html
```

## Test Features

### Comprehensive Coverage

- **Configuration Testing**: Default and custom configurations for all components
- **Lifecycle Testing**: Creation, initialization, state transitions, and cleanup
- **Error Handling**: Robust failure scenarios and edge cases
- **Async Support**: Full async/await testing for Brain operations
- **Mocking**: External services (LLM APIs) properly mocked
- **Integration**: Component interaction and data flow testing

### Test Infrastructure

- **Shared Fixtures**: Reusable test components in `conftest.py`
- **Modern Tooling**: pytest + pytest-asyncio + pytest-cov
- **Proper Isolation**: No real API calls in unit tests
- **Fast Execution**: 115 tests run in ~1.2 seconds

## Key Test Categories

### Brain System Tests

- BrainConfig validation (default/custom values, DeepSeek integration)
- Message creation, serialization, and OpenAI format conversion
- ChatHistory management with limits and clearing
- Brain thinking processes with LLM integration
- Tool reasoning and memory integration
- Error handling and recovery

### Task Management Tests

- TaskConfig creation and validation
- Task lifecycle (start/stop/delete operations)
- Status transitions and metadata handling
- Event registration and handling
- Chat session management

### Memory System Tests

- MemoryItem creation and serialization
- Memory storage (sync/async with backend fallback)
- Semantic search and retrieval
- Memory cleanup and importance scoring
- Statistics and context generation
- Conversation summaries and learning storage

### Event System Tests

- Event creation and serialization
- EventBus listener registration/unregistration
- Synchronous and asynchronous event emission
- Event history management and cleanup
- Global event bus singleton pattern
- Error handling in event callbacks

### Team Management Tests

- TeamConfig and speaker selection methods
- Agent management (add/remove/validation)
- Conversation flow and round management
- Speaker selection algorithms (round-robin, random, custom)
- Termination conditions and history management
- Team statistics and summaries

## Next Steps

### Immediate Fixes Needed

1. **Agent Tests**: Update test_agent.py to use current Agent API (AgentConfig-based)
2. **Team Tests**: Fix 4 failing tests related to mock objects and method signatures
3. **Import Issues**: Resolve memory_tools.py import to use Memory instead of TaskMemory

### Future Expansion

1. **Integration Tests**: Multi-component workflows and real API integration
2. **Performance Tests**: Load testing and benchmarking
3. **Tool System Tests**: Comprehensive tool registry and execution testing
4. **Server Tests**: FastAPI endpoints and WebSocket connections
5. **Search Tests**: Search backend integration and indexing
6. **Config Tests**: Configuration loading and validation

### Test Quality Improvements

1. **Property-Based Testing**: Use Hypothesis for edge case generation
2. **Mutation Testing**: Verify test quality with mutation testing
3. **Contract Testing**: API contract validation
4. **End-to-End Tests**: Full workflow testing with real components

## Dependencies

The test suite uses:

- `pytest`: Test framework
- `pytest-asyncio`: Async test support
- `pytest-cov`: Coverage reporting
- `unittest.mock`: Mocking and patching

Install with:

```bash
uv add --dev pytest pytest-cov pytest-asyncio
```

## Contributing

When adding new tests:

1. Follow the existing naming conventions
2. Use appropriate fixtures from `conftest.py`
3. Mock external dependencies
4. Include both success and failure scenarios
5. Add docstrings explaining test purpose
6. Ensure tests are fast and isolated

## Test Philosophy

Our testing approach emphasizes:

- **Fast Feedback**: Quick test execution for rapid development
- **Comprehensive Coverage**: Testing all code paths and edge cases
- **Realistic Scenarios**: Tests that reflect actual usage patterns
- **Maintainable Code**: Clear, well-documented test code
- **Reliable Results**: Consistent, deterministic test outcomes
