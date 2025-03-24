# Roboco Object Model

This document describes the high-level object model and architecture of the Roboco system, focusing on the relationships between components rather than specific implementations.

## System Architecture

Roboco follows Domain-Driven Design principles with a clear separation of concerns across different layers:

```mermaid
flowchart TB
    subgraph Interface["Interface Layer"]
        API_Routes["API Routes"]
        API_Schemas["API Schemas"]
        CLI["Command Line Tools"]
    end
    
    subgraph Application["Application Layer"]
        Project_Service["Project Service"]
        Agent_Service["Agent Service"]
        Task_Service["Task Service"]
        API_Service["API Service"]
    end
    
    subgraph Core["Core Layer"]
        Models["Models"]
        Repositories["Repositories\n(Interfaces)"]
        Schema["Schema Definitions"]
    end
    
    subgraph Infrastructure["Infrastructure Layer"]
        Repo_Impl["Repository Impl"]
        External_APIs["External APIs"]
        Adapters["Adapters"]
    end
    
    Interface --> Application
    Application --> Core
    Core --> Infrastructure
```

## Core Domain Objects

### Project Management Domain

```mermaid
classDiagram
    Project "1" --> "*" Sprint
    Sprint "1" --> "*" TodoItem
    Project --> ProjectStatus
    Sprint --> SprintStatus
    TodoItem --> TodoStatus
    
    class Project {
        +id: str
        +name: str
        +description: str
        +status: ProjectStatus
        +created_at: datetime
        +updated_at: datetime
    }
    
    class Sprint {
        +id: str
        +project_id: str
        +name: str
        +description: str
        +status: SprintStatus
        +start_date: datetime
        +end_date: datetime
    }
    
    class TodoItem {
        +id: str
        +sprint_id: str
        +title: str
        +description: str
        +status: TodoStatus
        +assigned_to: str
        +priority: int
    }
    
    class ProjectStatus {
        <<enumeration>>
        PLANNING
        ACTIVE
        COMPLETED
        ARCHIVED
    }
    
    class SprintStatus {
        <<enumeration>>
        PLANNED
        IN_PROGRESS
        COMPLETED
        CANCELLED
    }
    
    class TodoStatus {
        <<enumeration>>
        TODO
        IN_PROGRESS
        REVIEW
        DONE
    }
```

### Agent Orchestration Domain

```mermaid
classDiagram
    Team "1" --> "*" Agent
    Agent "1" --> "*" Tool
    
    class Team {
        +id: str
        +name: str
        +description: str
        +agents: List[str]
    }
    
    class Agent {
        +id: str
        +name: str
        +type: str
        +capabilities: List[str]
    }
    
    class Tool {
        +id: str
        +name: str
        +description: str
        +agent_id: str
    }
```

## Core Layer

The core layer contains the domain models, interfaces, and schema definitions that form the heart of the system.

### Domain Models

Domain models represent the core business entities with behavior, not just data structures. They encapsulate business rules and invariants.

**Key Characteristics:**
- Rich behavior methods
- Business rule enforcement
- Domain-specific operations

**Example Structure:**
```mermaid
graph TD
    core[core/] --> models[models/]
    core --> repositories[repositories/]
    core --> schema[schema/]
    models --> project[project.py]
    models --> sprint[sprint.py]
    models --> task[task.py]
    repositories --> project_repository[project_repository.py]
```

### Repository Interfaces

Repository interfaces define the contract for data access operations without specifying implementation details.

**Key Characteristics:**
- Abstract interfaces
- CRUD operations
- Domain-specific queries

## Application Layer

The application layer orchestrates the core layer to perform business operations.

### Services

Services coordinate domain objects to perform business operations that span multiple entities.

**Key Characteristics:**
- Orchestration of domain objects
- Transaction management
- No business rules (delegated to domain)

**Example Structure:**
```mermaid
graph TD
    services[services/] --> project_service[project_service.py]
    services --> agent_service[agent_service.py]
    services --> task_service[task_service.py]
    services --> api_service[api_service.py]
```

## Infrastructure Layer

The infrastructure layer provides technical capabilities to support the higher layers.

### Repository Implementations

Concrete implementations of repository interfaces that handle data persistence.

**Key Characteristics:**
- Implement repository interfaces
- Handle data storage details
- Manage serialization/deserialization

**Example Structure:**
```mermaid
graph TD
    infrastructure[infrastructure/] --> repositories[repositories/]
    infrastructure --> adapters[adapters/]
    repositories --> file_project_repository[file_project_repository.py]
    adapters --> pydantic_adapters[pydantic_adapters.py]
```

### Adapters

Adapters convert between domain models and external representations (like API DTOs).

**Key Characteristics:**
- Bidirectional conversion
- Prevent domain model leakage
- Handle format differences

## Interface Layer

The interface layer handles interaction with external systems or users.

### API Schemas

Pydantic models for API validation and serialization.

**Key Characteristics:**
- Input validation
- Response serialization
- No business logic

**Example Structure:**
```mermaid
graph TD
    api[api/] --> schemas[schemas/]
    api --> routers[routers/]
    schemas --> project_schema[project.py]
    schemas --> sprint_schema[sprint.py]
    schemas --> task_schema[task.py]
    routers --> project_router[project.py]
    routers --> job_router[job.py]
```

### API Routers

FastAPI routers that handle HTTP requests and delegate to the application services.

**Key Characteristics:**
- Route definition
- Request handling
- Response formatting
- Error handling

## Extension Points

Roboco is designed to be extensible in several key areas:

1. **New Agent Types**: The system can be extended with new agent types by implementing the base Agent class
2. **New Tools**: New tools can be added by implementing the Tool interface
3. **New Repository Implementations**: Alternative storage mechanisms can be implemented by creating new repository classes
4. **New API Endpoints**: The API can be extended with new endpoints by adding routers

## Configuration System

The configuration system allows for customization without code changes:

```mermaid
graph TD
    config[config/] --> roles[roles/]
    config --> teams[teams/]
    config --> tools[tools/]
    config --> config_toml[config.toml]
```

## Dependency Flow

The system follows a dependency rule where inner layers do not depend on outer layers:

- Core layer has no external dependencies
- Application layer depends only on the core layer
- Infrastructure layer implements interfaces defined in the core layer
- Interface layer depends on the application layer

This ensures that the core business logic remains isolated from technical concerns and can evolve independently.
