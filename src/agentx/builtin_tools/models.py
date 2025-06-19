"""
Builtin tools subsystem models - Self-contained data models for builtin tools.

This module contains all data models related to builtin tools, following the
architectural rule that subsystems should be self-contained and not import from core.
"""

from typing import Dict, List, Optional, Any, Union, Literal
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod

# Internal utilities (avoid importing from core/utils)
import secrets
import string

def generate_short_id(length: int = 8) -> str:
    """Generate a short, URL-friendly, cryptographically secure random ID."""
    alphabet = string.ascii_uppercase + string.ascii_lowercase + string.digits + '_'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


# ============================================================================
# BUILTIN TOOL TYPE DEFINITIONS
# ============================================================================

class BuiltinToolCategory(str, Enum):
    """Categories of builtin tools."""
    SEARCH = "search"
    MEMORY = "memory"
    STORAGE = "storage"
    WEB = "web"
    CONTEXT = "context"
    PLANNING = "planning"
    COMMUNICATION = "communication"
    UTILITY = "utility"


class SearchProvider(str, Enum):
    """Supported search providers."""
    SERPAPI = "serpapi"
    GOOGLE = "google"
    BING = "bing"
    DUCKDUCKGO = "duckduckgo"
    TAVILY = "tavily"


class WebBrowserEngine(str, Enum):
    """Supported web browser engines."""
    PLAYWRIGHT = "playwright"
    SELENIUM = "selenium"
    REQUESTS = "requests"


# ============================================================================
# SEARCH TOOL MODELS
# ============================================================================

class SearchQuery(BaseModel):
    """Search query parameters."""
    query: str
    provider: SearchProvider = SearchProvider.SERPAPI
    num_results: int = 10
    safe_search: bool = True
    country: Optional[str] = None
    language: Optional[str] = None
    
    # Advanced search options
    date_range: Optional[str] = None  # "day", "week", "month", "year"
    file_type: Optional[str] = None
    site_search: Optional[str] = None
    
    # Metadata
    search_id: str = Field(default_factory=lambda: f"search_{generate_short_id()}")
    requested_by: Optional[str] = None
    task_id: Optional[str] = None


class SearchResult(BaseModel):
    """Individual search result."""
    title: str
    url: str
    snippet: str
    
    # Additional metadata
    position: int = 0
    domain: Optional[str] = None
    published_date: Optional[datetime] = None
    thumbnail: Optional[str] = None
    
    # Rich snippets
    featured_snippet: Optional[str] = None
    rating: Optional[float] = None
    price: Optional[str] = None
    
    # Internal metadata
    relevance_score: Optional[float] = None
    extracted_at: datetime = Field(default_factory=datetime.now)


class SearchResponse(BaseModel):
    """Complete search response."""
    query: str
    results: List[SearchResult]
    total_results: Optional[int] = None
    
    # Search metadata
    search_id: str
    provider: SearchProvider
    execution_time_ms: float = 0.0
    
    # Related searches
    related_searches: List[str] = Field(default_factory=list)
    suggested_queries: List[str] = Field(default_factory=list)
    
    # Provider-specific data
    provider_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    searched_at: datetime = Field(default_factory=datetime.now)


# ============================================================================
# WEB TOOL MODELS
# ============================================================================

class WebPageRequest(BaseModel):
    """Request to fetch a web page."""
    url: str
    method: str = "GET"
    headers: Dict[str, str] = Field(default_factory=dict)
    params: Dict[str, Any] = Field(default_factory=dict)
    data: Optional[Union[str, Dict[str, Any]]] = None
    
    # Browser options
    use_browser: bool = False
    wait_for_selector: Optional[str] = None
    screenshot: bool = False
    pdf: bool = False
    
    # Request settings
    timeout_seconds: int = 30
    follow_redirects: bool = True
    verify_ssl: bool = True
    
    # Metadata
    request_id: str = Field(default_factory=lambda: f"req_{generate_short_id()}")
    requested_by: Optional[str] = None
    task_id: Optional[str] = None


