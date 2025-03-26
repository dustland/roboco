"""
Team Assigner Module

This module provides functionality to assign appropriate teams for executing different types of phases.
"""

from typing import Any, Dict, List, Optional
from roboco.core.logger import get_logger

from roboco.core.models.phase import Phase
from roboco.core.project_fs import ProjectFS
from roboco.teams.versatile import VersatileTeam
from roboco.teams.planning import PlanningTeam

# Initialize logger
logger = get_logger(__name__)

class TeamAssigner:
    """Assigns appropriate teams for executing different types of phases."""
    
    def __init__(self, fs: ProjectFS):
        """Initialize the team assigner.
        
        Args:
            fs: ProjectFS instance
        """
        self.fs = fs
        
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
        
        if team_type == "planning":
            return PlanningTeam(fs=self.fs)
        else:
            # Default to VersatileTeam instead of ExecutionTeam for better adaptability
            return VersatileTeam(fs=self.fs)
        