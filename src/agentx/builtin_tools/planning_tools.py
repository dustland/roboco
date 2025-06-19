"""
Planning and Execution Management Tools - LLM-friendly project planning and tracking.

Provides flexible execution plan management with loose JSON parsing and natural language
queries. Designed to work seamlessly with LLM agents for project planning and tracking.
"""

import json
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from ..tool.models import Tool, tool, ToolResult
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PlanningTool(Tool):
    """
    Generic execution plan management tool for tracking project phases, tasks, and progress.
    
    Features:
    - Loose JSON parsing for plan creation and updates
    - Natural language queries for plan retrieval
    - Flexible task management with status tracking
    - Automatic progress calculation and reporting
    - File-based persistence with versioning
    """
    
    def __init__(self, plan_file: str = "execution_plan.json", workspace_path: str = "./workspace"):
        super().__init__()
        self.workspace_path = Path(workspace_path).resolve()
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        self.plan_file = self.workspace_path / plan_file
        self.plan_data = self._load_plan()
    
    def _load_plan(self) -> Dict[str, Any]:
        """Load execution plan from file with error handling."""
        if not self.plan_file.exists():
            return {
                "_metadata": {
                    "created_at": datetime.now().isoformat(),
                    "version": "1.0",
                    "last_updated": datetime.now().isoformat(),
                    "plan_id": str(uuid.uuid4())[:8]
                },
                "phases": [],
                "overall_status": "not_started",
                "progress": {
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "in_progress_tasks": 0,
                    "percentage_complete": 0.0
                }
            }
        
        try:
            with open(self.plan_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ensure required structure exists
                if "_metadata" not in data:
                    data["_metadata"] = {
                        "created_at": datetime.now().isoformat(),
                        "version": "1.0",
                        "plan_id": str(uuid.uuid4())[:8]
                    }
                if "phases" not in data:
                    data["phases"] = []
                if "progress" not in data:
                    data["progress"] = {
                        "total_tasks": 0,
                        "completed_tasks": 0,
                        "in_progress_tasks": 0,
                        "percentage_complete": 0.0
                    }
                data["_metadata"]["last_updated"] = datetime.now().isoformat()
                return data
        except Exception as e:
            logger.warning(f"Failed to load plan file: {e}. Starting with empty plan.")
            return {
                "_metadata": {
                    "created_at": datetime.now().isoformat(),
                    "version": "1.0",
                    "last_updated": datetime.now().isoformat(),
                    "plan_id": str(uuid.uuid4())[:8],
                    "load_error": str(e)
                },
                "phases": [],
                "overall_status": "not_started",
                "progress": {
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "in_progress_tasks": 0,
                    "percentage_complete": 0.0
                }
            }
    
    def _save_plan(self) -> bool:
        """Save execution plan to file with backup."""
        try:
            # Create backup if file exists
            if self.plan_file.exists():
                backup_file = self.plan_file.with_suffix('.json.bak')
                self.plan_file.rename(backup_file)
            
            # Update metadata and recalculate progress
            self.plan_data["_metadata"]["last_updated"] = datetime.now().isoformat()
            self.plan_data["_metadata"]["version"] = str(float(self.plan_data["_metadata"].get("version", "1.0")) + 0.1)
            self._recalculate_progress()
            
            # Save new file
            with open(self.plan_file, 'w', encoding='utf-8') as f:
                json.dump(self.plan_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            logger.error(f"Failed to save plan: {e}")
            return False
    
    def _parse_loose_json(self, json_str: str) -> Dict[str, Any]:
        """Parse JSON with error tolerance for LLM-generated content."""
        if not json_str.strip():
            return {}
        
        # Try direct JSON parsing first
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        # Try to fix common LLM JSON issues
        try:
            # Remove markdown code blocks
            if json_str.strip().startswith('```'):
                lines = json_str.strip().split('\n')
                json_str = '\n'.join(lines[1:-1]) if len(lines) > 2 else json_str
            
            # Fix single quotes to double quotes
            json_str = json_str.replace("'", '"')
            
            # Try parsing again
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        # Last resort: try to extract structured data
        import re
        
        # Look for phase-like structures
        phase_pattern = r'(?:phase|step|stage)\s*(\d+)?[:\-]?\s*([^\n]+)'
        task_pattern = r'(?:task|action|item)[:\-]?\s*([^\n]+)'
        
        phases = []
        current_phase = None
        
        lines = json_str.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for phase
            phase_match = re.search(phase_pattern, line, re.IGNORECASE)
            if phase_match:
                if current_phase:
                    phases.append(current_phase)
                current_phase = {
                    "name": phase_match.group(2).strip(),
                    "status": "pending",
                    "tasks": []
                }
                continue
            
            # Check for task
            task_match = re.search(task_pattern, line, re.IGNORECASE)
            if task_match and current_phase:
                current_phase["tasks"].append({
                    "id": str(uuid.uuid4())[:8],
                    "description": task_match.group(1).strip(),
                    "status": "pending",
                    "created_at": datetime.now().isoformat()
                })
                continue
            
            # If we have a current phase and this looks like a task
            if current_phase and line and not line.startswith('#'):
                current_phase["tasks"].append({
                    "id": str(uuid.uuid4())[:8],
                    "description": line,
                    "status": "pending",
                    "created_at": datetime.now().isoformat()
                })
        
        if current_phase:
            phases.append(current_phase)
        
        return {"phases": phases} if phases else {}
    
    def _recalculate_progress(self):
        """Recalculate overall progress statistics."""
        total_tasks = 0
        completed_tasks = 0
        in_progress_tasks = 0
        
        for phase in self.plan_data.get("phases", []):
            for task in phase.get("tasks", []):
                total_tasks += 1
                if task.get("status") == "completed":
                    completed_tasks += 1
                elif task.get("status") == "in_progress":
                    in_progress_tasks += 1
        
        percentage_complete = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
        
        self.plan_data["progress"] = {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "percentage_complete": round(percentage_complete, 1)
        }
        
        # Update overall status
        if completed_tasks == total_tasks and total_tasks > 0:
            self.plan_data["overall_status"] = "completed"
        elif in_progress_tasks > 0 or completed_tasks > 0:
            self.plan_data["overall_status"] = "in_progress"
        else:
            self.plan_data["overall_status"] = "not_started"
    
    @tool(description="Create or update execution plan with flexible JSON input")
    async def create_plan(
        self,
        plan_data: str,
        plan_name: str = "",
        replace_existing: bool = False
    ) -> ToolResult:
        """
        Create or update execution plan with loose JSON parsing.
        
        Args:
            plan_data: JSON string or structured text describing the plan
            plan_name: Optional name for the plan
            replace_existing: Whether to replace existing plan or merge
        
        Returns:
            ToolResult with success status and plan summary
        """
        try:
            # Parse the plan data with error tolerance
            parsed_data = self._parse_loose_json(plan_data)
            
            if not parsed_data:
                return ToolResult(
                    success=False,
                    result=None,
                    error="No valid plan data found in input"
                )
            
            if replace_existing:
                # Keep metadata but replace plan content
                metadata = self.plan_data.get("_metadata", {})
                self.plan_data = {
                    "_metadata": metadata,
                    "phases": [],
                    "overall_status": "not_started",
                    "progress": {
                        "total_tasks": 0,
                        "completed_tasks": 0,
                        "in_progress_tasks": 0,
                        "percentage_complete": 0.0
                    }
                }
            
            # Add plan name if provided
            if plan_name:
                self.plan_data["plan_name"] = plan_name
            
            # Process phases
            if "phases" in parsed_data:
                for phase_data in parsed_data["phases"]:
                    phase = {
                        "id": str(uuid.uuid4())[:8],
                        "name": phase_data.get("name", "Unnamed Phase"),
                        "description": phase_data.get("description", ""),
                        "status": phase_data.get("status", "pending"),
                        "created_at": datetime.now().isoformat(),
                        "tasks": []
                    }
                    
                    # Process tasks in this phase
                    for task_data in phase_data.get("tasks", []):
                        if isinstance(task_data, str):
                            task = {
                                "id": str(uuid.uuid4())[:8],
                                "description": task_data,
                                "status": "pending",
                                "created_at": datetime.now().isoformat()
                            }
                        else:
                            task = {
                                "id": task_data.get("id", str(uuid.uuid4())[:8]),
                                "description": task_data.get("description", ""),
                                "status": task_data.get("status", "pending"),
                                "created_at": task_data.get("created_at", datetime.now().isoformat()),
                                "estimated_hours": task_data.get("estimated_hours"),
                                "assigned_to": task_data.get("assigned_to"),
                                "deliverable": task_data.get("deliverable"),
                                "success_criteria": task_data.get("success_criteria")
                            }
                        phase["tasks"].append(task)
                    
                    self.plan_data["phases"].append(phase)
            
            # Save to file
            saved = self._save_plan()
            
            # Create summary
            total_phases = len(self.plan_data["phases"])
            total_tasks = sum(len(phase["tasks"]) for phase in self.plan_data["phases"])
            
            summary = {
                "plan_created": True,
                "plan_name": self.plan_data.get("plan_name", "Unnamed Plan"),
                "total_phases": total_phases,
                "total_tasks": total_tasks,
                "plan_id": self.plan_data["_metadata"]["plan_id"],
                "saved_to_file": saved
            }
            
            return ToolResult(
                success=True,
                result=summary,
                metadata={"plan_file": str(self.plan_file)}
            )
            
        except Exception as e:
            logger.error(f"Failed to create plan: {e}")
            return ToolResult(
                success=False,
                result=None,
                error=f"Plan creation failed: {str(e)}"
            )
    
    @tool(description="Update task status and progress")
    async def update_task_status(
        self,
        task_query: str,
        new_status: str,
        notes: str = ""
    ) -> ToolResult:
        """
        Update task status with flexible task identification.
        
        Args:
            task_query: Task ID, description, or natural language query to find task
            new_status: New status - "pending", "in_progress", "completed", "blocked"
            notes: Optional notes about the status change
        
        Returns:
            ToolResult with update status and task details
        """
        try:
            # Find the task
            found_tasks = []
            task_query_lower = task_query.lower()
            
            for phase in self.plan_data.get("phases", []):
                for task in phase.get("tasks", []):
                    # Check if query matches task ID or description
                    if (task.get("id") == task_query or 
                        task_query_lower in task.get("description", "").lower()):
                        found_tasks.append((phase, task))
            
            if not found_tasks:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"No task found matching query: {task_query}"
                )
            
            if len(found_tasks) > 1:
                # Multiple matches - return options
                options = []
                for phase, task in found_tasks:
                    options.append({
                        "task_id": task["id"],
                        "description": task["description"],
                        "phase": phase["name"],
                        "current_status": task.get("status", "pending")
                    })
                
                return ToolResult(
                    success=False,
                    result={"multiple_matches": options},
                    error="Multiple tasks found. Please be more specific or use task ID."
                )
            
            # Update the single found task
            phase, task = found_tasks[0]
            old_status = task.get("status", "pending")
            task["status"] = new_status
            task["last_updated"] = datetime.now().isoformat()
            
            if notes:
                if "notes" not in task:
                    task["notes"] = []
                task["notes"].append({
                    "timestamp": datetime.now().isoformat(),
                    "note": notes,
                    "status_change": f"{old_status} → {new_status}"
                })
            
            # Save changes
            saved = self._save_plan()
            
            result = {
                "task_updated": True,
                "task_id": task["id"],
                "description": task["description"],
                "phase": phase["name"],
                "old_status": old_status,
                "new_status": new_status,
                "progress": self.plan_data["progress"],
                "saved_to_file": saved
            }
            
            return ToolResult(
                success=True,
                result=result,
                metadata={"task_id": task["id"], "phase_id": phase["id"]}
            )
            
        except Exception as e:
            logger.error(f"Failed to update task status: {e}")
            return ToolResult(
                success=False,
                result=None,
                error=f"Task status update failed: {str(e)}"
            )
    
    @tool(description="Get plan status and progress with flexible querying")
    async def get_plan_status(
        self,
        query: str = "",
        include_completed: bool = True,
        format_output: str = "summary"
    ) -> ToolResult:
        """
        Get plan status and progress with flexible querying.
        
        Args:
            query: Natural language query to filter results (empty for all)
            include_completed: Whether to include completed tasks
            format_output: Output format - "summary", "detailed", "progress_only"
        
        Returns:
            ToolResult with plan status and progress information
        """
        try:
            if format_output == "progress_only":
                return ToolResult(
                    success=True,
                    result=self.plan_data["progress"],
                    metadata={"overall_status": self.plan_data.get("overall_status")}
                )
            
            # Filter phases and tasks based on query
            filtered_phases = []
            query_lower = query.lower() if query else ""
            
            for phase in self.plan_data.get("phases", []):
                # Check if phase matches query
                phase_matches = not query or query_lower in phase.get("name", "").lower()
                
                # Filter tasks
                filtered_tasks = []
                for task in phase.get("tasks", []):
                    # Skip completed tasks if not requested
                    if not include_completed and task.get("status") == "completed":
                        continue
                    
                    # Check if task matches query
                    task_matches = (not query or 
                                  query_lower in task.get("description", "").lower() or
                                  query_lower in task.get("status", "").lower())
                    
                    if phase_matches or task_matches:
                        filtered_tasks.append(task)
                
                if filtered_tasks or phase_matches:
                    phase_copy = phase.copy()
                    phase_copy["tasks"] = filtered_tasks
                    filtered_phases.append(phase_copy)
            
            if format_output == "summary":
                # Create summary format
                summary = {
                    "plan_name": self.plan_data.get("plan_name", "Unnamed Plan"),
                    "plan_id": self.plan_data["_metadata"]["plan_id"],
                    "overall_status": self.plan_data.get("overall_status"),
                    "progress": self.plan_data["progress"],
                    "total_phases": len(filtered_phases),
                    "phases_summary": []
                }
                
                for phase in filtered_phases:
                    phase_summary = {
                        "name": phase["name"],
                        "status": phase.get("status", "pending"),
                        "total_tasks": len(phase["tasks"]),
                        "completed_tasks": len([t for t in phase["tasks"] if t.get("status") == "completed"]),
                        "in_progress_tasks": len([t for t in phase["tasks"] if t.get("status") == "in_progress"])
                    }
                    summary["phases_summary"].append(phase_summary)
                
                result = summary
            else:  # detailed
                result = {
                    "plan_name": self.plan_data.get("plan_name", "Unnamed Plan"),
                    "plan_id": self.plan_data["_metadata"]["plan_id"],
                    "overall_status": self.plan_data.get("overall_status"),
                    "progress": self.plan_data["progress"],
                    "last_updated": self.plan_data["_metadata"]["last_updated"],
                    "phases": filtered_phases
                }
            
            return ToolResult(
                success=True,
                result=result,
                metadata={
                    "query": query,
                    "format": format_output,
                    "total_phases": len(filtered_phases)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to get plan status: {e}")
            return ToolResult(
                success=False,
                result=None,
                error=f"Plan status retrieval failed: {str(e)}"
            )
    
    @tool(description="Add new task to existing phase")
    async def add_task(
        self,
        phase_query: str,
        task_description: str,
        task_details: str = ""
    ) -> ToolResult:
        """
        Add a new task to an existing phase.
        
        Args:
            phase_query: Phase name or ID to add task to
            task_description: Description of the new task
            task_details: Optional JSON string with additional task details
        
        Returns:
            ToolResult with task creation status
        """
        try:
            # Find the phase
            found_phase = None
            phase_query_lower = phase_query.lower()
            
            for phase in self.plan_data.get("phases", []):
                if (phase.get("id") == phase_query or 
                    phase_query_lower in phase.get("name", "").lower()):
                    found_phase = phase
                    break
            
            if not found_phase:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"No phase found matching query: {phase_query}"
                )
            
            # Create new task
            new_task = {
                "id": str(uuid.uuid4())[:8],
                "description": task_description,
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }
            
            # Add optional details
            if task_details:
                try:
                    details = self._parse_loose_json(task_details)
                    new_task.update(details)
                except:
                    # If parsing fails, add as notes
                    new_task["notes"] = [{"timestamp": datetime.now().isoformat(), "note": task_details}]
            
            # Add task to phase
            found_phase["tasks"].append(new_task)
            
            # Save changes
            saved = self._save_plan()
            
            result = {
                "task_added": True,
                "task_id": new_task["id"],
                "description": task_description,
                "phase": found_phase["name"],
                "phase_id": found_phase["id"],
                "saved_to_file": saved
            }
            
            return ToolResult(
                success=True,
                result=result,
                metadata={"task_id": new_task["id"], "phase_id": found_phase["id"]}
            )
            
        except Exception as e:
            logger.error(f"Failed to add task: {e}")
            return ToolResult(
                success=False,
                result=None,
                error=f"Task addition failed: {str(e)}"
            )