"""
Team Assigner Module

This module provides functionality to assign appropriate teams for executing different types of phases.
"""

from typing import Any, Dict, List, Optional
from roboco.core.logger import get_logger

from roboco.core.models.phase import Phase
from roboco.teams.versatile import VersatileTeam

# Initialize logger
logger = get_logger(__name__)

class TeamAssigner:
    """Assigns appropriate teams for executing different types of phases."""
    
    def __init__(self, workspace_dir: str):
        """Initialize the team assigner.
        
        Args:
            workspace_dir: Base workspace directory for team operations
        """
        self.workspace_dir = workspace_dir
        
        # Simple mapping of phase keywords to team types
        self.phase_team_mapping = {
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
    
    def get_team_for_phase(self, phase: Phase) -> Any:
        """Get an appropriate team for executing the given phase.
        
        Args:
            phase: The phase to be executed
            
        Returns:
            A team instance appropriate for the phase
        """
        # Determine team type from phase name
        team_type = self._determine_team_type(phase.name)
        
        # Create and return appropriate team
        return self._create_team(team_type)
    
    def _determine_team_type(self, phase_name: str) -> str:
        """Determine the appropriate team type for a phase name.
        
        Args:
            phase_name: Name of the phase
            
        Returns:
            The determined team type as a string
        """
        phase_name_lower = phase_name.lower()
        
        # Look for keywords in the phase name
        for keyword, team_type in self.phase_team_mapping.items():
            if keyword in phase_name_lower:
                logger.debug(f"Determined team type '{team_type}' for phase '{phase_name}'")
                return team_type
        
        # Default to versatile team if no specific match found
        logger.debug(f"No specific team type found for phase '{phase_name}', defaulting to versatile")
        return "versatile"
    
    def _create_team(self, team_type: str) -> Any:
        """Create and configure a team of the specified type.
        
        Args:
            team_type: Type of team to create
            
        Returns:
            A team instance appropriate for the team type
        """
        logger.debug(f"Creating team of type '{team_type}'")
        
        try:
            if team_type == "planning":
                from roboco.teams.planning import PlanningTeam
                return PlanningTeam(workspace_dir=self.workspace_dir)
                
            else:
                # Default to VersatileTeam instead of ExecutionTeam for better adaptability
                logger.info(f"No specific team implementation for '{team_type}', using VersatileTeam")
                return VersatileTeam(workspace_dir=self.workspace_dir)
                
        except Exception as e:
            logger.error(f"Error creating team of type '{team_type}': {e}")
            logger.warning("Attempting to use VersatileTeam as fallback")
            try:
                from roboco.teams.versatile import VersatileTeam
                return VersatileTeam(workspace_dir=self.workspace_dir)
            except Exception:
                logger.warning("Failed to create VersatileTeam, falling back to ExecutionTeam")
                from roboco.teams.execution import ExecutionTeam
                return ExecutionTeam(project_dir=self.workspace_dir) 