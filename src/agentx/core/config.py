from pydantic import BaseModel, Field, model_validator
from typing import List, Dict, Any, Optional, Literal, Union
from datetime import datetime
from enum import Enum

class ExecutionMode(str, Enum):
    """Execution modes for task processing."""
    AUTONOMOUS = "autonomous"
    STEP_THROUGH = "step_through"

class LLMProvider(str, Enum):
    """Supported LLM providers."""
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    CUSTOM = "custom"

class ToolType(str, Enum):
    """Types of tools supported by the framework."""
    PYTHON_FUNCTION = "python_function"
    SHELL_SCRIPT = "shell_script"
    MCP_TOOL = "mcp_tool"
    BUILTIN = "builtin"

class CollaborationPatternType(str, Enum):
    """Types of collaboration patterns."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONSENSUS = "consensus"
    DYNAMIC = "dynamic"

class GuardrailType(str, Enum):
    """Types of guardrails."""
    INPUT_VALIDATION = "input_validation"
    OUTPUT_FILTERING = "output_filtering"
    RATE_LIMITING = "rate_limiting"
    CONTENT_SAFETY = "content_safety"

class LLMConfig(BaseModel):
    """LLM configuration with DeepSeek as default provider."""
    provider: str = "deepseek"  # Default provider (Req #17)
    model: str = "deepseek-chat"  # Default model (Req #17)
    temperature: float = 0.7
    max_tokens: int = 4000  # Default value
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 30
    retry_policy: Dict[str, Any] = Field(default_factory=dict)
    
    @model_validator(mode='after')
    def set_default_base_url(self):
        if self.base_url is None and self.provider == 'deepseek':
            self.base_url = 'https://api.deepseek.com'
        return self

class ToolConfig(BaseModel):
    """Tool configuration supporting multiple tool types."""
    name: str
    type: Union[ToolType, str]  # Accept both enum and string values
    description: Optional[str] = None
    source: Optional[str] = None  # For python_function tools
    parameters: Optional[Dict[str, Any]] = None  # JSON schema for parameters
    config: Dict[str, Any] = Field(default_factory=dict)
    # For custom tools
    path: Optional[str] = None
    function: Optional[str] = None
    # For MCP tools
    server_url: Optional[str] = None
    # For HITL tools
    timeout: Optional[int] = None
    escalation_policy: Optional[str] = None

class HandoffRule(BaseModel):
    """Handoff rule for agent-to-agent routing."""
    from_agent: str
    to_agent: str
    condition: Optional[str] = None  # Future: conditional handoffs
    handoff_type: str = "sequential"  # "sequential", "parallel"

class CollaborationPattern(BaseModel):
    """Custom collaboration pattern configuration."""
    name: str
    type: str  # "parallel", "consensus", "custom"
    agents: List[str]
    coordination_agent: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)

class GuardrailPolicy(BaseModel):
    """Guardrail policy for safety and compliance."""
    name: str
    type: str  # "input_validation", "content_filter", "rate_limit", "compliance"
    rules: List[Dict[str, Any]]
    severity: str = "medium"
    action: str = "warn"  # "block", "warn", "log"

class MemoryConfig(BaseModel):
    """Memory system configuration."""
    enabled: bool = True
    max_context_tokens: int = 8000
    semantic_search_enabled: bool = True
    short_term_limit: int = 10000  # tokens
    long_term_enabled: bool = True
    consolidation_interval: int = 3600  # seconds
    vector_db_config: Dict[str, Any] = Field(default_factory=dict)

class AgentConfig(BaseModel):
    """Agent configuration for flat team structure."""
    name: str
    description: str
    prompt_template: str  # Path to Jinja2 template file
    llm_config: Optional[LLMConfig] = None  # Override default LLM
    tools: List[str] = Field(default_factory=list)  # Tool names available to this agent
    memory_config: Optional[MemoryConfig] = None
    guardrail_policies: List[str] = Field(default_factory=list)
    collaboration_patterns: List[str] = Field(default_factory=list)
    max_parallel_tasks: int = 1

class ExecutionConfig(BaseModel):
    """Execution configuration for task control."""
    mode: str = "autonomous"  # "autonomous", "step_through"
    max_rounds: int = 20  # Maximum conversation rounds
    timeout_seconds: int = 300  # Task timeout
    step_through_enabled: bool = False
    max_steps: Optional[int] = None
    breakpoints: List[str] = Field(default_factory=list)
    human_intervention_points: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)
    failure_criteria: List[str] = Field(default_factory=list)

class TeamConfig(BaseModel):
    """Root team configuration model."""
    name: str
    description: str
    version: str = "1.0.0"
    agents: List[AgentConfig]
    tools: List[ToolConfig] = Field(default_factory=list)
    handoff_rules: List[HandoffRule] = Field(default_factory=list)
    collaboration_patterns: List[CollaborationPattern] = Field(default_factory=list)
    guardrail_policies: List[GuardrailPolicy] = Field(default_factory=list)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)  # Changed from memory_config to memory
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)  # Changed from execution_config to execution
    deployment_config: Dict[str, Any] = Field(default_factory=dict)
    
    # Dynamic context variables for agent coordination
    context_variables: Dict[str, Any] = Field(default_factory=dict)
    
    # Execution plan configuration
    execution_plan: Dict[str, Any] = Field(default_factory=dict) 