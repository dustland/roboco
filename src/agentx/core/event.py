from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Union, Literal, List, Dict, Any, Optional
from .tool import ToolResult
from .message import Artifact
from .tool import ToolCall

# This file defines the execution event models for the AgentX framework.
# These are discrete notifications about significant lifecycle events.
# For message streaming, see streaming.py

# --- Dual-Channel Event Model ---

class StreamChunk(BaseModel):
    """
    Channel 1: Low-latency token stream for UI updates.
    """
    type: Literal["content_chunk"] = "content_chunk"
    text: str

# --- Structured Execution Events ---

# Task Lifecycle Events
class TaskStartEvent(BaseModel):
    """Task execution started."""
    type: Literal["event_task_start"] = "event_task_start"
    task_id: str
    timestamp: datetime
    initial_prompt: str
    execution_mode: str
    team_config: Dict[str, Any]

class TaskCompleteEvent(BaseModel):
    """Task execution completed."""
    type: Literal["event_task_complete"] = "event_task_complete"
    task_id: str
    timestamp: datetime
    final_status: Literal["success", "error", "cancelled"]
    summary: Optional[str] = None
    artifacts_created: List[str] = Field(default_factory=list)
    total_steps: int
    total_duration_ms: int

class TaskPausedEvent(BaseModel):
    """Task execution paused."""
    type: Literal["event_task_paused"] = "event_task_paused"
    task_id: str
    timestamp: datetime
    reason: str  # "step_mode", "breakpoint", "user_request", "hitl_intervention"
    context: Dict[str, Any] = Field(default_factory=dict)

class TaskResumedEvent(BaseModel):
    """Task execution resumed."""
    type: Literal["event_task_resumed"] = "event_task_resumed"
    task_id: str
    timestamp: datetime
    reason: str
    context: Dict[str, Any] = Field(default_factory=dict)

# Agent Events
class AgentStartEvent(BaseModel):
    """Agent turn started."""
    type: Literal["event_agent_start"] = "event_agent_start"
    agent_name: str
    step_id: str
    timestamp: datetime
    context_size: Optional[int] = None
    memory_retrieved: Optional[int] = None

class AgentCompleteEvent(BaseModel):
    """Agent turn completed."""
    type: Literal["event_agent_complete"] = "event_agent_complete"
    agent_name: str
    step_id: str
    timestamp: datetime
    token_count: Optional[int] = None
    execution_time_ms: Optional[int] = None
    memory_stored: Optional[int] = None

class AgentHandoffEvent(BaseModel):
    """Agent handoff occurred."""
    type: Literal["event_agent_handoff"] = "event_agent_handoff"
    from_agent: str
    to_agent: str
    reason: str
    timestamp: datetime
    context: Dict[str, Any] = Field(default_factory=dict)
    handoff_type: str = "sequential"  # "sequential", "parallel"

# Advanced Collaboration Events
class ParallelExecutionStartEvent(BaseModel):
    """Parallel execution started."""
    type: Literal["event_parallel_start"] = "event_parallel_start"
    agents: List[str]
    coordination_agent: Optional[str] = None
    timestamp: datetime
    sync_points: List[str] = Field(default_factory=list)

class ParallelExecutionSyncEvent(BaseModel):
    """Parallel execution sync point reached."""
    type: Literal["event_parallel_sync"] = "event_parallel_sync"
    sync_point: str
    completed_agents: List[str]
    waiting_agents: List[str]
    timestamp: datetime

class ConsensusProposalEvent(BaseModel):
    """Consensus proposal made."""
    type: Literal["event_consensus_proposal"] = "event_consensus_proposal"
    proposal_id: str
    proposer_agent: str
    decision: str
    stakeholders: List[str]
    timestamp: datetime

class ConsensusVoteEvent(BaseModel):
    """Consensus vote cast."""
    type: Literal["event_consensus_vote"] = "event_consensus_vote"
    proposal_id: str
    voter_agent: str
    vote: str
    reasoning: str
    timestamp: datetime

class ConsensusReachedEvent(BaseModel):
    """Consensus reached."""
    type: Literal["event_consensus_reached"] = "event_consensus_reached"
    proposal_id: str
    final_decision: str
    votes: Dict[str, str]
    timestamp: datetime

# Tool Events
class ToolCallEvent(BaseModel):
    """Tool call initiated."""
    type: Literal["event_tool_call"] = "event_tool_call"
    tool_call: ToolCall
    agent_name: str
    timestamp: datetime
    sandbox_id: Optional[str] = None

class ToolResultEvent(BaseModel):
    """Tool call completed."""
    type: Literal["event_tool_result"] = "event_tool_result"
    tool_result: ToolResult
    timestamp: datetime
    execution_time_ms: Optional[int] = None
    sandbox_id: Optional[str] = None

# Memory Events
class MemoryStoreEvent(BaseModel):
    """Memory stored."""
    type: Literal["event_memory_store"] = "event_memory_store"
    memory_id: str
    memory_type: str
    agent_name: str
    content_size: int
    timestamp: datetime

class MemoryRetrieveEvent(BaseModel):
    """Memory retrieved."""
    type: Literal["event_memory_retrieve"] = "event_memory_retrieve"
    query: str
    results_count: int
    agent_name: str
    timestamp: datetime
    relevance_threshold: Optional[float] = None

