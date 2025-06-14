"""
Roboco Observability Monitor

Context-aware observability system:
- Integrated mode: Real-time monitoring for long-running services
- Independent mode: Post-mortem analysis of persisted data
"""

import json
import logging
import asyncio
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, AsyncGenerator
from collections import defaultdict, deque
import os
from pathlib import Path

from ..core.event import global_events, Event

logger = logging.getLogger(__name__)


class ConversationHistory:
    """Track task-level conversation history with persistence."""
    
    def __init__(self, max_tasks: int = 100, persist_path: Optional[str] = None):
        self.tasks: Dict[str, List[Dict[str, Any]]] = {}
        self.max_tasks = max_tasks
        self._task_order = deque(maxlen=max_tasks)
        self.persist_path = persist_path or "roboco_conversations.json"
        
        # Load existing data if available
        self._load_persisted_data()
    
    def add_message(self, task_id: str, agent: str, message: str, message_type: str = "message"):
        """Add a message to task conversation history."""
        if task_id not in self.tasks:
            self.tasks[task_id] = []
            self._task_order.append(task_id)
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "message": message,
            "type": message_type
        }
        
        self.tasks[task_id].append(entry)
        logger.debug(f"Added {message_type} from {agent} to task {task_id}")
        
        # Persist data
        self._persist_data()
    
    def get_task_history(self, task_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a specific task."""
        return self.tasks.get(task_id, [])
    
    def get_all_tasks(self) -> List[str]:
        """Get list of all task IDs."""
        return list(self._task_order)
    
    def get_recent_tasks(self, limit: int = 10) -> List[str]:
        """Get most recent task IDs."""
        return list(self._task_order)[-limit:]
    
    def _persist_data(self):
        """Persist conversation data to disk."""
        try:
            data = {
                "tasks": dict(self.tasks),
                "task_order": list(self._task_order),
                "last_updated": datetime.now().isoformat()
            }
            with open(self.persist_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist conversation data: {e}")
    
    def _load_persisted_data(self):
        """Load persisted conversation data."""
        try:
            if os.path.exists(self.persist_path):
                with open(self.persist_path, 'r') as f:
                    data = json.load(f)
                
                self.tasks = data.get("tasks", {})
                task_order = data.get("task_order", [])
                self._task_order = deque(task_order, maxlen=self.max_tasks)
                
                logger.info(f"Loaded {len(self.tasks)} tasks from {self.persist_path}")
        except Exception as e:
            logger.error(f"Failed to load persisted conversation data: {e}")
    
    async def stream_task_history(self, task_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream conversation history for a task (only works when integrated)."""
        history = self.get_task_history(task_id)
        for entry in history:
            yield entry
            await asyncio.sleep(0.1)  # Small delay for streaming effect


class EventCapture:
    """Capture all events with wildcard handler (integrated mode only)."""
    
    def __init__(self, max_events: int = 1000, persist_path: Optional[str] = None):
        self.events: deque = deque(maxlen=max_events)
        self.event_counts: Dict[str, int] = defaultdict(int)
        self.enabled = False
        self.persist_path = persist_path or "roboco_events.json"
    
    def enable(self):
        """Enable event capture (only when running integrated)."""
        if not self.enabled:
            self._setup_handler()
            self.enabled = True
            logger.info("Event capture enabled")
    
    def _setup_handler(self):
        """Set up the catch-all event handler."""
        def capture_all_events(event: Event):
            event_data = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event.event_type,
                "source": event.source,
                "data": event.data
            }
            
            self.events.append(event_data)
            self.event_counts[event.event_type] += 1
            
            # Persist events periodically
            if len(self.events) % 10 == 0:  # Every 10 events
                self._persist_events()
            
            logger.debug(f"Captured event: {event.event_type} from {event.source}")
        
        # Register for all events using the wildcard pattern
        global_events.on("*", capture_all_events)
    
    def get_events(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get captured events, optionally filtered by type."""
        if not self.enabled:
            return []
            
        events = list(self.events)
        
        if event_type:
            events = [e for e in events if e["event_type"] == event_type]
        
        return events[-limit:]
    
    def get_event_types(self) -> Dict[str, int]:
        """Get count of events by type."""
        return dict(self.event_counts) if self.enabled else {}
    
    def _persist_events(self):
        """Persist events to disk."""
        try:
            data = {
                "events": list(self.events),
                "event_counts": dict(self.event_counts),
                "last_updated": datetime.now().isoformat()
            }
            with open(self.persist_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist events: {e}")


class MemoryViewer:
    """Browse and view memory with persistence support."""
    
    def __init__(self, persist_path: Optional[str] = None):
        self.memory_cache: Dict[str, Any] = {}
        self.categories: Dict[str, List[str]] = defaultdict(list)
        self.persist_path = persist_path or "roboco_memory.json"
        
        # Load existing data
        self._load_persisted_data()
    
    def update_memory_cache(self, key: str, value: Any, category: str = "general"):
        """Update the memory cache with new data."""
        self.memory_cache[key] = {
            "value": value,
            "category": category,
            "timestamp": datetime.now().isoformat()
        }
        
        if key not in self.categories[category]:
            self.categories[category].append(key)
        
        logger.debug(f"Updated memory cache: {key} in category {category}")
        
        # Persist data
        self._persist_data()
    
    async def load_from_memory_api(self, base_url: str = "http://localhost:8000"):
        """Load memory data from the main server API (independent mode)."""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                # Get all tasks first
                response = await client.get(f"{base_url}/tasks")
                if response.status_code == 200:
                    tasks = response.json()
                    
                    for task in tasks:
                        task_id = task["task_id"]
                        
                        # Get memory for each task
                        memory_response = await client.get(f"{base_url}/tasks/{task_id}/memory")
                        if memory_response.status_code == 200:
                            memory_data = memory_response.json()
                            
                            # Update cache with task memory
                            self.update_memory_cache(
                                f"task_{task_id}",
                                memory_data,
                                "tasks"
                            )
                    
                    logger.info(f"Loaded memory data from {len(tasks)} tasks")
                    
        except Exception as e:
            logger.error(f"Failed to load memory from API: {e}")
    
    def get_memory_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        """Get memory item by key."""
        return self.memory_cache.get(key)
    
    def get_memory_by_category(self, category: str) -> Dict[str, Any]:
        """Get all memory items in a category."""
        keys = self.categories.get(category, [])
        return {key: self.memory_cache[key] for key in keys if key in self.memory_cache}
    
    def get_all_categories(self) -> List[str]:
        """Get list of all memory categories."""
        return list(self.categories.keys())
    
    def search_memory(self, query: str) -> Dict[str, Any]:
        """Search memory by key or content."""
        results = {}
        query_lower = query.lower()
        
        for key, data in self.memory_cache.items():
            if query_lower in key.lower():
                results[key] = data
            elif isinstance(data["value"], str) and query_lower in data["value"].lower():
                results[key] = data
        
        return results
    
    def _persist_data(self):
        """Persist memory data to disk."""
        try:
            data = {
                "memory_cache": self.memory_cache,
                "categories": dict(self.categories),
                "last_updated": datetime.now().isoformat()
            }
            with open(self.persist_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist memory data: {e}")
    
    def _load_persisted_data(self):
        """Load persisted memory data."""
        try:
            if os.path.exists(self.persist_path):
                with open(self.persist_path, 'r') as f:
                    data = json.load(f)
                
                self.memory_cache = data.get("memory_cache", {})
                categories_data = data.get("categories", {})
                self.categories = defaultdict(list, categories_data)
                
                logger.info(f"Loaded {len(self.memory_cache)} memory items from {self.persist_path}")
        except Exception as e:
            logger.error(f"Failed to load persisted memory data: {e}")


class ObservabilityMonitor:
    """Main observability monitor with context awareness."""
    
    def __init__(self, data_dir: Optional[str] = None):
        # Set up data directory
        self.data_dir = Path(data_dir or "roboco_data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize components with persistence
        self.conversation_history = ConversationHistory(
            persist_path=str(self.data_dir / "conversations.json")
        )
        self.event_capture = EventCapture(
            persist_path=str(self.data_dir / "events.json")
        )
        self.memory_viewer = MemoryViewer(
            persist_path=str(self.data_dir / "memory.json")
        )
        
        self.is_running = False
        self.is_integrated = False
        
        # Detect runtime context
        self._detect_context()
        
        if self.is_integrated:
            # Set up event handlers for automatic tracking
            self._setup_automatic_tracking()
            self.event_capture.enable()
            logger.info("Observability monitor initialized (integrated mode)")
        else:
            logger.info("Observability monitor initialized (independent mode)")
    
    def _detect_context(self):
        """Detect if we're running as part of the main server or independently."""
        try:
            # Try to access the global event bus - if it works, we're integrated
            from ..core.event import global_events
            # If we can emit a test event, we're integrated
            test_event = Event("monitor.test", "observability", {})
            global_events.emit(test_event)
            self.is_integrated = True
        except Exception:
            self.is_integrated = False
    
    def _setup_automatic_tracking(self):
        """Set up automatic tracking of key events (only when integrated)."""
        
        def track_agent_messages(event: Event):
            """Track agent messages in conversation history."""
            if event.event_type == "agent.message.sent":
                task_id = event.data.get("task_id", "default")
                agent = event.source
                message = event.data.get("message", "")
                
                self.conversation_history.add_message(task_id, agent, message, "message")
        
        def track_tool_usage(event: Event):
            """Track tool usage in conversation history."""
            if event.event_type in ["tool.started", "tool.completed", "tool.failed"]:
                task_id = event.data.get("task_id", "default")
                agent = event.source
                tool_name = event.data.get("tool_name", "unknown")
                
                if event.event_type == "tool.started":
                    message = f"Started using tool: {tool_name}"
                elif event.event_type == "tool.completed":
                    message = f"Completed tool: {tool_name}"
                else:
                    message = f"Failed tool: {tool_name} - {event.data.get('error', 'Unknown error')}"
                
                self.conversation_history.add_message(task_id, agent, message, "tool")
        
        def track_memory_operations(event: Event):
            """Track memory operations and update viewer."""
            if event.event_type == "memory.saved":
                # Update memory viewer cache
                content = event.data.get("content", "")
                agent = event.source
                key = f"{agent}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                category = event.data.get("category", agent)
                
                self.memory_viewer.update_memory_cache(key, content, category)
        
        # Register event handlers
        global_events.on("agent.message.sent", track_agent_messages)
        global_events.on("tool.started", track_tool_usage)
        global_events.on("tool.completed", track_tool_usage)
        global_events.on("tool.failed", track_tool_usage)
        global_events.on("memory.saved", track_memory_operations)
    
    async def refresh_data(self):
        """Refresh data (load from API if independent, or just return current data if integrated)."""
        if not self.is_integrated:
            # In independent mode, try to load from API if server is running
            try:
                await self.memory_viewer.load_from_memory_api()
            except Exception as e:
                logger.info(f"No API server available, using persisted data: {e}")
    
    def start(self):
        """Start the monitor."""
        self.is_running = True
        logger.info("Observability monitor started")
    
    def stop(self):
        """Stop the monitor."""
        self.is_running = False
        logger.info("Observability monitor stopped")
    
    # API methods for web interface
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard summary data."""
        return {
            "is_integrated": self.is_integrated,
            "is_running": self.is_running,
            "total_events": len(self.event_capture.events) if self.is_integrated else 0,
            "total_tasks": len(self.conversation_history.tasks),
            "total_memory_items": len(self.memory_viewer.memory_cache),
            "memory_categories": len(self.memory_viewer.categories),
            "event_types": self.event_capture.get_event_types() if self.is_integrated else {},
            "recent_tasks": self.conversation_history.get_recent_tasks(5),
            "data_dir": str(self.data_dir)
        }
    
    def get_task_conversation(self, task_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a task."""
        return self.conversation_history.get_task_history(task_id)
    
    async def stream_task_conversation(self, task_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream conversation history for a task (only works when integrated)."""
        if self.is_integrated:
            async for entry in self.conversation_history.stream_task_history(task_id):
                yield entry
        else:
            # Fallback to regular get for independent mode
            history = self.get_task_conversation(task_id)
            for entry in history:
                yield entry
    
    def get_recent_tasks(self, limit: int = 10) -> List[str]:
        """Get recent task IDs."""
        return self.conversation_history.get_recent_tasks(limit)
    
    def get_events(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get events (only works when integrated)."""
        return self.event_capture.get_events(event_type, limit)
    
    def get_event_summary(self) -> Dict[str, int]:
        """Get event summary (only works when integrated)."""
        return self.event_capture.get_event_types()
    
    def get_memory_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        """Get memory by key."""
        return self.memory_viewer.get_memory_by_key(key)
    
    def get_memory_by_category(self, category: str) -> Dict[str, Any]:
        """Get memory by category."""
        return self.memory_viewer.get_memory_by_category(category)
    
    def get_memory_categories(self) -> List[str]:
        """Get all memory categories."""
        return self.memory_viewer.get_all_categories()
    
    def search_memory(self, query: str) -> Dict[str, Any]:
        """Search memory."""
        return self.memory_viewer.search_memory(query)
    
    def get_configuration_data(self) -> Dict[str, Any]:
        """Get system configuration data."""
        try:
            config_data = {
                "system": {
                    "mode": "Integrated" if self.is_integrated else "Independent",
                    "data_directory": str(self.data_dir),
                    "running": self.is_running,
                    "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                    "platform": sys.platform,
                },
                "llm_models": self._get_llm_configuration(),
                "agents": self._get_agent_configuration(),
                "tools": self._get_tools_configuration(),
                "memory": self._get_memory_configuration(),
                "events": self._get_events_configuration(),
            }
            return config_data
        except Exception as e:
            logger.error(f"Failed to get configuration data: {e}")
            return {
                "system": {
                    "mode": "Integrated" if self.is_integrated else "Independent",
                    "data_directory": str(self.data_dir),
                    "running": self.is_running,
                    "error": str(e)
                },
                "llm_models": {},
                "agents": {},
                "tools": {},
                "memory": {},
                "events": {}
            }
    
    def _get_llm_configuration(self) -> Dict[str, Any]:
        """Get LLM configuration from environment and config files."""
        llm_config = {}
        
        # Check for common environment variables
        env_keys = [
            ("OpenAI", "OPENAI_API_KEY"),
            ("DeepSeek", "DEEPSEEK_API_KEY"),
            ("Anthropic", "ANTHROPIC_API_KEY"),
            ("Google", "GOOGLE_API_KEY"),
        ]
        
        for provider, env_key in env_keys:
            api_key = os.getenv(env_key)
            llm_config[provider] = {
                "configured": bool(api_key),
                "api_key_set": bool(api_key),
                "api_key_preview": f"{api_key[:8]}..." if api_key else None
            }
        
        # Try to load from config files
        config_paths = [
            self.data_dir / "config" / "config.yaml",
            Path("config/config.yaml"),
            Path("examples/simple_team/config/config.yaml")
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                try:
                    import yaml
                    with open(config_path, 'r') as f:
                        config = yaml.safe_load(f)
                    
                    if 'llm' in config:
                        llm_config['config_file'] = {
                            "path": str(config_path),
                            "default_model": config['llm'].get('default_model', 'Not specified'),
                            "models": list(config['llm'].get('models', {}).keys()) if 'models' in config['llm'] else []
                        }
                    break
                except Exception as e:
                    logger.debug(f"Could not load config from {config_path}: {e}")
        
        return llm_config
    
    def _get_agent_configuration(self) -> Dict[str, Any]:
        """Get agent configuration."""
        agents_config = {}
        
        # Try to load from config files
        config_paths = [
            self.data_dir / "config",
            Path("config"),
            Path("examples/simple_team/config")
        ]
        
        for config_dir in config_paths:
            if config_dir.exists():
                try:
                    # Look for team config files
                    for config_file in config_dir.glob("*.yaml"):
                        if config_file.name in ["config.yaml", "team.yaml", "default.yaml"]:
                            try:
                                import yaml
                                with open(config_file, 'r') as f:
                                    config = yaml.safe_load(f)
                                
                                if 'agents' in config:
                                    for agent in config['agents']:
                                        agent_name = agent.get('name', 'Unknown')
                                        agents_config[agent_name] = {
                                            "class": agent.get('class', 'Unknown'),
                                            "role": agent.get('role', 'assistant'),
                                            "model": self._extract_model_from_agent(agent),
                                            "tools": agent.get('tools', []),
                                            "config_file": str(config_file)
                                        }
                                break
                            except Exception as e:
                                logger.debug(f"Could not load agent config from {config_file}: {e}")
                    
                    if agents_config:
                        break
                except Exception as e:
                    logger.debug(f"Could not scan config directory {config_dir}: {e}")
        
        return agents_config
    
    def _extract_model_from_agent(self, agent_config: Dict[str, Any]) -> str:
        """Extract model name from agent configuration."""
        llm_config = agent_config.get('llm_config', {})
        if 'config_list' in llm_config and llm_config['config_list']:
            return llm_config['config_list'][0].get('model', 'Unknown')
        return llm_config.get('model', 'Unknown')
    
    def _get_tools_configuration(self) -> Dict[str, Any]:
        """Get tools configuration."""
        tools_config = {
            "available_tools": [],
            "enabled_tools": [],
            "tool_modules": []
        }
        
        # Try to detect available tools
        try:
            import pkgutil
            import roboco.builtin_tools
            
            for importer, modname, ispkg in pkgutil.iter_modules(roboco.builtin_tools.__path__):
                tools_config["tool_modules"].append(modname)
        except Exception as e:
            logger.debug(f"Could not scan tools: {e}")
        
        return tools_config
    
    def _get_memory_configuration(self) -> Dict[str, Any]:
        """Get memory configuration."""
        memory_config = {
            "provider": "Unknown",
            "vector_store": "Unknown",
            "embedder": "Unknown",
            "categories": len(self.get_memory_categories()),
            "total_items": len(self.memory_viewer.memory_cache)
        }
        
        # Try to load from config
        config_paths = [
            self.data_dir / "config" / "config.yaml",
            Path("config/config.yaml"),
            Path("examples/simple_team/config/config.yaml")
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                try:
                    import yaml
                    with open(config_path, 'r') as f:
                        config = yaml.safe_load(f)
                    
                    if 'memory' in config:
                        mem_config = config['memory']
                        memory_config.update({
                            "provider": mem_config.get('vector_store', {}).get('provider', 'Unknown'),
                            "vector_store": mem_config.get('vector_store', {}).get('provider', 'Unknown'),
                            "embedder": mem_config.get('embedder', {}).get('provider', 'Unknown'),
                            "llm_provider": mem_config.get('llm', {}).get('provider', 'Unknown'),
                            "version": mem_config.get('version', 'Unknown')
                        })
                    break
                except Exception as e:
                    logger.debug(f"Could not load memory config from {config_path}: {e}")
        
        return memory_config
    
    def _get_events_configuration(self) -> Dict[str, Any]:
        """Get events configuration."""
        return {
            "integrated_mode": self.is_integrated,
            "capture_enabled": self.event_capture.enabled if hasattr(self, 'event_capture') else False,
            "total_events": len(self.event_capture.events) if hasattr(self, 'event_capture') and self.event_capture.enabled else 0,
            "event_types": len(self.event_capture.event_counts) if hasattr(self, 'event_capture') and self.event_capture.enabled else 0
        }


# Global monitor instance
_monitor_instance: Optional[ObservabilityMonitor] = None

def get_monitor() -> ObservabilityMonitor:
    """Get the global monitor instance."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = ObservabilityMonitor()
    return _monitor_instance 