class WebPageResponse(BaseModel):
    """Response from web page fetch."""
    url: str
    status_code: int
    content: str
    
    # Response metadata
    headers: Dict[str, str] = Field(default_factory=dict)
    content_type: Optional[str] = None
    content_length: Optional[int] = None
    encoding: Optional[str] = None
    
    # Page metadata
    title: Optional[str] = None
    description: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    
    # Rich content
    links: List[str] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)
    forms: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Files (if requested)
    screenshot_path: Optional[str] = None
    pdf_path: Optional[str] = None
    
    # Execution metadata
    request_id: str
    execution_time_ms: float = 0.0
    fetched_at: datetime = Field(default_factory=datetime.now)
    
    # Error information
    error: Optional[str] = None
    redirect_chain: List[str] = Field(default_factory=list)


class BrowserAction(BaseModel):
    """Browser action for web automation."""
    action_type: str  # "click", "type", "scroll", "wait", "navigate"
    selector: Optional[str] = None
    text: Optional[str] = None
    coordinates: Optional[tuple[int, int]] = None
    
    # Action options
    wait_before_ms: int = 0
    wait_after_ms: int = 0
    timeout_ms: int = 5000
    
    # Metadata
    action_id: str = Field(default_factory=lambda: f"action_{generate_short_id()}")
    description: Optional[str] = None


class BrowserSession(BaseModel):
    """Browser automation session."""
    session_id: str = Field(default_factory=lambda: f"session_{generate_short_id()}")
    engine: WebBrowserEngine = WebBrowserEngine.PLAYWRIGHT
    
    # Session state
    current_url: Optional[str] = None
    page_title: Optional[str] = None
    cookies: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Session history
    actions_performed: List[BrowserAction] = Field(default_factory=list)
    pages_visited: List[str] = Field(default_factory=list)
    
    # Session metadata
    started_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    active: bool = True


# ============================================================================
# MEMORY TOOL MODELS
# ============================================================================

class MemoryToolOperation(str, Enum):
    """Memory tool operations."""
    ADD = "add"
    SEARCH = "search"
    GET = "get"
    UPDATE = "update"
    DELETE = "delete"
    CLEAR = "clear"
    STATS = "stats"


class MemoryToolRequest(BaseModel):
    """Request for memory tool operation."""
    operation: MemoryToolOperation
    
    # Content (for add/update operations)
    content: Optional[str] = None
    memory_type: Optional[str] = None
    importance: Optional[float] = None
    tags: List[str] = Field(default_factory=list)
    
    # Query (for search operations)
    query: Optional[str] = None
    limit: int = 10
    
    # Targeting (for get/update/delete operations)
    memory_id: Optional[str] = None
    
    # Context
    agent_name: Optional[str] = None
    task_id: Optional[str] = None
    
    # Metadata
    request_id: str = Field(default_factory=lambda: f"mem_req_{generate_short_id()}")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemoryToolResponse(BaseModel):
    """Response from memory tool operation."""
    operation: MemoryToolOperation
    success: bool
    
    # Results
    memory_id: Optional[str] = None
    memories: List[Dict[str, Any]] = Field(default_factory=list)
    stats: Optional[Dict[str, Any]] = None
    
    # Execution metadata
    request_id: str
    execution_time_ms: float = 0.0
    
    # Error information
    error: Optional[str] = None
    error_code: Optional[str] = None


# ============================================================================
# STORAGE TOOL MODELS
# ============================================================================

