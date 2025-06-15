"""
AgentX Observability Monitor

Read-only observability system that monitors AgentX project data:
- Reads workspace data from {project_path}/workspace/
- Reads configuration from {project_path}/config/
- Provides web interface for viewing project data
- Does NOT create or modify any files
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict
from pathlib import Path

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ProjectStorage:
    """Read-only project-based storage for observability."""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.workspace_dir = self.project_path / "workspace"
        self.config_dir = self.project_path / "config"
        
    def _get_workspace_file_path(self, filename: str) -> Path:
        """Get full path for a workspace data file."""
        if not filename.endswith('.json'):
            filename += '.json'
        return self.workspace_dir / filename
    
    def _get_config_file_path(self, filename: str) -> Path:
        """Get full path for a config file."""
        return self.config_dir / filename
    
    def read_workspace_file(self, filename: str) -> Dict[str, Any]:
        """Read data from workspace file."""
        file_path = self._get_workspace_file_path(filename)
        
        if not file_path.exists():
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Remove metadata for clean data
                data.pop('_metadata', None)
                return data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to read workspace file {filename}: {e}")
            return {}
    
    def read_config_file(self, filename: str) -> Dict[str, Any]:
        """Read data from config file."""
        file_path = self._get_config_file_path(filename)
        
        if not file_path.exists():
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if filename.endswith('.json'):
                    return json.load(f)
                else:
                    # For non-JSON config files, return as text
                    return {"content": f.read()}
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to read config file {filename}: {e}")
            return {}
    
    def workspace_file_exists(self, filename: str) -> bool:
        """Check if workspace file exists."""
        return self._get_workspace_file_path(filename).exists()
    
    def config_file_exists(self, filename: str) -> bool:
        """Check if config file exists."""
        return self._get_config_file_path(filename).exists()
    
    def get_workspace_file_info(self, filename: str) -> Dict[str, Any]:
        """Get workspace file information."""
        file_path = self._get_workspace_file_path(filename)
        if not file_path.exists():
            return {"exists": False}
        
        try:
            stat = file_path.stat()
            return {
                "exists": True,
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting workspace file info for {filename}: {e}")
            return {"exists": True, "error": str(e)}
    
    def get_config_file_info(self, filename: str) -> Dict[str, Any]:
        """Get config file information."""
        file_path = self._get_config_file_path(filename)
        if not file_path.exists():
            return {"exists": False}
        
        try:
            stat = file_path.stat()
            return {
                "exists": True,
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting config file info for {filename}: {e}")
            return {"exists": True, "error": str(e)}
    
    def list_workspace_files(self) -> List[str]:
        """List all files in workspace directory."""
        if not self.workspace_dir.exists():
            return []
        
        try:
            return [f.name for f in self.workspace_dir.iterdir() if f.is_file()]
        except Exception as e:
            logger.error(f"Error listing workspace files: {e}")
            return []
    
    def list_config_files(self) -> List[str]:
        """List all files in config directory."""
        if not self.config_dir.exists():
            return []
        
        try:
            return [f.name for f in self.config_dir.iterdir() if f.is_file()]
        except Exception as e:
            logger.error(f"Error listing config files: {e}")
            return []


class ConversationHistory:
    """Read conversation history from workspace/conversations.json."""
    
    def __init__(self, storage: ProjectStorage):
        self.storage = storage
        self.filename = "conversations"
    
    def get_conversation(self, task_id: str) -> List[Dict[str, Any]]:
        """Get conversation for a task."""
        data = self.storage.read_workspace_file(self.filename)
        return data.get("tasks", {}).get(task_id, [])
    
    def get_recent_tasks(self, limit: int = 10) -> List[str]:
        """Get list of recent task IDs."""
        data = self.storage.read_workspace_file(self.filename)
        tasks = data.get("tasks", {})
        
        # Sort by last message timestamp
        task_times = []
        for task_id, messages in tasks.items():
            if messages:
                last_msg = messages[-1]
                timestamp = last_msg.get('timestamp', '1970-01-01T00:00:00')
                task_times.append((timestamp, task_id))
        
        task_times.sort(reverse=True)
        return [task_id for _, task_id in task_times[:limit]]
    
    def get_task_summary(self, task_id: str) -> Dict[str, Any]:
        """Get summary of a task."""
        messages = self.get_conversation(task_id)
        if not messages:
            return {"task_id": task_id, "message_count": 0}
        
        first_msg = messages[0]
        last_msg = messages[-1]
        
        return {
            "task_id": task_id,
            "message_count": len(messages),
            "started_at": first_msg.get('timestamp'),
            "last_activity": last_msg.get('timestamp'),
            "agents_involved": list(set(msg.get('agent_name', 'unknown') for msg in messages if msg.get('agent_name')))
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get conversation statistics."""
        data = self.storage.read_workspace_file(self.filename)
        tasks = data.get("tasks", {})
        
        if not tasks:
            return {"total_tasks": 0, "total_messages": 0}
        
        total_messages = sum(len(messages) for messages in tasks.values())
        agents = set()
        
        for messages in tasks.values():
            for msg in messages:
                if msg.get('agent_name'):
                    agents.add(msg['agent_name'])
        
        return {
            "total_tasks": len(tasks),
            "total_messages": total_messages,
            "unique_agents": len(agents),
            "agent_names": sorted(list(agents))
        }


