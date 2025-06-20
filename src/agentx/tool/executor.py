"""
Tool executor for secure and performant tool execution.

The executor is responsible for:
- Secure tool execution with validation
- Performance monitoring and resource limits
- Error handling and result formatting
- Security policies and audit logging
"""

import time
import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel
from dataclasses import asdict, is_dataclass
from ..utils.logger import get_logger
from .registry import ToolRegistry, get_tool_registry
from .models import ToolResult

logger = get_logger(__name__)


def safe_json_serialize(obj):
    """
    Safely serialize objects to JSON, handling dataclasses, Pydantic models, and other complex types.
    """
    if is_dataclass(obj):
        return asdict(obj)
    elif hasattr(obj, 'model_dump'):  # Pydantic model
        return obj.model_dump()
    elif hasattr(obj, '__dict__'):  # Regular object with attributes
        return obj.__dict__
    elif isinstance(obj, (list, tuple)):
        return [safe_json_serialize(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: safe_json_serialize(value) for key, value in obj.items()}
    else:
        # For primitive types and other serializable objects
        return obj


def safe_json_dumps(obj, **kwargs):
    """
    Safely convert object to JSON string, handling complex nested objects.
    """
    try:
        # First try regular JSON serialization
        return json.dumps(obj, **kwargs)
    except TypeError:
        # If that fails, use safe serialization
        safe_obj = safe_json_serialize(obj)
        return json.dumps(safe_obj, **kwargs)


class SecurityPolicy:
    """Security policies for tool execution."""
    
    # Resource limits
    MAX_EXECUTION_TIME = 60.0  # seconds
    MAX_TOOLS_PER_BATCH = 10
    MAX_CONCURRENT_EXECUTIONS = 3
    
    # Tool permissions per agent type
    TOOL_PERMISSIONS = {
        "default": [
            # Basic file operations
            "read_file", "write_file", "append_file", "file_exists",
            "create_directory", "delete_file", "list_directory",
            # Artifact operations
            "store_artifact", "get_artifact", "list_artifacts",
            "get_artifact_versions", "delete_artifact",
            # Framework operations
            "get_context", "set_context", "create_plan", 
            "update_task_status", "get_plan_status",
            # Search and weather tools
            "web_search", "serpapi_search", "get_weather",
            # Web content tools
            "extract_content", "crawl_website", "automate_browser",
            # News and search tools
            "news_search"
        ],
        "research_agent": [
            "web_search", "serpapi_search", "extract_content", "news_search", "read_file", "store_artifact"
        ],
        "writer_agent": [
            "read_file", "write_file", "store_artifact", "get_artifact"
        ],
        "reviewer_agent": [
            "read_file", "store_artifact", "get_artifact"
        ]
    }
    
    # Blocked tools (never allowed)
    BLOCKED_TOOLS = [
        "system_command", "exec", "eval", "delete_all"
    ]


class ToolExecutor:
    """
    Secure tool executor with performance monitoring and security policies.
    
    This class handles the actual execution of tools with:
    - Security validation and permissions
    - Resource limits and monitoring
    - Error handling and logging
    - Audit trails
    """
    
    def __init__(self, registry: Optional[ToolRegistry] = None):
        """
        Initialize tool executor.
        
        Args:
            registry: Tool registry to use (defaults to global registry)
        """
        self.registry = registry or get_tool_registry()
        self.security_policy = SecurityPolicy()
        self.active_executions = 0
        self.execution_history: List[Dict[str, Any]] = []
        
        logger.info("🔧 ToolExecutor initialized with security policies")
    
    async def execute_tool(
        self, 
        tool_name: str, 
        agent_name: str = "default",
        **kwargs
    ) -> ToolResult:
        """
        Execute a single tool with security validation.
        
        Args:
            tool_name: Name of the tool to execute
            agent_name: Name of the agent requesting execution (for permissions)
            **kwargs: Tool arguments
            
        Returns:
            ToolResult with execution outcome
        """
        start_time = time.time()
        
        try:
            # Security validation
            validation_result = self._validate_execution(tool_name, agent_name, kwargs)
            if not validation_result.success:
                return validation_result
            
            # Resource limit check
            if self.active_executions >= self.security_policy.MAX_CONCURRENT_EXECUTIONS:
                return ToolResult(
                    success=False,
                    error="Maximum concurrent executions exceeded",
                    execution_time=time.time() - start_time
                )
            
            # Get tool function
            tool_function = self.registry.get_tool_function(tool_name)
            if not tool_function:
                return ToolResult(
                    success=False,
                    error=f"Tool '{tool_name}' not found in registry",
                    execution_time=time.time() - start_time
                )
            
            # Execute with monitoring
            self.active_executions += 1
            try:
                result = await self._execute_with_timeout(
                    tool_function.function, 
                    kwargs,
                    self.security_policy.MAX_EXECUTION_TIME
                )
                
                execution_time = time.time() - start_time
                
                # Log successful execution
                self._log_execution(tool_name, agent_name, kwargs, True, execution_time)
                
                return ToolResult(
                    success=True,
                    result=result,
                    execution_time=execution_time,
                    metadata={
                        "tool_name": tool_name,
                        "agent_name": agent_name
                    }
                )
                
            finally:
                self.active_executions -= 1
                
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            error_msg = f"Tool execution timed out after {self.security_policy.MAX_EXECUTION_TIME}s"
            self._log_execution(tool_name, agent_name, kwargs, False, execution_time, error_msg)
            
            return ToolResult(
                success=False,
                error=error_msg,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Tool execution failed: {str(e)}"
            self._log_execution(tool_name, agent_name, kwargs, False, execution_time, error_msg)
            
            return ToolResult(
                success=False,
                error=error_msg,
                execution_time=execution_time
            )
    
    async def execute_tool_calls(
        self, 
        tool_calls: List[Any], 
        agent_name: str = "default"
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple tool calls and return formatted results for LLM.
        
        Args:
            tool_calls: List of tool call objects from LLM response
            agent_name: Name of the agent requesting execution
            
        Returns:
            List of tool result messages formatted for LLM conversation
        """
        # Validate batch size
        if len(tool_calls) > self.security_policy.MAX_TOOLS_PER_BATCH:
            error_msg = f"Too many tool calls: {len(tool_calls)} > {self.security_policy.MAX_TOOLS_PER_BATCH}"
            logger.error(error_msg)
            
            # Return error for all tool calls
            return [
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.function.name,
                    "content": safe_json_dumps({
                        "success": False,
                        "error": error_msg
                    })
                } for tc in tool_calls
            ]
        
        tool_messages = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            tool_call_id = tool_call.id
            try:
                # Parse tool arguments
                tool_args = json.loads(tool_call.function.arguments)
                
                # Log tool call start
                logger.info(f"🔧 TOOL CALL START | ID: {tool_call_id} | Tool: {tool_name} | Agent: {agent_name}")
                logger.info(f"📝 TOOL ARGS | {safe_json_dumps(tool_args, indent=2)}")
                
                # Execute the tool
                start_time = time.time()
                result = await self.execute_tool(tool_name, agent_name, **tool_args)
                execution_time = time.time() - start_time
                
                # Log tool call result
                if result.success:
                    logger.info(f"✅ TOOL CALL SUCCESS | ID: {tool_call_id} | Tool: {tool_name} | Time: {execution_time:.2f}s")
                    logger.info(f"📤 TOOL RESULT | {safe_json_dumps(result.result, indent=2)[:500]}{'...' if len(str(result.result)) > 500 else ''}")
                else:
                    logger.error(f"❌ TOOL CALL FAILED | ID: {tool_call_id} | Tool: {tool_name} | Error: {result.error}")
                    logger.error(f"⏱️  TOOL TIME | {execution_time:.2f}s")
                
                # Format result for LLM using safe serialization
                if result.success:
                    content = safe_json_dumps({
                        "success": True,
                        "result": result.result,
                        "execution_time": result.execution_time,
                        "metadata": result.metadata
                    }, ensure_ascii=False, indent=2)
                else:
                    content = safe_json_dumps({
                        "success": False,
                        "error": result.error,
                        "execution_time": result.execution_time
                    }, ensure_ascii=False, indent=2)
                    
            except json.JSONDecodeError as e:
                logger.error(f"❌ TOOL CALL PARSE ERROR | ID: {tool_call_id} | Tool: {tool_name} | Error: Invalid JSON arguments")
                logger.error(f"🔍 RAW ARGS | {tool_call.function.arguments}")
                content = safe_json_dumps({
                    "success": False,
                    "error": f"Invalid tool arguments: {str(e)}"
                })
                
            except Exception as e:
                logger.error(f"❌ TOOL CALL EXCEPTION | ID: {tool_call_id} | Tool: {tool_name} | Error: {str(e)}")
                content = safe_json_dumps({
                    "success": False,
                    "error": f"Tool execution failed: {str(e)}"
                })
            
            # Add tool result message
            tool_messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": content
            })
        
        # Log batch summary
        successful_calls = sum(1 for msg in tool_messages if '"success": true' in msg["content"])
        failed_calls = len(tool_messages) - successful_calls
        logger.info(f"📊 TOOL BATCH COMPLETE | Agent: {agent_name} | Total: {len(tool_messages)} | Success: {successful_calls} | Failed: {failed_calls}")
            
        return tool_messages
    
    def _validate_execution(
        self, 
        tool_name: str, 
        agent_name: str, 
        kwargs: Dict[str, Any]
    ) -> ToolResult:
        """
        Validate tool execution request against security policies.
        
        Args:
            tool_name: Tool to execute
            agent_name: Agent requesting execution
            kwargs: Tool arguments
            
        Returns:
            ToolResult indicating validation success/failure
        """
        # Check if tool is blocked
        if tool_name in self.security_policy.BLOCKED_TOOLS:
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' is blocked by security policy"
            )
        
        # Check agent permissions
        allowed_tools = self.security_policy.TOOL_PERMISSIONS.get(
            agent_name, 
            self.security_policy.TOOL_PERMISSIONS["default"]
        )
        
        if tool_name not in allowed_tools:
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' not allowed for agent '{agent_name}'"
            )
        
        # Additional validation can be added here
        # - Argument validation
        # - Rate limiting
        # - Resource checks
        
        return ToolResult(success=True)
    
    async def _execute_with_timeout(
        self, 
        func, 
        kwargs: Dict[str, Any], 
        timeout: float
    ):
        """
        Execute function with timeout.
        
        Args:
            func: Function to execute
            kwargs: Function arguments
            timeout: Timeout in seconds
            
        Returns:
            Function result
            
        Raises:
            asyncio.TimeoutError: If execution exceeds timeout
        """
        if asyncio.iscoroutinefunction(func):
            # Async function
            return await asyncio.wait_for(func(**kwargs), timeout=timeout)
        else:
            # Sync function - run in thread pool
            loop = asyncio.get_event_loop()
            return await asyncio.wait_for(
                loop.run_in_executor(None, lambda: func(**kwargs)),
                timeout=timeout
            )
    
    def _log_execution(
        self, 
        tool_name: str, 
        agent_name: str, 
        kwargs: Dict[str, Any],
        success: bool,
        execution_time: float,
        error: Optional[str] = None
    ):
        """
        Log tool execution for audit trail.
        
        Args:
            tool_name: Tool that was executed
            agent_name: Agent that requested execution
            kwargs: Tool arguments
            success: Whether execution succeeded
            execution_time: Time taken for execution
            error: Error message if failed
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "agent_name": agent_name,
            "arguments": kwargs,
            "success": success,
            "execution_time": execution_time,
            "error": error
        }
        
        self.execution_history.append(log_entry)
        
        # Keep only last 1000 entries to prevent memory bloat
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]
        
        # Log to file/external system if needed
        if success:
            logger.debug(f"✅ Tool '{tool_name}' executed successfully for '{agent_name}' in {execution_time:.2f}s")
        else:
            logger.debug(f"❌ Tool '{tool_name}' failed for '{agent_name}': {error}")
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        total_executions = len(self.execution_history)
        successful_executions = sum(1 for entry in self.execution_history if entry["success"])
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failure_rate": (total_executions - successful_executions) / max(total_executions, 1),
            "active_executions": self.active_executions,
            "recent_executions": self.execution_history[-10:] if self.execution_history else []
        }
    
    def clear_history(self):
        """Clear execution history."""
        self.execution_history.clear()
        logger.debug("Tool execution history cleared") 