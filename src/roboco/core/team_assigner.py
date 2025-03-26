"""
Team Assigner Module

This module provides functionality to assign appropriate teams for executing different types of tasks.
"""

from typing import Any, Dict, List, Optional
from roboco.core.logger import get_logger

from roboco.core.models.task import Task
from roboco.core.models.phase import Phase
from roboco.core.project_fs import ProjectFS
from roboco.teams.versatile import VersatileTeam
from roboco.teams.planning import PlanningTeam

# Initialize logger
logger = get_logger(__name__)

class TeamAssigner:
    """Assigns appropriate teams for executing different types of tasks."""
    
    def __init__(self, fs: ProjectFS):
        """Initialize the team assigner.
        
        Args:
            fs: ProjectFS instance
        """
        self.fs = fs
        
        # Simple mapping of task keywords to team types
        self.task_team_mapping = {
            "research": "research",
            "planning": "planning",
            "design": "design",
            "development": "development",
            "implementation": "development",
            "testing": "testing",
            "deployment": "deployment",
            "general": "versatile",
            "universal": "versatile",
            "common": "versatile",
            "miscellaneous": "versatile",
            "other": "versatile",
            "versatile": "versatile"
        }
    
    def get_team_for_task(self, task: Task) -> Any:
        """Get an appropriate team for executing the given task.
        
        Args:
            task: The task to be executed
            
        Returns:
            A team instance appropriate for the task
        """
        # Determine team type from task description
        team_type = self._determine_team_type(task.description)
        
        # Create and return appropriate team
        return self._create_team(team_type)
    
    def get_team_for_phase(self, phase: Phase) -> Any:
        """Get an appropriate team for executing the given phase.
        
        Args:
            phase: The phase to be executed
            
        Returns:
            A team instance appropriate for the phase
        """
        # For backward compatibility, use the first task's description to determine team
        if phase.tasks:
            return self.get_team_for_task(phase.tasks[0])
        return self._create_team("versatile")
    
    def _determine_team_type(self, description: str) -> str:
        """Determine the appropriate team type for a description.
        
        Args:
            description: Description of the task or phase
            
        Returns:
            The determined team type as a string
        """
        description_lower = description.lower()
        
        # Look for keywords in the description
        for keyword, team_type in self.task_team_mapping.items():
            if keyword in description_lower:
                logger.debug(f"Determined team type '{team_type}' for description '{description}'")
                return team_type
        
        # Default to versatile team if no specific match found
        logger.debug(f"No specific team type found for description '{description}', defaulting to versatile")
        return "versatile"
    
    def _create_team(self, team_type: str) -> Any:
        """Create and configure a team of the specified type.
        
        Args:
            team_type: Type of team to create
            
        Returns:
            A team instance appropriate for the team type
        """
        logger.debug(f"Creating team of type '{team_type}'")
        
        if team_type == "planning":
            return PlanningTeam(fs=self.fs)
        else:
            # Default to VersatileTeam instead of ExecutionTeam for better adaptability
            return VersatileTeam(fs=self.fs)
        