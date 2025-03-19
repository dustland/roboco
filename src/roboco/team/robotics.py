"""
Robotics Corporation Core Module

This module provides the main RoboticsCompany class that orchestrates
all agents for the robotics corporation.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
import yaml

from roboco.core import Tool, get_workspace
from roboco.core.logger import get_logger
from roboco.agents import (
    Executive,
    ProductManager,
    SoftwareEngineer,
    RoboticsScientist,
    ReportWriter,
    HumanProxy
)

logger = get_logger(__name__)

class RoboticsCompany:
    """Main class for orchestrating the robotics corporation operations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the robotics corporation.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.workspace = get_workspace()
        
        # Load organizational structure
        self.org_chart = self._load_org_chart()
        
        # Initialize corporation structure
        self._setup_corporation_structure()
        
        # Initialize agents based on org chart
        self.agents = self._initialize_agents()
        
        logger.info("RoboticsCompany initialized successfully")
    
    def _load_org_chart(self) -> Dict[str, Any]:
        """Load the organizational chart configuration.
        
        Returns:
            Dictionary containing the org chart configuration
        """
        # Look for org chart in the config directory
        config_dir = self.workspace.parent / "config"
        org_chart_path = config_dir / "org_chart.yaml"
        
        if not org_chart_path.exists():
            raise FileNotFoundError(f"Organizational chart file not found at {org_chart_path}")
            
        with open(org_chart_path, "r") as f:
            org_chart = yaml.safe_load(f)
            
        # Extract organizational structure
        if "org_structure" not in org_chart:
            raise ValueError("No organizational structure found in org chart configuration")
            
        return org_chart["org_structure"]
    
    def _setup_corporation_structure(self) -> None:
        """Set up the corporation structure based on the org chart."""
        # Initialize role mappings
        self.role_mappings = {
            "executive": Executive,
            "product_manager": ProductManager,
            "software_engineer": SoftwareEngineer,
            "robotics_scientist": RoboticsScientist,
            "report_writer": ReportWriter,
            "human_proxy": HumanProxy
        }
        
        # Create role instances
        self.roles = {}
        for role_id, role_config in self.org_chart.items():
            if role_id in self.role_mappings:
                role_class = self.role_mappings[role_id]
                self.roles[role_id] = role_class(
                    name=role_config["role"],
                    responsibilities=role_config["responsibilities"],
                    tools=role_config["tools"]
                )
                logger.info(f"Initialized role: {role_config['role']}")
    
    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize agents based on the org chart configuration.
        
        Returns:
            Dictionary of initialized agents
        """
        agents = {}
        
        for role_id, role_config in self.org_chart.items():
            if role_id in self.roles:
                role = self.roles[role_id]
                agents[role_id] = role.create_agent()
                logger.info(f"Created agent for role: {role_config['role']}")
        
        return agents
    
    def get_agent(self, role_id: str) -> Optional[Any]:
        """Get an agent by role ID.
        
        Args:
            role_id: The role ID to look up
            
        Returns:
            The agent instance if found, None otherwise
        """
        return self.agents.get(role_id)
    
    def get_role(self, role_id: str) -> Optional[Any]:
        """Get a role by ID.
        
        Args:
            role_id: The role ID to look up
            
        Returns:
            The role instance if found, None otherwise
        """
        return self.roles.get(role_id)
    
    def get_org_structure(self) -> Dict[str, Any]:
        """Get the organizational structure.
        
        Returns:
            Dictionary containing the org chart configuration
        """
        return self.org_chart
    
    async def start_research_project(self, project_name: str, description: str) -> Dict[str, Any]:
        """Start a new research project.
        
        Args:
            project_name: Name of the research project
            description: Project description
            
        Returns:
            Dictionary with project information
        """
        return await self.agents["robotics_scientist"].research_topic(project_name, description)
    
    async def develop_robot(self, robot_name: str, specifications: Dict[str, Any]) -> Dict[str, Any]:
        """Start development of a new robot.
        
        Args:
            robot_name: Name of the robot
            specifications: Robot specifications
            
        Returns:
            Dictionary with development information
        """
        return await self.agents["software_engineer"].develop_robot(robot_name, specifications)
    
    async def test_robot(self, robot_name: str, test_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Start testing of a robot.
        
        Args:
            robot_name: Name of the robot to test
            test_plan: Testing plan and requirements
            
        Returns:
            Dictionary with testing information
        """
        return await self.agents["software_engineer"].test_robot(robot_name, test_plan)
    
    async def deploy_robot(self, robot_name: str, deployment_config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy a robot to operations.
        
        Args:
            robot_name: Name of the robot to deploy
            deployment_config: Deployment configuration
            
        Returns:
            Dictionary with deployment information
        """
        return await self.agents["software_engineer"].deploy_robot(robot_name, deployment_config)
    
    async def generate_report(self, report_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a corporation report.
        
        Args:
            report_type: Type of report to generate
            parameters: Report parameters
            
        Returns:
            Dictionary with report information
        """
        return await self.agents["report_writer"].generate_report(report_type, parameters)
    
    @classmethod
    def create_with_config(cls, config: Dict[str, Any]) -> 'RoboticsCompany':
        """Create a RoboticsCompany instance with the specified configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Configured RoboticsCompany instance
        """
        return cls(config=config) 