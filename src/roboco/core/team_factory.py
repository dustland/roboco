"""
Factory and registry for creating teams based on task phase requirements.
"""
import copy
import logging
from typing import Dict, Any, Optional, List

from roboco.core.models.phase import Phase
from roboco.core.models.team_template import TeamTemplate, TeamCapabilities
from roboco.core.team import (
    BaseExecutionTeam, 
    SequentialExecutionTeam, 
    ParallelExecutionTeam, 
    IterativeExecutionTeam, 
    GenericExecutionTeam
)

logger = logging.getLogger(__name__)


class TeamRegistry:
    """Registry of predefined team templates for different phases."""
    
    def __init__(self):
        self._templates: Dict[str, TeamTemplate] = {}
        self._register_default_templates()
    
    def _register_default_templates(self):
        """Register default team templates for common phases."""
        self._templates["Research"] = TeamTemplate(
            agents=["researcher", "analyst"],
            tools=["web_search", "document_analyzer"],
            workflow="parallel",
            description="Team specialized in research and information gathering"
        )
        
        self._templates["Design"] = TeamTemplate(
            agents=["architect", "designer", "reviewer"],
            tools=["diagram_generator", "code_generator"],
            workflow="sequential",
            description="Team specialized in system and UI design"
        )
        
        self._templates["Development"] = TeamTemplate(
            agents=["developer", "tester"],
            tools=["code_generator", "file_system", "test_runner"],
            workflow="iterative",
            description="Team specialized in code implementation"
        )
        
        self._templates["Testing"] = TeamTemplate(
            agents=["tester", "quality_analyst"],
            tools=["test_runner", "code_analyzer"],
            workflow="parallel",
            description="Team specialized in testing and quality assurance"
        )
        
        self._templates["Deployment"] = TeamTemplate(
            agents=["devops", "security_analyst"],
            tools=["deployment_manager", "security_scanner"],
            workflow="sequential",
            description="Team specialized in deployment and operations"
        )
    
    def get_template(self, phase_name: str) -> Optional[TeamTemplate]:
        """Get a team template for a specific phase.
        
        Args:
            phase_name: Name of the phase to get a template for
            
        Returns:
            A team template if found, None otherwise
        """
        # Try exact match
        if phase_name in self._templates:
            return self._templates[phase_name]
        
        # Try fuzzy match
        for template_name, template in self._templates.items():
            if template_name.lower() in phase_name.lower() or phase_name.lower() in template_name.lower():
                return template
        
        return None
    
    def register_template(self, phase_name: str, template: TeamTemplate) -> None:
        """Register a new team template.
        
        Args:
            phase_name: Name of the phase to register a template for
            template: Team template to register
        """
        self._templates[phase_name] = template