class MemoryConsolidateEvent(BaseModel):
    """Memory consolidated."""
    type: Literal["event_memory_consolidate"] = "event_memory_consolidate"
    topic: str
    items_consolidated: int
    timestamp: datetime
    summary_length: int

# HITL Events
class HITLRequestEvent(BaseModel):
    """Human-in-the-loop request made."""
    type: Literal["event_hitl_request"] = "event_hitl_request"
    request_id: str
    request_type: str  # "approval", "feedback", "escalation"
    agent_name: str
    context: Dict[str, Any]
    timeout: Optional[int] = None
    timestamp: datetime

class HITLResponseEvent(BaseModel):
    """Human-in-the-loop response received."""
    type: Literal["event_hitl_response"] = "event_hitl_response"
    request_id: str
    response_type: str  # "approved", "rejected", "modified", "timeout"
    response_data: Dict[str, Any]
    response_time_ms: int
    timestamp: datetime

# Guardrail Events
class GuardrailViolationEvent(BaseModel):
    """Guardrail policy violation."""
    type: Literal["event_guardrail_violation"] = "event_guardrail_violation"
    violation_id: str
    check_type: str
    severity: str
    policy_violated: str
    agent_name: Optional[str] = None
    content_sample: Optional[str] = None
    action_taken: str  # "blocked", "warned", "logged"
    timestamp: datetime

class GuardrailPolicyUpdateEvent(BaseModel):
    """Guardrail policy updated."""
    type: Literal["event_guardrail_policy_update"] = "event_guardrail_policy_update"
    policy_name: str
    update_type: str  # "created", "modified", "deleted"
    updated_by: str
    timestamp: datetime

# Artifact Events
class ArtifactCreatedEvent(BaseModel):
    """Artifact created."""
    type: Literal["event_artifact_created"] = "event_artifact_created"
    artifact: Artifact
    created_by: str
    timestamp: datetime

class ArtifactModifiedEvent(BaseModel):
    """Artifact modified."""
    type: Literal["event_artifact_modified"] = "event_artifact_modified"
    artifact_uri: str
    modified_by: str
    changes: Dict[str, Any]
    version: str
    timestamp: datetime

class ArtifactVersionedEvent(BaseModel):
    """Artifact versioned."""
    type: Literal["event_artifact_versioned"] = "event_artifact_versioned"
    artifact_uri: str
    old_version: str
    new_version: str
    reason: str
    timestamp: datetime

# Error Events
class ErrorEvent(BaseModel):
    """Error occurred."""
    type: Literal["event_error"] = "event_error"
    error_id: str
    error_type: str
    error_message: str
    context: Dict[str, Any]
    timestamp: datetime
    recoverable: bool
    recovery_action: Optional[str] = None
    stack_trace: Optional[str] = None

class RecoveryEvent(BaseModel):
    """Error recovery attempted."""
    type: Literal["event_recovery"] = "event_recovery"
    error_id: str
    recovery_strategy: str
    success: bool
    timestamp: datetime
    details: Dict[str, Any] = Field(default_factory=dict)

# Step-Through Events
class BreakpointHitEvent(BaseModel):
    """Breakpoint hit during execution."""
    type: Literal["event_breakpoint_hit"] = "event_breakpoint_hit"
    breakpoint_id: str
    breakpoint_type: str
    context: Dict[str, Any]
    timestamp: datetime
    agent_name: Optional[str] = None

class UserInterventionEvent(BaseModel):
    """User intervention occurred."""
    type: Literal["event_user_intervention"] = "event_user_intervention"
    intervention_id: str
    intervention_type: str  # "instruction", "plan_update", "agent_override", "team_modification"
    details: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[str] = None

# System Health Events
class HealthCheckEvent(BaseModel):
    """System health check result."""
    type: Literal["event_health_check"] = "event_health_check"
    component: str
    status: str  # "healthy", "degraded", "unhealthy"
    metrics: Dict[str, Any]
    timestamp: datetime

class PerformanceMetricEvent(BaseModel):
    """Performance metric recorded."""
    type: Literal["event_performance_metric"] = "event_performance_metric"
    metric_name: str
    metric_value: float
    metric_unit: str
    component: str
    timestamp: datetime
    tags: Dict[str, str] = Field(default_factory=dict)

# Union type for all execution events
ExecutionEvent = Union[
    TaskStartEvent, TaskCompleteEvent, TaskPausedEvent, TaskResumedEvent,
    AgentStartEvent, AgentCompleteEvent, AgentHandoffEvent,
    ParallelExecutionStartEvent, ParallelExecutionSyncEvent,
    ConsensusProposalEvent, ConsensusVoteEvent, ConsensusReachedEvent,
    ToolCallEvent, ToolResultEvent,
    MemoryStoreEvent, MemoryRetrieveEvent, MemoryConsolidateEvent,
    HITLRequestEvent, HITLResponseEvent,
    GuardrailViolationEvent, GuardrailPolicyUpdateEvent,
    ArtifactCreatedEvent, ArtifactModifiedEvent, ArtifactVersionedEvent,
    ErrorEvent, RecoveryEvent,
    BreakpointHitEvent, UserInterventionEvent,
    HealthCheckEvent, PerformanceMetricEvent
]