class EventCapture:
    """Read events from workspace/events.json."""
    
    def __init__(self, storage: ProjectStorage):
        self.storage = storage
        self.filename = "events"
    
    def get_events(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent events."""
        data = self.storage.read_workspace_file(self.filename)
        events = data.get("events", [])
        
        if event_type:
            events = [e for e in events if e.get("event_type") == event_type]
        
        return events[-limit:]
    
    def get_event_stats(self) -> Dict[str, Any]:
        """Get event statistics."""
        data = self.storage.read_workspace_file(self.filename)
        events = data.get("events", [])
        
        if not events:
            return {"total_events": 0, "event_types": {}}
        
        event_types = defaultdict(int)
        for event in events:
            event_types[event.get("event_type", "unknown")] += 1
        
        return {
            "total_events": len(events),
            "event_types": dict(event_types),
            "oldest_event": events[0].get("timestamp") if events else None,
            "newest_event": events[-1].get("timestamp") if events else None
        }
    
    def get_events_by_type(self, event_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get events of a specific type."""
        return self.get_events(event_type, limit)


class ArtifactsViewer:
    """Browse and view workspace files as artifacts."""
    
    def __init__(self, storage: ProjectStorage):
        self.storage = storage
    
    def get_file_list(self) -> List[Dict[str, Any]]:
        """Get list of all workspace files."""
        files = []
        workspace_files = self.storage.list_workspace_files()
        
        for filename in workspace_files:
            try:
                file_info = self.storage.get_workspace_file_info(filename)
                files.append({
                    "name": filename,
                    "path": filename,
                    "type": "file",
                    "size": file_info.get("size_human", "0 B"),
                    "size_bytes": file_info.get("size_bytes", 0),
                    "modified": file_info.get("last_modified", "Unknown"),
                    "is_text": self._is_text_file(filename)
                })
            except Exception as e:
                logger.warning(f"Error getting info for file {filename}: {e}")
                files.append({
                    "name": filename,
                    "path": filename,
                    "type": "file",
                    "size": "Unknown",
                    "size_bytes": 0,
                    "modified": "Unknown",
                    "is_text": self._is_text_file(filename)
                })
        
        return sorted(files, key=lambda x: x["name"])
    
    def get_file_content(self, filename: str) -> Dict[str, Any]:
        """Get file content and metadata."""
        try:
            file_info = self.storage.get_workspace_file_info(filename)
            is_text = self._is_text_file(filename)
            
            if is_text:
                # Try to read as text
                try:
                    if filename.endswith('.json'):
                        # For JSON files, read as dict and format nicely
                        content_dict = self.storage.read_workspace_file(filename)
                        import json
                        content = json.dumps(content_dict, indent=2, ensure_ascii=False)
                    else:
                        # For other text files, read raw content
                        file_path = self.storage._get_workspace_file_path(filename)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    
                    lines = len(content.split('\n'))
                    
                    return {
                        "success": True,
                        "content": content,
                        "file_info": {
                            **file_info,
                            "is_text": True,
                            "lines": lines,
                            "mime_type": self._get_mime_type(filename)
                        }
                    }
                except UnicodeDecodeError:
                    # File is not actually text
                    is_text = False
            
            if not is_text:
                return {
                    "success": True,
                    "content": None,
                    "file_info": {
                        **file_info,
                        "is_text": False,
                        "mime_type": self._get_mime_type(filename)
                    }
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_artifacts_stats(self) -> Dict[str, Any]:
        """Get artifacts statistics."""
        files = self.get_file_list()
        
        total_files = len(files)
        total_size_bytes = sum(f["size_bytes"] for f in files)
        text_files = sum(1 for f in files if f["is_text"])
        
        # Format total size
        if total_size_bytes < 1024:
            total_size = f"{total_size_bytes} B"
        elif total_size_bytes < 1024 * 1024:
            total_size = f"{total_size_bytes / 1024:.1f} KB"
        elif total_size_bytes < 1024 * 1024 * 1024:
            total_size = f"{total_size_bytes / (1024 * 1024):.1f} MB"
        else:
            total_size = f"{total_size_bytes / (1024 * 1024 * 1024):.1f} GB"
        
        # Get most recent modification time
        last_modified = "Unknown"
        if files:
            try:
                from datetime import datetime
                modified_times = [f["modified"] for f in files if f["modified"] != "Unknown"]
                if modified_times:
                    # Assuming ISO format timestamps
                    latest = max(modified_times)
                    last_modified = latest
            except Exception:
                pass
        
        return {
            "total_files": total_files,
            "total_size": total_size,
            "text_files": text_files,
            "binary_files": total_files - text_files,
            "last_modified": last_modified
        }
    
    def _is_text_file(self, filename: str) -> bool:
        """Check if file is likely a text file based on extension."""
        text_extensions = {
            '.txt', '.json', '.yaml', '.yml', '.md', '.py', '.js', '.html', '.css',
            '.xml', '.csv', '.log', '.conf', '.cfg', '.ini', '.toml', '.sh', '.bat'
        }
        
        import os
        _, ext = os.path.splitext(filename.lower())
        return ext in text_extensions or not ext  # Files without extension might be text
    
    def _get_mime_type(self, filename: str) -> str:
        """Get MIME type for file."""
        import os
        _, ext = os.path.splitext(filename.lower())
        
        mime_types = {
            '.json': 'application/json',
            '.yaml': 'application/x-yaml',
            '.yml': 'application/x-yaml',
            '.md': 'text/markdown',
            '.py': 'text/x-python',
            '.js': 'text/javascript',
            '.html': 'text/html',
            '.css': 'text/css',
            '.xml': 'application/xml',
            '.csv': 'text/csv',
            '.log': 'text/plain',
            '.txt': 'text/plain'
        }
        
        return mime_types.get(ext, 'text/plain' if self._is_text_file(filename) else 'application/octet-stream')


class ConfigViewer:
    """Read configuration files from config/ directory."""
    
    def __init__(self, storage: ProjectStorage):
        self.storage = storage
    
    def get_config_files(self) -> List[str]:
        """Get list of config files."""
        return self.storage.list_config_files()
    
    def get_config_file(self, filename: str) -> Dict[str, Any]:
        """Get specific config file content."""
        return self.storage.read_config_file(filename)
    
    def get_config_file_info(self, filename: str) -> Dict[str, Any]:
        """Get config file information."""
        return self.storage.get_config_file_info(filename)


class ObservabilityMonitor:
    """Read-only observability monitor for AgentX project data."""
    
    def __init__(self, project_path: Optional[str] = None):
        self.project_path = project_path or "."
        self.storage = ProjectStorage(self.project_path)
        
        # Initialize read-only components
        self.conversation_history = ConversationHistory(self.storage)
        self.event_capture = EventCapture(self.storage)
        self.artifacts_viewer = ArtifactsViewer(self.storage)
        self.config_viewer = ConfigViewer(self.storage)
        
        self.is_running = False
        self.last_refresh = None
        
        logger.info(f"Read-only observability monitor initialized for project: {self.project_path}")
    
    def start(self):
        """Start the monitor."""
        self.is_running = True
        self.last_refresh = datetime.now()
        logger.info("Observability monitor started (read-only mode)")
    
    def stop(self):
        """Stop the monitor."""
        self.is_running = False
        logger.info("Observability monitor stopped")
    
    def refresh(self):
        """Refresh data (just updates timestamp since we read files on demand)."""
        self.last_refresh = datetime.now()
    
    def get_project_status(self) -> Dict[str, Any]:
        """Get status of the project directories."""
        project_path = Path(self.project_path)
        workspace_path = project_path / "workspace"
        config_path = project_path / "config"
        
        return {
            "project_path": str(project_path.absolute()),
            "workspace": {
                "exists": workspace_path.exists(),
                "path": str(workspace_path),
                "files": self.storage.list_workspace_files() if workspace_path.exists() else []
            },
            "config": {
                "exists": config_path.exists(),
                "path": str(config_path),
                "files": self.storage.list_config_files() if config_path.exists() else []
            }
        }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        try:
            return {
                "system": {
                    "is_running": self.is_running,
                    "project_path": self.project_path,
                    "last_refresh": self.last_refresh.isoformat() if self.last_refresh else None,
                    "project_status": self.get_project_status()
                },
                "conversations": self.conversation_history.get_stats(),
                "events": self.event_capture.get_event_stats(),
                "artifacts": self.artifacts_viewer.get_artifacts_stats()
            }
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {"error": str(e)}
    
    # Conversation methods
    def get_task_conversation(self, task_id: str) -> List[Dict[str, Any]]:
        """Get conversation for a specific task."""
        return self.conversation_history.get_conversation(task_id)
    
    def get_recent_tasks(self, limit: int = 10) -> List[str]:
        """Get recent task IDs."""
        return self.conversation_history.get_recent_tasks(limit)
    
    # Artifacts methods
    def get_artifacts_files(self) -> List[Dict[str, Any]]:
        """Get list of artifact files."""
        return self.artifacts_viewer.get_file_list()
    
    def get_artifact_content(self, filename: str) -> Dict[str, Any]:
        """Get artifact file content."""
        return self.artifacts_viewer.get_file_content(filename)
    
    def get_artifacts_stats(self) -> Dict[str, Any]:
        """Get artifacts statistics."""
        return self.artifacts_viewer.get_artifacts_stats()
    
    # Event methods
    def get_events(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get events."""
        return self.event_capture.get_events(event_type, limit)
    
    # Config methods
    def get_config_files(self) -> List[str]:
        """Get list of config files."""
        return self.config_viewer.get_config_files()
    
    def get_config_file(self, filename: str) -> Dict[str, Any]:
        """Get config file content."""
        return self.config_viewer.get_config_file(filename)
    
    def get_configuration_data(self) -> Dict[str, Any]:
        """Get configuration data for the web interface."""
        import sys
        import platform
        
        return {
            "project_path": self.project_path,
            "system": {
                "project_path": self.project_path,
                "python_version": sys.version.split()[0],
                "platform": platform.system(),
                "is_running": self.is_running,
                "mode": "Read-Only Project Monitor",
                "data_directory": str(self.storage.workspace_dir)
            },
            "storage": {
                "workspace_dir": str(self.storage.workspace_dir),
                "config_dir": str(self.storage.config_dir),
                "conversations_file": str(self.storage._get_workspace_file_path("conversations")),
                "events_file": str(self.storage._get_workspace_file_path("events")),
                "memory_file": str(self.storage._get_workspace_file_path("memory"))
            },
            "project_status": self.get_project_status()
        }


def get_monitor(project_path: Optional[str] = None) -> ObservabilityMonitor:
    """Get or create observability monitor instance."""
    if not hasattr(get_monitor, '_instance'):
        get_monitor._instance = ObservabilityMonitor(project_path)
    return get_monitor._instance


def find_project_directory() -> str:
    """Find existing project directory with workspace and config subdirectories."""
    current_dir = Path.cwd()
    
    # Check current directory
    if (current_dir / "workspace").exists() and (current_dir / "config").exists():
        return str(current_dir)
    
    # Check parent directories
    for parent in [current_dir.parent, current_dir.parent.parent, current_dir.parent.parent.parent]:
        if parent == current_dir:
            break
        if (parent / "workspace").exists() and (parent / "config").exists():
            return str(parent)
    
    # Return current directory as default
    return str(current_dir) 