class TeamFactory:
    """Factory for creating teams based on task phase requirements."""
    
    def __init__(self):
        self.registry = TeamRegistry()
    
    def create_team_for_phase(self, phase: Phase, project_dir: str) -> BaseExecutionTeam:
        """Create an appropriate team for a specific phase.
        
        Args:
            phase: Phase to create a team for
            project_dir: Directory of the project
            
        Returns:
            A team instance appropriate for the phase
        """
        # Get template from registry
        template = self.registry.get_template(phase.name)
        
        if not template:
            # Default to a generic team if no template exists
            logger.info(f"No template found for phase '{phase.name}', creating generic team")
            return self._create_generic_team(phase, project_dir)
        
        # Analyze phase tasks to determine if we need to customize the template
        required_capabilities = self._analyze_phase_requirements(phase)
        
        # Customize template based on requirements
        customized_template = self._customize_template(template, required_capabilities)
        
        # Create and return the team
        return self._create_team_from_template(customized_template, phase, project_dir)
    
    def _analyze_phase_requirements(self, phase: Phase) -> TeamCapabilities:
        """Analyze phase tasks to determine required capabilities.
        
        Args:
            phase: Phase to analyze
            
        Returns:
            TeamCapabilities object with required capabilities
        """
        capabilities = TeamCapabilities(
            required_tools=set(),
            complexity="medium",
            domain_knowledge=[],
            specialized_skills=[]
        )
        
        # Analyze task descriptions to infer requirements
        for task in phase.tasks:
            task_description = task.description.lower() if task.description else ""
            
            # Check for tool requirements
            if "api" in task_description or "endpoint" in task_description or "api" in task_description:
                capabilities.required_tools.add("api_tester")
            
            if "database" in task_description or "data model" in task_description or "database" in task_description:
                capabilities.required_tools.add("database_manager")
            
            if "ui" in task_description or "interface" in task_description or "ui" in task_description:
                capabilities.required_tools.add("ui_generator")
            
            # Check for complexity
            if "complex" in task_description or "advanced" in task_description or "complex" in task_description:
                capabilities.complexity = "high"
            
            # Extract domain knowledge requirements
            if "authentication" in task_description or "auth" in task_description or "authentication" in task_description:
                capabilities.domain_knowledge.append("authentication")
            
            if "payment" in task_description or "billing" in task_description or "payment" in task_description:
                capabilities.domain_knowledge.append("payment_processing")
        
        return capabilities
    
    def _customize_template(self, template: TeamTemplate, capabilities: TeamCapabilities) -> TeamTemplate:
        """Customize a template based on specific requirements.
        
        Args:
            template: Base template to customize
            capabilities: Required capabilities
            
        Returns:
            Customized team template
        """
        customized = copy.deepcopy(template)
        
        # Add required tools
        for tool in capabilities.required_tools:
            if tool not in customized.tools:
                customized.tools.append(tool)
        
        # Adjust for complexity
        if capabilities.complexity == "high" and "architect" not in customized.agents:
            customized.agents.append("architect")
        
        # Add domain specialists
        for domain in capabilities.domain_knowledge:
            if domain == "authentication" and "security_specialist" not in customized.agents:
                customized.agents.append("security_specialist")
            elif domain == "payment_processing" and "payment_specialist" not in customized.agents:
                customized.agents.append("payment_specialist")
        
        return customized
    
    def _create_team_from_template(self, template: TeamTemplate, phase: Phase, project_dir: str) -> BaseExecutionTeam:
        """Create a team instance from a template.
        
        Args:
            template: Template to create a team from
            phase: Phase the team will execute
            project_dir: Directory of the project
            
        Returns:
            A team instance based on the template
        """
        logger.info(f"Creating {template.workflow} team for phase '{phase.name}'")
        
        if template.workflow == "parallel":
            return ParallelExecutionTeam(
                name=f"{phase.name}Team",
                agent_types=template.agents,
                tool_types=template.tools,
                project_dir=project_dir
            )
        elif template.workflow == "sequential":
            return SequentialExecutionTeam(
                name=f"{phase.name}Team",
                agent_types=template.agents,
                tool_types=template.tools,
                project_dir=project_dir
            )
        elif template.workflow == "iterative":
            return IterativeExecutionTeam(
                name=f"{phase.name}Team",
                agent_types=template.agents,
                tool_types=template.tools,
                project_dir=project_dir
            )
        else:
            return GenericExecutionTeam(
                name=f"{phase.name}Team",
                agent_types=template.agents,
                tool_types=template.tools,
                project_dir=project_dir
            )
    
    def _create_generic_team(self, phase: Phase, project_dir: str) -> BaseExecutionTeam:
        """Create a generic team when no template exists.
        
        Args:
            phase: Phase the team will execute
            project_dir: Directory of the project
            
        Returns:
            A generic team instance
        """
        return GenericExecutionTeam(
            name=f"{phase.name}Team",
            agent_types=["developer", "analyst"],
            tool_types=["file_system", "code_generator"],
            project_dir=project_dir
        )
