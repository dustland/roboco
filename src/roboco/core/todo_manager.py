"""
Manager for todo.md files - handles parsing, updating, and tracking task completion.
"""
import logging
import re
import uuid
from datetime import datetime
from typing import List, Optional

from roboco.core.models.phase import Phase
from roboco.core.value_objects.phase_status import PhaseStatus
from roboco.core.value_objects.task_status import TaskStatus
from roboco.core.schema import TodoItem

logger = logging.getLogger(__name__)


class TodoManager:
    """Component for parsing, updating, and managing todo.md files."""
    
    def parse(self, todo_path: str) -> List[Phase]:
        """Parse todo.md into structured Phase objects with TodoItems.
        
        Args:
            todo_path: Path to the todo.md file
            
        Returns:
            List of Phase objects with TodoItems
        """
        phases = []
        current_phase = None
        
        try:
            with open(todo_path, 'r') as file:
                lines = file.readlines()
        except FileNotFoundError:
            logger.error(f"Todo file not found: {todo_path}")
            return phases
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Skip the project title (first line)
            if line.startswith('# ') and not phases:
                continue
            
            # Parse phase headers
            if line.startswith('## '):
                if current_phase:
                    phases.append(current_phase)
                
                phase_name = line[3:].strip()
                current_phase = Phase(
                    name=phase_name,
                    tasks=[],
                    status=PhaseStatus.TODO
                )
            
            # Parse task items
            elif line.startswith('- [ ]') or line.startswith('- [x]'):
                if not current_phase:
                    # If no phase has been defined yet, create a default one
                    current_phase = Phase(
                        name="Default",
                        tasks=[],
                        status=PhaseStatus.TODO
                    )
                
                is_completed = line.startswith('- [x]')
                task_content = line[5:].strip()
                
                # Extract task title and description
                task_parts = task_content.split(':', 1)
                task_title = task_parts[0].strip()
                task_description = task_parts[1].strip() if len(task_parts) > 1 else ""
                
                # Create TodoItem
                task = TodoItem(
                    id=str(uuid.uuid4()),
                    title=task_title,
                    description=task_description,
                    status=TaskStatus.DONE if is_completed else TaskStatus.TODO,
                    completed_at=datetime.now() if is_completed else None
                )
                
                current_phase.tasks.append(task)
        
        # Add the last phase
        if current_phase:
            phases.append(current_phase)
        
        # Update phase statuses based on task completion
        for phase in phases:
            if all(task.status == TaskStatus.DONE for task in phase.tasks):
                phase.status = PhaseStatus.DONE
            elif any(task.status == TaskStatus.DONE for task in phase.tasks):
                phase.status = PhaseStatus.IN_PROGRESS
        
        return phases
    
    def mark_task_completed(self, phases: List[Phase], task_id: str) -> bool:
        """Mark a specific task as completed.
        
        Args:
            phases: List of phases containing tasks
            task_id: ID of the task to mark as completed
            
        Returns:
            True if the task was found and marked, False otherwise
        """
        for phase in phases:
            for task in phase.tasks:
                if task.id == task_id:
                    task.status = TaskStatus.DONE
                    task.completed_at = datetime.now()
                    
                    # Update phase status if all tasks are completed
                    if all(t.status == TaskStatus.DONE for t in phase.tasks):
                        phase.status = PhaseStatus.DONE
                    else:
                        phase.status = PhaseStatus.IN_PROGRESS
                    
                    return True
        
        return False
    
    def update_todo_file(self, todo_path: str, phases: List[Phase]) -> None:
        """Update the todo.md file with the current status of tasks.
        
        Args:
            todo_path: Path to the todo.md file
            phases: List of phases with tasks to update
        """
        try:
            # Read the original file to preserve the project title
            with open(todo_path, 'r') as file:
                lines = file.readlines()
            
            # Extract the project title (first line)
            project_title = lines[0] if lines else "# Project\n"
            
            # Create new content
            new_lines = [project_title]
            if not project_title.endswith('\n'):
                new_lines.append('\n')
            new_lines.append('\n')
            
            # Add phases and tasks
            for phase in phases:
                new_lines.append(f"## {phase.name}\n")
                
                for task in phase.tasks:
                    checkbox = "[x]" if task.status == TaskStatus.DONE else "[ ]"
                    task_line = f"- {checkbox} {task.title}"
                    
                    if task.description:
                        task_line += f": {task.description}"
                    
                    new_lines.append(task_line + '\n')
                
                new_lines.append('\n')
            
            # Write to file
            with open(todo_path, 'w') as file:
                file.writelines(new_lines)
                
        except Exception as e:
            logger.error(f"Error updating todo file: {str(e)}")
    
    def get_phase_by_name(self, phases: List[Phase], phase_name: str) -> Optional[Phase]:
        """Get a phase by name.
        
        Args:
            phases: List of phases to search
            phase_name: Name of the phase to find
            
        Returns:
            Phase if found, None otherwise
        """
        for phase in phases:
            if phase.name.lower() == phase_name.lower():
                return phase
        return None
    
    def get_task_by_title(self, phases: List[Phase], task_title: str) -> Optional[TodoItem]:
        """Get a task by title.
        
        Args:
            phases: List of phases to search
            task_title: Title of the task to find
            
        Returns:
            TodoItem if found, None otherwise
        """
        for phase in phases:
            for task in phase.tasks:
                if task.title.lower() == task_title.lower():
                    return task
        return None
