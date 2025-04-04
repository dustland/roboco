# Test Structure for Roboco

This directory contains tests for the roboco application. Tests are organized into subdirectories by type.

## Directory Structure

- `tests/`: Main test directory
  - `unit/`: Unit tests for individual components
    - `test_api_models.py`: Tests for API models
    - `test_message.py`: Tests for Message model
    - `test_models.py`: Tests for the core models
    - `test_relationships.py`: Tests for model relationships
  - `db/`: Database integration tests
    - `test_project.py`: Tests for Project DB operations
  - `fixtures/`: Shared test fixtures
    - `utils.py`: Utility functions for tests
  - `conftest.py`: Global test configuration and fixtures

## Key Changes

1. **Removed Task Dependencies**:

   - Simplified the Task model by removing dependencies and subtasks
   - Removed the TaskDependencyLink model
   - Simplified relationship tracking to make AG2 integration easier

2. **Testing Infrastructure**:

   - Created consistent fixtures in conftest.py
   - Implemented clean testing approach with session isolation
   - Made tests independent of service layer for better isolation

3. **Simplified Database Access**:
   - Tests now directly use SQLModel/SQLAlchemy without service layer
   - Each test cleans up its own state

## Test Environment

- Uses SQLite in-memory database for testing
- Each test starts with a clean database state
- Database isolation is maintained between test modules

## Notes for Future Development

1. When adding new tests:

   - Use the existing fixtures in conftest.py
   - Follow the pattern of direct database access (not using service layer in tests)
   - Ensure tests clean up after themselves

2. Task dependencies and subtasks:

   - These have been temporarily removed to simplify AG2 integration
   - If reintroducing them, consider how they'll integrate with AG2

3. Important fixtures:
   - `db_session`: Provides an active database session
   - `clean_db`: Clears database tables before test
   - `test_engine`/`test_session`: Used for unit tests of models

## Running Tests

Currently, most tests are failing due to issues described in the "Current Issues" section.
However, some individual tests can be run successfully.

To run all tests:

```
pytest
```

To run a specific test file:

```
pytest tests/unit/test_api_models.py
```

To run tests with verbose output:

```
pytest -v
```

## Current Issues

There are several issues with the test suite after the separation of API models from core domain models:

1. **SQLAlchemy Model Registration**: Tests fail with `UnmappedClassError` because SQLModel tables are not properly initialized in the test environment. This happens when creating domain model instances directly in unit tests.

2. **Database Session Handling**: Tests fail with `DetachedInstanceError` due to sessions not being properly maintained between fixture creation and test execution. This is a common issue when using SQLAlchemy/SQLModel with pytest.

3. **API Model Validation**: Tests for MessageCreate model are failing validation.

4. **Database Engine/Session Management**: Multiple instances of the database engine and sessions are being created, causing objects to be detached from their sessions.

## Migration Notes

The codebase has been restructured to properly separate:

- Core domain models (in `src/roboco/core/models/`)
- API models (in `src/roboco/api/models/`)

API models now use Pydantic's BaseModel instead of SQLModel and include conversion methods:

- `to_db_model()`: Convert API model to domain/database model
- `from_db_model()`: Convert domain/database model to API response model

## Fixing the Tests

To fix the test suite, the following changes are needed:

1. **Single Database Engine**: Create a single database engine instance shared across all tests to ensure SQLModel metadata is properly initialized once.

2. **Improved Session Management**:

   - Use session-scoped fixtures for core database setup
   - Use function-scoped sessions for individual tests
   - Ensure proper rollback/cleanup between tests

3. **Test Isolation**: Add fixtures to clear database tables between tests to prevent test interactions.

4. **SQLModel Initialization**: Ensure SQLModel.metadata.create_all() is called at the right time to properly register all models.

The current approach uses a combination of these practices, but additional work is needed to fully resolve the issues.