class StorageToolOperation(str, Enum):
    """Storage tool operations."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    COPY = "copy"
    MOVE = "move"
    EXISTS = "exists"


class StorageToolRequest(BaseModel):
    """Request for storage tool operation."""
    operation: StorageToolOperation
    path: str
    
    # Content (for create/update operations)
    content: Optional[Union[str, bytes]] = None
    content_type: Optional[str] = None
    
    # Options
    source_path: Optional[str] = None  # For copy/move operations
    recursive: bool = False  # For list/delete operations
    overwrite: bool = False  # For create operations
    
    # Filters (for list operations)
    file_pattern: Optional[str] = None
    include_hidden: bool = False
    
    # Context
    agent_name: Optional[str] = None
    task_id: Optional[str] = None
    
    # Metadata
    request_id: str = Field(default_factory=lambda: f"storage_req_{generate_short_id()}")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StorageToolResponse(BaseModel):
    """Response from storage tool operation."""
    operation: StorageToolOperation
    success: bool
    path: str
    
    # Results
    content: Optional[Union[str, bytes]] = None
    artifact_id: Optional[str] = None
    files: List[Dict[str, Any]] = Field(default_factory=list)
    exists: Optional[bool] = None
    
    # File metadata
    size_bytes: Optional[int] = None
    modified_at: Optional[datetime] = None
    content_type: Optional[str] = None
    
    # Execution metadata
    request_id: str
    execution_time_ms: float = 0.0
    
    # Error information
    error: Optional[str] = None
    error_code: Optional[str] = None


# ============================================================================
# CONTEXT TOOL MODELS
# ============================================================================

class ContextToolOperation(str, Enum):
    """Context tool operations."""
    GET_TASK_INFO = "get_task_info"
    GET_AGENT_INFO = "get_agent_info"
    GET_CONVERSATION_HISTORY = "get_conversation_history"
    GET_TOOL_HISTORY = "get_tool_history"
    GET_WORKSPACE_INFO = "get_workspace_info"
    SET_VARIABLE = "set_variable"
    GET_VARIABLE = "get_variable"
    LIST_VARIABLES = "list_variables"


class ContextToolRequest(BaseModel):
    """Request for context tool operation."""
    operation: ContextToolOperation
    
    # Query parameters
    agent_name: Optional[str] = None
    task_id: Optional[str] = None
    limit: int = 100
    
    # Variable operations
    variable_name: Optional[str] = None
    variable_value: Optional[Any] = None
    variable_scope: str = "task"  # "task", "agent", "global"
    
    # Metadata
    request_id: str = Field(default_factory=lambda: f"ctx_req_{generate_short_id()}")
    requested_by: Optional[str] = None


class ContextToolResponse(BaseModel):
    """Response from context tool operation."""
    operation: ContextToolOperation
    success: bool
    
    # Results
    data: Dict[str, Any] = Field(default_factory=dict)
    
    # Execution metadata
    request_id: str
    execution_time_ms: float = 0.0
    
    # Error information
    error: Optional[str] = None
    error_code: Optional[str] = None


# ============================================================================
# PLANNING TOOL MODELS
# ============================================================================

class PlanningToolOperation(str, Enum):
    """Planning tool operations."""
    CREATE_PLAN = "create_plan"
    UPDATE_PLAN = "update_plan"
    GET_PLAN = "get_plan"
    EXECUTE_STEP = "execute_step"
    COMPLETE_STEP = "complete_step"
    ADD_STEP = "add_step"
    REMOVE_STEP = "remove_step"
    LIST_PLANS = "list_plans"


class PlanStep(BaseModel):
    """Individual step in a plan."""
    step_id: str = Field(default_factory=lambda: f"step_{generate_short_id()}")
    title: str
    description: str
    
    # Step properties
    estimated_duration_minutes: Optional[int] = None
    priority: int = 1
    dependencies: List[str] = Field(default_factory=list)  # step_ids
    
    # Execution
    status: str = "pending"  # "pending", "in_progress", "completed", "failed", "skipped"
    assigned_agent: Optional[str] = None
    tools_required: List[str] = Field(default_factory=list)
    
    # Results
    result: Optional[str] = None
    artifacts_created: List[str] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Plan(BaseModel):
    """Execution plan."""
    plan_id: str = Field(default_factory=lambda: f"plan_{generate_short_id()}")
    title: str
    description: str
    
    # Plan structure
    steps: List[PlanStep] = Field(default_factory=list)
    
    # Plan properties
    estimated_duration_minutes: Optional[int] = None
    priority: int = 1
    
    # Execution state
    status: str = "draft"  # "draft", "active", "completed", "failed", "cancelled"
    current_step: Optional[str] = None  # step_id
    
    # Context
    task_id: Optional[str] = None
    created_by: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PlanningToolRequest(BaseModel):
    """Request for planning tool operation."""
    operation: PlanningToolOperation
    
    # Plan targeting
    plan_id: Optional[str] = None
    step_id: Optional[str] = None
    
    # Plan data
    title: Optional[str] = None
    description: Optional[str] = None
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Context
    task_id: Optional[str] = None
    agent_name: Optional[str] = None
    
    # Metadata
    request_id: str = Field(default_factory=lambda: f"plan_req_{generate_short_id()}")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PlanningToolResponse(BaseModel):
    """Response from planning tool operation."""
    operation: PlanningToolOperation
    success: bool
    
    # Results
    plan: Optional[Plan] = None
    plans: List[Plan] = Field(default_factory=list)
    step: Optional[PlanStep] = None
    
    # Execution metadata
    request_id: str
    execution_time_ms: float = 0.0
    
    # Error information
    error: Optional[str] = None
    error_code: Optional[str] = None


# ============================================================================
# BUILTIN TOOL REGISTRY MODELS
# ============================================================================

class BuiltinToolInfo(BaseModel):
    """Information about a builtin tool."""
    name: str
    category: BuiltinToolCategory
    description: str
    
    # Tool properties
    version: str = "1.0.0"
    enabled: bool = True
    requires_config: bool = False
    
    # Dependencies
    required_packages: List[str] = Field(default_factory=list)
    optional_packages: List[str] = Field(default_factory=list)
    
    # Configuration
    config_schema: Dict[str, Any] = Field(default_factory=dict)
    default_config: Dict[str, Any] = Field(default_factory=dict)
    
    # Usage statistics
    usage_count: int = 0
    last_used: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BuiltinToolConfig(BaseModel):
    """Configuration for builtin tools."""
    # Search tools
    search_enabled: bool = True
    search_provider: SearchProvider = SearchProvider.SERPAPI
    search_api_key: Optional[str] = None
    
    # Web tools
    web_enabled: bool = True
    browser_engine: WebBrowserEngine = WebBrowserEngine.PLAYWRIGHT
    browser_headless: bool = True
    
    # Memory tools
    memory_enabled: bool = True
    memory_context_limit: int = 10
    
    # Storage tools
    storage_enabled: bool = True
    storage_max_file_size_mb: int = 100
    
    # Context tools
    context_enabled: bool = True
    context_history_limit: int = 100
    
    # Planning tools
    planning_enabled: bool = True
    planning_max_steps: int = 50
    
    # Global settings
    timeout_seconds: int = 30
    retry_attempts: int = 3
    rate_limit_per_minute: int = 60
    
    # Security settings
    allowed_domains: Optional[List[str]] = None
    blocked_domains: List[str] = Field(default_factory=list)
    safe_mode: bool = True


class BuiltinToolStats(BaseModel):
    """Statistics for builtin tools usage."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    
    # Per-category stats
    calls_by_category: Dict[str, int] = Field(default_factory=dict)
    calls_by_tool: Dict[str, int] = Field(default_factory=dict)
    
    # Performance stats
    avg_execution_time_ms: float = 0.0
    total_execution_time_ms: float = 0.0
    
    # Time-based stats
    calls_today: int = 0
    calls_this_week: int = 0
    calls_this_month: int = 0
    
    # Error stats
    error_rate: float = 0.0
    common_errors: Dict[str, int] = Field(default_factory=dict)
    
    # Last activity
    last_call: Optional[datetime] = None
    most_used_tool: Optional[str] = None


# ============================================================================
# BUILTIN TOOL UTILITIES
# ============================================================================

def create_search_query(query: str, provider: SearchProvider = SearchProvider.SERPAPI,
                       num_results: int = 10, agent_name: str = None,
                       task_id: str = None) -> SearchQuery:
    """Create a search query with default parameters."""
    return SearchQuery(
        query=query,
        provider=provider,
        num_results=num_results,
        requested_by=agent_name,
        task_id=task_id
    )


def create_web_request(url: str, method: str = "GET", use_browser: bool = False,
                      agent_name: str = None, task_id: str = None) -> WebPageRequest:
    """Create a web page request with default parameters."""
    return WebPageRequest(
        url=url,
        method=method,
        use_browser=use_browser,
        requested_by=agent_name,
        task_id=task_id
    )


def create_plan_step(title: str, description: str, assigned_agent: str = None,
                    priority: int = 1, estimated_minutes: int = None) -> PlanStep:
    """Create a plan step with default parameters."""
    return PlanStep(
        title=title,
        description=description,
        assigned_agent=assigned_agent,
        priority=priority,
        estimated_duration_minutes=estimated_minutes
    ) 