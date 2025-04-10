"""
Task Manager Module

This module provides functionality for managing tasks, including parsing, 
updating, executing, and tracking task completion.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
import markdown
from bs4 import BeautifulSoup
import os
import asyncio
import traceback

from roboco.core.fs import ProjectFS
from roboco.core.models.task import TaskStatus
from roboco.core.models import Task
from roboco.core.team_manager import TeamManager
from loguru import logger

from roboco.utils.id_generator import generate_short_id

logger = logger.bind(module=__name__)


class TaskManager:
    """Component for parsing, updating, executing, and managing tasks."""
    
    def __init__(self, fs: ProjectFS):
        """Initialize the task manager.
        
        Args:
            fs: ProjectFS instance for file operations
        """
        self.fs = fs
        
        # Initialize team manager for task execution
        self.team_manager = TeamManager(fs=fs)
        
        # Import FileSystemTool here to avoid circular imports
        from roboco.tools.fs import FileSystemTool
        self.file_tool = FileSystemTool(fs)
        
        # Log initialization without accessing potentially missing attributes
        logger.debug(f"Initialized TaskManager")
    
    def parse_tasks_from_markdown(self, markdown_content: str, project_id: str) -> List[Task]:
        """
        Parse tasks from markdown format into Task objects.
        
        Uses the markdown package to convert markdown to HTML, then
        BeautifulSoup to parse the HTML structure for tasks.
        
        Args:
            markdown_content: Markdown content containing task definitions
            project_id: ID of the project the tasks belong to
            
        Returns:
            List of Task objects
        """
        tasks = []
        
        # Convert markdown to HTML and parse with BeautifulSoup
        html = markdown.markdown(markdown_content)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all h2 headers (## Task: Title)
        h2_elements = soup.find_all('h2')
        
        for h2 in h2_elements:
            # Handle both old format (status in heading) and new format (status after heading)
            title_text = ""
            status = TaskStatus.TODO  # Default status
            
            # Check if we have the old format with status in heading
            if '[x]' in h2.text or '[ ]' in h2.text:
                # Old format: extract status from heading
                status = TaskStatus.COMPLETED if '[x]' in h2.text else TaskStatus.TODO
                # Clean up the title text
                title_text = h2.text.replace('[x]', '').replace('[ ]', '').replace('Task:', '').strip()
            elif 'Task:' in h2.text:
                # New format: extract title only from heading
                title_text = h2.text.replace('Task:', '').strip()
            else:
                # Not a task heading, skip it
                continue
                
            # Find next sibling elements to find status indicator, description and details
            current = h2.next_sibling
            description = title_text  # Default to title if no description found
            details = []
            desc_found = False
            status_found = False
            
            # Process elements after the heading
            while current and not (current.name == 'h2'):
                # Check if this is the status indicator line (only for new format)
                if not status_found and current.name and current.text and ('[x]' in current.text or '[ ]' in current.text):
                    status = TaskStatus.COMPLETED if '[x]' in current.text else TaskStatus.TODO
                    status_found = True
                # Otherwise, if it's a paragraph and we haven't found description yet, treat as description
                elif current.name == 'p' and not desc_found:
                    # Skip the status indicator paragraph
                    if not ('[x]' in current.text or '[ ]' in current.text):
                        description = current.text.strip()
                        desc_found = True
                # If it's a list, extract detail points
                elif current.name == 'ul':
                    for li in current.find_all('li'):
                        details.append(li.text.strip())
                current = current.next_sibling
            
            # Create task metadata
            meta = {"details": details} if details else {}
            
            # Create the Task object
            task = Task(
                id=generate_short_id(),
                title=title_text,
                description=description,
                status=status,
                project_id=project_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                meta=meta
            )
            
            tasks.append(task)
        
        logger.info(f"Parsed {len(tasks)} tasks from markdown using HTML parsing")
        return tasks
    
    def tasks_to_markdown(self, tasks: List[Task], project_name: str) -> str:
        """
        Convert Task objects to markdown format.
        
        Args:
            tasks: List of Task objects
            project_name: Name of the project for the markdown header
            
        Returns:
            Markdown string representation of the tasks
        """
        lines = [f"# Tasks for {project_name}", ""]
        
        for task in tasks:
            # Add the heading first, then the checkbox as a separate element
            lines.append(f"## Task: {task.title}")
            
            # Add status indicator on the next line, not inside the heading
            status_indicator = "x" if task.status == TaskStatus.COMPLETED else " "
            lines.append(f"- [{status_indicator}] Status: {'Completed' if task.status == TaskStatus.COMPLETED else 'Todo'}")
            lines.append("")
            
            # Add description
            lines.append(f"{task.description}")
            lines.append("")
            
            # Add details
            details = task.meta.get("details", []) if task.meta else []
            if details:
                for detail in details:
                    lines.append(f"- {detail}")
                lines.append("")
        
        return "\n".join(lines)
    
    def update_task_status(self, task: Task, status: TaskStatus, meta_updates: Optional[Dict[str, Any]] = None) -> Task:
        """
        Update a task's status and metadata in the database.
        
        Args:
            task: The task to update
            status: New status to set
            meta_updates: Optional dictionary of metadata updates to apply
            
        Returns:
            The updated task
        """
        # Import DB operations here to avoid circular imports
        from roboco.db.service import update_task
        
        # Update task status
        task.status = status
        
        # Set completed_at timestamp if completing the task
        if status == TaskStatus.COMPLETED and not task.completed_at:
            task.completed_at = datetime.utcnow()
        
        # Update timestamp
        task.updated_at = datetime.utcnow()
        
        # Update metadata if provided
        if meta_updates:
            task.meta = task.meta or {}
            task.meta.update(meta_updates)
        
        # Update the task in the database
        updated_task = update_task(task.id, task)
        
        logger.info(f"Updated task {task.id} status to {status.value}")
        return updated_task
    
    def mark_task_completed(self, task: Task, details: Optional[str] = None) -> Task:
        """
        Mark a specific task as completed in the database.
        
        Args:
            task: The task to mark as completed
            details: Optional completion details to add to metadata
            
        Returns:
            The updated task
        """
        meta_updates = None
        if details:
            meta_updates = {"completion_details": details}
            
        return self.update_task_status(
            task=task,
            status=TaskStatus.COMPLETED,
            meta_updates=meta_updates
        )
    
    def mark_task_failed(self, task: Task, error: str, error_details: Optional[str] = None) -> Task:
        """
        Mark a specific task as failed in the database.
        
        Args:
            task: The task to mark as failed
            error: Error message
            error_details: Optional error details/traceback
            
        Returns:
            The updated task
        """
        meta_updates = {
            "error": error,
            "failed_at": datetime.utcnow().isoformat()
        }
        
        if error_details:
            meta_updates["error_details"] = error_details
            
        return self.update_task_status(
            task=task,
            status=TaskStatus.FAILED,
            meta_updates=meta_updates
        )
    
    def load_tasks(self, project_id: str) -> List[Task]:
        """
        Load tasks from the database for a project.
        
        Args:
            project_id: ID of the project to load tasks for
            
        Returns:
            List of Task objects
        """
        from roboco.db.service import get_tasks_by_project
        return get_tasks_by_project(project_id)
    
    def create_task(self, title: str, description: str, project_id: str, 
                   status: TaskStatus = TaskStatus.TODO, 
                   details: Optional[List[str]] = None) -> Task:
        """
        Create a new task in the database.
        
        Args:
            title: Title of the task
            description: Detailed description of the task
            project_id: ID of the project this task belongs to
            status: Task status (default: TODO)
            details: Optional list of detailed points for the task
            
        Returns:
            The created Task object
        """
        from roboco.db.service import create_task
        from roboco.utils.id_generator import generate_short_id
        from datetime import datetime
        
        # Create task metadata with details if provided
        meta = {}
        if details:
            meta["details"] = details
        
        # Create the task object
        task = Task(
            id=generate_short_id(),
            title=title,
            description=description,
            status=status,
            project_id=project_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            meta=meta
        )
        
        # Save to database
        created_task = create_task(project_id, task)
        logger.info(f"Created task '{title}' for project {project_id}")
        
        return created_task
    
    def _generate_task_context(self, current_task: Task, tasks: List[Task], project_info: Dict[str, Any]) -> str:
        """
        Generate context information about a task and its project.
        
        Args:
            current_task: The current task being executed
            tasks: List of all tasks in the project
            project_info: Dictionary with project information
            
        Returns:
            String containing formatted context information
        """
        context_parts = []
        
        # Ensure current_task and project_info are valid
        if not current_task:
            logger.warning("No current task provided for context generation")
            return "No task context available."
            
        if not project_info:
            logger.warning("No project info provided for context generation")
            project_info = {"id": "unknown", "name": "Unknown Project", "description": "No description available"}
        
        # Add current task information
        context_parts.append(f"Current task: {current_task.title}")
        context_parts.append(f"Description: {current_task.description}")
        
        # Add other tasks for context
        task_summaries = []
        
        # Ensure tasks is a list
        if tasks is None:
            tasks = []
            
        try:
            for task in tasks:
                if task.description != current_task.description:
                    status = "COMPLETED" if task.status == TaskStatus.COMPLETED else "TODO"
                    task_summaries.append(f"- {task.description} [{status}]")
        except (AttributeError, TypeError) as e:
            logger.warning(f"Error processing tasks list: {str(e)}")
        
        if task_summaries:
            context_parts.append("\nOther tasks in project:")
            context_parts.extend(task_summaries)
        
        # Add project information
        context_parts.append(f"\nProject ID: {project_info.get('id', 'unknown')}")
        if project_info.get('name'):
            context_parts.append(f"Project name: {project_info.get('name')}")
        
        # Return the joined context parts
        return "\n".join(context_parts)
    
    def create_header(self, text: str, style: str = "task", status: Optional[str] = None) -> str:
        """
        Create a visually distinct header with consistent styling.
        
        Args:
            text: The text to display in the header
            style: The header style ("task", "complete", or "batch")
            status: Optional status indicator for completion headers
            
        Returns:
            A formatted header string
        """
        if style == "task":
            separator = "=" * 80
            heading = f" EXECUTING TASK: {text} "
            symbol = ""
        elif style == "complete":
            separator = "-" * 80
            status_symbol = "✅" if status == "completed" else "❌" if status == "failed" else "⏩"
            heading = f" {status_symbol} TASK COMPLETE: {text} [{status.upper()}] "
            symbol = status_symbol
        elif style == "batch":
            separator = "*" * 80
            heading = f" BEGINNING EXECUTION OF {text} TASKS "
            symbol = ""
        elif style == "batch_complete":
            separator = "*" * 80
            # Safely parse the completion statistics
            try:
                status_info = text.split("/")
                completed = int(status_info[0]) if status_info[0].isdigit() else 0
                total = int(status_info[1]) if len(status_info) > 1 and status_info[1].isdigit() else 0
                
                # Avoid division by zero
                percentage = (completed / total * 100) if total > 0 else 0
                status_symbol = "✅" if status == "success" else "⚠️" if status == "partial_failure" else "❌"
                heading = f" {status_symbol} TASK BATCH COMPLETE: {completed}/{total} tasks completed successfully ({percentage:.1f}%) [{status.upper()}] "
            except (ValueError, IndexError, ZeroDivisionError):
                # Handle any parsing or calculation errors safely
                status_symbol = "⚠️"
                heading = f" {status_symbol} TASK BATCH COMPLETE: {text} [{status.upper()}] "
            symbol = status_symbol
        else:
            separator = "-" * 80
            heading = f" {text} "
            symbol = ""
            
        # Center the heading within the separator
        centered_heading = heading.center(80, separator[0])
        
        return f"\n{separator}\n{centered_heading}\n{separator}\n"
    
    # Use the unified create_header method instead of these specialized methods
    create_task_header = lambda self, task: self.create_header(task.description, "task")
    create_task_completion_header = lambda self, task, status: self.create_header(task.description, "complete", status)
    create_batch_task_header = lambda self, num_tasks: self.create_header(str(num_tasks), "batch")
    create_batch_completion_header = lambda self, status, completed, total: self.create_header(f"{completed}/{total}", "batch_complete", status)
    
    def _convert_to_dict(self, obj):
        """
        Convert a potentially non-serializable object to a dictionary.
        
        Args:
            obj: Object to convert
            
        Returns:
            Dictionary representation that's JSON serializable
        """
        if obj is None:
            return None
            
        # If it's already a dict, just process each value recursively
        if isinstance(obj, dict):
            return {k: self._convert_to_dict(v) for k, v in obj.items()}
            
        # If it's a list, convert each item
        if isinstance(obj, list):
            return [self._convert_to_dict(item) for item in obj]
            
        # For objects with a to_dict method, use that
        if hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
            return self._convert_to_dict(obj.to_dict())
            
        # For objects with __dict__, convert to dictionary
        if hasattr(obj, '__dict__'):
            return {k: self._convert_to_dict(v) for k, v in obj.__dict__.items() 
                   if not k.startswith('_')}
            
        # Try to serialize, otherwise convert to string
        try:
            import json
            json.dumps(obj)
            return obj
        except (TypeError, OverflowError):
            return str(obj)
            
    async def execute_task(self, task: Task, tasks: List[Task] = None) -> Dict[str, Any]:
        """Execute a specific task.
        
        Args:
            task: The task to execute
            tasks: Optional list of all tasks for context
            
        Returns:
            Results of task execution
        """
        # Check if task is already completed
        if task.status == TaskStatus.COMPLETED:
            logger.info(f"Task '{task.description[:50]}...' is already completed, skipping execution")
            return {
                "status": "already_completed",
                "message": "Task already marked as completed"
            }
            
        # Get appropriate team for task execution
        team = self.team_manager.get_team_for_task(task)
        if not team:
            logger.error(f"Failed to create team for task: {task.id}")
            return {
                "status": "failed",
                "error": "Failed to get appropriate team for task execution"
            }
        logger.info(f"Created team of type '{type(team).__name__}' for task: {task.id}")
            
        # Get project info
        from roboco.core.models.project import Project
        project_id = os.path.basename(self.fs.base_dir)
        project_info = {
            "id": project_id,
            "name": task.title,
            "description": task.description
        }
        
        # Generate task context
        if tasks is None:
            tasks = []
        context = self._generate_task_context(task, tasks, project_info)
        
        # Print header
        task_header = self.create_task_header(task)
        logger.info(task_header)
        
        try:
            # Define message recorder function for real-time persistence
            async def message_recorder(agent_id, content, role="assistant", **kwargs):
                """Record a message from an agent in real-time directly to the database."""
                try:
                    from roboco.db.service import create_message
                    from roboco.core.models.message import MessageRole, MessageType
                    from roboco.api.models.message import MessageCreate
                    
                    # Validate inputs to prevent downstream errors
                    if not content or not isinstance(content, str):
                        logger.warning(f"Invalid message content from {agent_id}: {type(content)}")
                        content = str(content) if content is not None else "Empty message"
                    
                    # Ensure role is a valid MessageRole
                    try:
                        role_enum = role if isinstance(role, MessageRole) else MessageRole(role)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid message role from {agent_id}: {role}, using USER")
                        role_enum = MessageRole.USER
                    
                    # Ensure type is a valid MessageType
                    msg_type = kwargs.get("type", MessageType.TEXT)
                    try:
                        type_enum = msg_type if isinstance(msg_type, MessageType) else MessageType(msg_type)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid message type from {agent_id}: {msg_type}, using TEXT")
                        type_enum = MessageType.TEXT
                    
                    # Create a MessageCreate object (API model) instead of Message
                    message = MessageCreate(
                        content=content,
                        role=role_enum,
                        type=type_enum,
                        task_id=task.id,
                        agent_id=agent_id,
                        meta=kwargs.get("meta", {})
                    )
                    
                    # Create the message in the database immediately
                    create_message(task.id, message)
                    logger.debug(f"Saved message from {agent_id} for task {task.id} in real-time")
                except Exception as e:
                    logger.error(f"Error saving message for task {task.id}: {str(e)}")
                    logger.debug(f"Message content: {content[:100]}..." if isinstance(content, str) else f"Non-string content: {type(content)}")
                    logger.debug(f"Exception traceback: {traceback.format_exc()}")
            
            # Add message recorder to team
            team.message_recorder = message_recorder
            team.current_task_id = task.id
            
            # Setup task in shared context so agents can access it
            if not "task" in team.shared_context:
                team.shared_context["task"] = {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description
                }
            
            # Prepare the initial query with context
            query = f"{task.description}\n\nDetails:\n"
            
            # Safely get details from task.meta, handling None values and empty lists
            if task.meta and task.meta.get('details'):
                details = task.meta.get('details')
                if isinstance(details, list) and len(details) > 0:
                    query += details[0]
                elif isinstance(details, str):
                    query += details
                else:
                    query += "No additional details provided."
            else:
                query += "No additional details provided."
                
            # Add context to the query
            query += f"\n\nCONTEXT:\n{context}"
            
            # Execute the task using the team
            team_result = await team.run_chat(query)
            if "error" in team_result:
                # Build a comprehensive error report
                error_report = {
                    "status": "failed",
                    "error": team_result.get("error", "Unknown error"),
                    "error_type": team_result.get("error_type", "Unknown"),
                    "execution_time": 0  # We don't have start_time here
                }
                
                # Log to console directly
                logger.error(f"Task execution failed: {error_report['error']}")
                
                # Mark task as failed in the database
                self.mark_task_failed(
                    task=task,
                    error=error_report["error"],
                    error_details=team_result.get("traceback", "")
                )
                
                # Log task completion with failure status
                completion_header = self.create_task_completion_header(task, "failed")
                logger.info(completion_header)
                
                return error_report
            
            # Extract response and add execution time
            response = team_result.get("response") or {}
            
            # Check if the response contains error messages or if status is explicitly "failed"
            if team_result.get("status") == "failed":
                # Get the error message
                error_message = team_result.get("error", "Unknown error in team execution")
                
                # Mark task as failed in the database
                self.mark_task_failed(
                    task=task,
                    error=error_message,
                    error_details=team_result.get("traceback", "")
                )
                
                # Log task completion with failure status
                completion_header = self.create_task_completion_header(task, "failed")
                logger.info(completion_header)
                
                # Return error report
                return {
                    "status": "failed",
                    "error": error_message,
                    "execution_time": 0
                }
            
            # Check for errors in the messages list (like seen in the logs)
            if "messages" in team_result and team_result["messages"]:
                messages = team_result["messages"]
                if len(messages) > 0:
                    # Check the last message for error content
                    last_message = messages[-1]
                    content = last_message.get("content", "")
                    if content and isinstance(content, str) and (
                        content.startswith("ERROR:") or 
                        "API call failed" in content or
                        "exception" in content.lower() or
                        "error" in content.lower()
                    ):
                        logger.error(f"Error detected in last message: {content}")
                        
                        # Mark task as failed in the database
                        self.mark_task_failed(
                            task=task,
                            error=content,
                            error_details="Error detected in last message"
                        )
                        
                        # Log task completion with failure status
                        completion_header = self.create_task_completion_header(task, "failed")
                        logger.info(completion_header)
                        
                        # Return error report
                        return {
                            "status": "failed",
                            "error": content,
                            "execution_time": 0
                        }
            
            # If we received a response dictionary, check if it contains error indicators
            if isinstance(response, dict) and response.get("content"):
                content = response.get("content")
                # Check if the content is an error message
                if isinstance(content, str) and (
                    content.startswith("ERROR:") or 
                    "API call failed" in content or
                    "error" in content.lower()
                ):
                    # Mark task as failed in the database
                    self.mark_task_failed(
                        task=task,
                        error=content,
                        error_details="Error detected in response content"
                    )
                    
                    # Log task completion with failure status
                    completion_header = self.create_task_completion_header(task, "failed")
                    logger.info(completion_header)
                    
                    # Return error report
                    return {
                        "status": "failed",
                        "error": content,
                        "execution_time": 0
                    }
            
            # If we got this far, mark task as completed
            # Mark task as completed in the database with the response
            self.mark_task_completed(
                task=task,
                details=f"Task completed successfully with {len(response.items()) if isinstance(response, dict) else 0} response items"
            )
                
            # Create success result
            result = {
                "status": "completed",
                "message": "Task executed successfully",
                "execution_time": 0,  # We don't have start_time here
                "content": response
            }
                
            # Log task completion with success status
            completion_header = self.create_task_completion_header(task, "completed")
            logger.info(completion_header)
            
            # Add final response to task metadata
            try:
                # Remove unnecessary fields from final_response
                final_response = {k: v for k, v in response.items() if k != "sources" and k != "metadata"}
                
                # Update task metadata
                task.meta = task.meta or {}
                task.meta["final_response"] = final_response
                self.update_task_status(task, task.status, {"final_response": final_response})
            except Exception as e:
                logger.error(f"Failed to update task metadata: {str(e)}")
                
            return result
            
        except Exception as e:
            error_tb = traceback.format_exc()
            
            # Create comprehensive error report
            error_report = {
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": error_tb,
                "execution_time": 0  # We don't have start_time here
            }
            
            # Log error details
            logger.error(f"Error executing task '{task.description[:50]}...': {str(e)}")
            logger.error(error_tb)
            
            # Mark task as failed in the database
            self.mark_task_failed(
                task=task,
                error=str(e),
                error_details=error_tb
            )
            
            # Log task completion with failure status
            completion_header = self.create_task_completion_header(task, "failed")
            logger.info(completion_header)
            
            return error_report
    
    async def execute_tasks(self, tasks: List[Task]) -> Dict[str, Any]:
        """Execute a list of tasks.
        
        Args:
            tasks: List of tasks to execute
            
        Returns:
            Results of task execution
        """
        # Create and log batch header
        batch_header = self.create_batch_task_header(len(tasks))
        logger.info(batch_header)
        logger.info(f"Executing {len(tasks)} tasks")
        
        # Track results
        results = {
            "tasks": {},
            "status": "success"
        }
        
        # Track completion stats
        completed_count = 0
        
        # Execute each task
        for task in tasks:
            task_result = await self.execute_task(task, tasks)
            
            # Convert result to ensure it's serializable
            task_result = self._convert_to_dict(task_result)
            
            results["tasks"][task.description] = task_result
            
            # Update completion stats
            if task_result["status"] == "completed" or task_result["status"] == "already_completed":
                completed_count += 1
            
            # Update overall status if any task failed
            if task_result["status"] != "completed" and task_result["status"] != "already_completed":
                results["status"] = "partial_failure"
        
        # Create and log batch completion header
        batch_completion_header = self.create_batch_completion_header(
            results["status"], 
            completed_count, 
            len(tasks)
        )
        logger.info(batch_completion_header)
        
        logger.info(f"Tasks execution completed with status: {results['status']}")
        return results
    
    def _get_minimal_context(self, current_task: Task, tasks: List[Task] = None) -> str:
        """Get minimal but essential context for task execution.
        
        Args:
            current_task: The current task being executed
            tasks: Optional list of all tasks for context
            
        Returns:
            A string containing minimal context
        """
        context_parts = []
        
        # Add current task information with clear heading
        context_parts.append("## Current Task")
        context_parts.append(f"Title: {current_task.title}")
        context_parts.append(f"Description: {current_task.description}")
        context_parts.append(f"Status: {current_task.status.value}")
        
        # Add other tasks if available with clear separation
        if tasks:
            task_summaries = []
            for task in tasks:
                if task.id != current_task.id:  # Use ID comparison for safety
                    status = "COMPLETED" if task.status == TaskStatus.COMPLETED else "TODO"
                    task_summaries.append(f"- Title: {task.title}")
                    task_summaries.append(f"  Description: {task.description}")
                    task_summaries.append(f"  Status: {status}")
            
            if task_summaries:
                context_parts.append("\n## Other Tasks")
                context_parts.extend(task_summaries)
        
        # Add project structure information with clear heading
        try:
            # Get project ID from base directory name
            project_id = os.path.basename(self.fs.base_dir)
            
            # Add basic project structure information
            context_parts.append("\n## Project Structure")
            context_parts.append(f"- Project root: {project_id}")
            context_parts.append(f"- Source code directory: src")
            context_parts.append(f"- Documentation directory: docs")
            
            # List top-level directories and files with clear heading
            root_items = self.fs.list_sync(".")
            if root_items:
                context_parts.append("\n## Root Directory Contents")
                for item in root_items:
                    context_parts.append(f"- {item}")
        
        except Exception as e:
            logger.warning(f"Could not get project structure: {e}")
        
        return "\n".join(context_parts)
