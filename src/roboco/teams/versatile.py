"""
Versatile Team Module

This module defines the VersatileTeam class, which provides a flexible and adaptable team implementation
with specialized roles designed to handle any type of task phase effectively.
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

# Initialize logger
logger = logger.bind(module=__name__)

from roboco.core.project_fs import ProjectFS
from roboco.core.team import Team
from roboco.core.models import Task
from roboco.agents.human_proxy import HumanProxy
from roboco.core.agent_factory import AgentFactory
from autogen import AfterWork, AfterWorkOption, OnCondition, register_hand_off


class VersatileTeam(Team):
    """
    A flexible and adaptable team with specialized roles that can handle any type of task.
    This team is designed to work effectively on task phases that don't clearly
    fit into specific categories like research, development, or design.
    
    Uses the AG2 swarm pattern for agent orchestration, allowing agents to collaborate
    with automatic handoffs based on conditions.
    """
    
    def __init__(
        self,
        fs: ProjectFS,
        config_path: Optional[str] = None
    ):
        """Initialize the versatile team with specialized roles.
        
        Args:
            workspace_dir: Directory for workspace files
            config_path: Optional path to team configuration file
        """
        super().__init__(name="VersatileTeam", config_path=config_path)
        self.fs = fs
        
        # Initialize the agents with specialized roles
        self._initialize_agents()
        
        # Register tools with agents
        self._register_tools()
        
        # Enable swarm capabilities with shared context
        self.enable_swarm({
            "project_phase": "initial",
            "allow_research": True,
            "allow_creation": True,
            "allow_evaluation": False,
            "allow_integration": False
        })
        
        # Register handoffs for the swarm
        self._register_handoffs()
        
        logger.info(f"Initialized VersatileTeam with specialized roles in workspace: {self.fs.base_dir}")
    
    def _initialize_agents(self):
        """Initialize agents with specialized roles for the team."""
        agent_factory = AgentFactory.get_instance()
        
        # Initialize each agent using the role configurations from roles.yaml
        # Consolidated roles from 6 to 4:
        # 1. Researcher (combines Architect and Explorer) - Research and planning
        # 2. Creator (unchanged) - Implementation 
        # 3. Evaluator (unchanged) - Testing and validation
        # 4. Integrator (replaces Synthesizer) - Integration and finalization
        
        # Researcher combines research and architectural design
        researcher = agent_factory.create_agent(
            role_key="researcher",  # Updated from architect to researcher
            terminate_msg="RESEARCH_COMPLETE"
        )
        
        # Creator implements the solution
        creator = agent_factory.create_agent(
            role_key="creator",
            terminate_msg="CREATION_COMPLETE"
        )
        
        # Evaluator tests and validates the implementation
        evaluator = agent_factory.create_agent(
            role_key="evaluator",
            terminate_msg="EVALUATION_COMPLETE"
        )
        
        # Integrator finalizes and delivers the complete solution
        integrator = agent_factory.create_agent(
            role_key="integrator",  # Updated from synthesizer to integrator
            terminate_msg="INTEGRATION_COMPLETE"
        )
        
        # Human Proxy - Interface for human input when needed
        executor = HumanProxy(
            name="executor",
            human_input_mode="NEVER"
        )
        
        # Add all agents to the team
        self.add_agent("researcher", researcher)
        self.add_agent("creator", creator)
        self.add_agent("evaluator", evaluator)
        self.add_agent("integrator", integrator)
        self.add_agent("executor", executor)
    
    def _register_tools(self):
        """Register necessary tools with the agents."""
        try:
            # Register filesystem tool with all agents
            from roboco.tools.fs import FileSystemTool
            # Create the filesystem tool with project context if available
            fs_tool = FileSystemTool(
                fs=self.fs, 
            )
            
            for agent_name, agent in self.agents.items():
                fs_tool.register_with_agents(agent)
            
            # Register web search tool if available
            try:
                from roboco.tools.web_search import WebSearchTool
                web_search_tool = WebSearchTool(
                    name="web_search",
                    description="Search the web for information"
                )
                
                # Register with researcher for research capabilities
                web_search_tool.register_with_agents(
                    self.get_agent("researcher")
                )
            except ImportError:
                logger.warning("WebSearchTool not available")
            except Exception as e:
                logger.warning(f"Could not initialize WebSearchTool: {str(e)}")
            
            # Register code tool with creator, evaluator, and integrator
            try:
                from roboco.tools.code import CodeTool
                code_tool = CodeTool(
                    fs=self.fs,
                    name="code",
                    description="Generate, validate, and execute code in multiple languages"
                )
                
                # Register with appropriate agents
                code_tool.register_with_agents(
                    self.get_agent("creator"),
                    self.get_agent("evaluator"),
                    self.get_agent("integrator")
                )
                
            except ImportError:
                logger.warning("CodeTool not available")
            except Exception as e:
                logger.warning(f"Could not initialize CodeTool: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error registering tools: {str(e)}")
    
    def _register_handoffs(self):
        """Register handoffs between agents for a collaborative swarm pattern."""
        researcher = self.get_agent("researcher")
        creator = self.get_agent("creator")
        evaluator = self.get_agent("evaluator")
        integrator = self.get_agent("integrator")
        executor = self.get_agent("executor")
        
        # Researcher can handoff to either Creator or self (for more research)
        register_hand_off(researcher, [
            # If research identifies implementation approach, go to Creator
            OnCondition(
                condition="Route to Creator when implementation plan is ready",
                target=creator
            ),
            # Otherwise, stay with Researcher for deeper exploration
            AfterWork(agent=researcher)
        ])
        
        # Creator can handoff to Evaluator, Researcher (if stuck), or self (to continue work)
        register_hand_off(creator, [
            # If implementation needs research help, go back to Researcher
            OnCondition(
                condition="Route to Researcher when more research is needed",
                target=researcher,
                available="allow_research"
            ),
            # If implementation is ready for testing, go to Evaluator
            OnCondition(
                condition="Route to Evaluator when implementation is ready for testing",
                target=evaluator,
                available="allow_evaluation"
            ),
            # Otherwise, continue implementation
            AfterWork(agent=creator)
        ])
        
        # Evaluator can handoff to Creator (if issues found), Integrator (if approved), or Researcher (if conceptual issues)
        register_hand_off(evaluator, [
            # If evaluation finds implementation issues, go back to Creator
            OnCondition(
                condition="Route to Creator when implementation issues are found",
                target=creator,
                available="allow_creation"
            ),
            # If evaluation finds conceptual/design issues, go back to Researcher
            OnCondition(
                condition="Route to Researcher when conceptual issues are found",
                target=researcher,
                available="allow_research"
            ),
            # If evaluation approves, move to Integration
            OnCondition(
                condition="Route to Integrator when implementation is approved",
                target=integrator,
                available="allow_integration"
            ),
            # Continue evaluation if more assessment needed
            AfterWork(agent=evaluator)
        ])
        
        # Integrator can consult any other agent as needed or terminate
        register_hand_off(integrator, [
            # If integration reveals implementation gaps, consult Creator
            OnCondition(
                condition="Route to Creator when implementation gaps are found",
                target=creator
            ),
            # If integration reveals research/design issues, consult Researcher
            OnCondition(
                condition="Route to Researcher when design issues are found",
                target=researcher
            ),
            # If integration needs validation, consult Evaluator
            OnCondition(
                condition="Route to Evaluator when validation is needed",
                target=evaluator
            ),
            # Terminate when integration is complete
            OnCondition(
                condition="Terminate when integration is complete",
                target=None
            ),
            # Terminate the swarm explicitly if integration is complete
            AfterWork(agent=AfterWorkOption.TERMINATE)
        ])
        
        # Human proxy can direct to any agent based on need
        register_hand_off(executor, [
            OnCondition(
                condition="Route to Researcher when requested",
                target=researcher
            ),
            OnCondition(
                condition="Route to Creator when requested",
                target=creator
            ),
            OnCondition(
                condition="Route to Evaluator when requested",
                target=evaluator
            ),
            OnCondition(
                condition="Route to Integrator when requested",
                target=integrator
            ),
            # Default to researcher if no specific direction
            AfterWork(agent=researcher)
        ])
        
        logger.info("Registered dynamic handoffs for collaborative swarm pattern with feedback loops")
    
    def _chat_result_to_dict(self, chat_result):
        """
        Convert a ChatResult object to a dictionary for JSON serialization.
        
        Args:
            chat_result: A ChatResult object or any other object
            
        Returns:
            A JSON-serializable dictionary
        """
        # If it's already a dict or basic type, return it
        if isinstance(chat_result, (dict, str, int, float, bool, type(None))):
            return chat_result
            
        # If it's a list, convert each item
        if isinstance(chat_result, list):
            return [self._chat_result_to_dict(item) for item in chat_result]
            
        # If it's a ChatResult object
        if hasattr(chat_result, '__class__') and chat_result.__class__.__name__ == 'ChatResult':
            result = {}
            # Add all attributes that don't start with underscore
            for attr in dir(chat_result):
                if not attr.startswith('_'):
                    try:
                        value = getattr(chat_result, attr)
                        # Skip methods
                        if not callable(value):
                            result[attr] = self._chat_result_to_dict(value)
                    except Exception as e:
                        logger.warning(f"Error getting attribute {attr} from ChatResult: {e}")
            return result
            
        # Try to convert object to dict if it has a to_dict method
        if hasattr(chat_result, 'to_dict') and callable(chat_result.to_dict):
            return self._chat_result_to_dict(chat_result.to_dict())
            
        # If it has a dict or model_dump method (pydantic models)
        if hasattr(chat_result, 'dict') and callable(getattr(chat_result, 'dict')):
            return self._chat_result_to_dict(chat_result.dict())
        if hasattr(chat_result, 'model_dump') and callable(getattr(chat_result, 'model_dump')):
            return self._chat_result_to_dict(chat_result.model_dump())
            
        # Last resort: try to convert to string
        try:
            return str(chat_result)
        except:
            return f"<Non-serializable object of type {type(chat_result).__name__}>"
            
    async def run_chat(self, query: str, teams: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run a chat session with all team members working together.
        
        This method uses swarm orchestration to enable all agents to collaborate
        on a task with automatic handoffs between agents.
        
        Args:
            query: The user's query
            teams: Optional list of teams to assign
            
        Returns:
            Dict containing the session results
        """
        # Convert string to Task
        from roboco.core.models import Task
        task = Task(description=query)
        
        # Create context variables with clear guidance for collaboration
        context = {
            "task": task.model_dump() if hasattr(task, 'model_dump') else (
                task.dict() if hasattr(task, 'dict') else {"description": task.description}
            ),
            "collaboration_guidelines": {
                "feedback_loops": "Actively request feedback from other specialists when needed",
                "debate": "Highlight areas of uncertainty and debate alternate approaches",
                "explicit_handoffs": "Clearly state when another specialist would be better suited for the current challenge",
                "shared_knowledge": "Reference and build upon insights from previous agents",
                "self_reflection": "Evaluate your own work and suggest improvements before handoff"
            }
        }
        
        # Log the start of collaborative session
        logger.info(f"Starting collaborative session with dynamic handoffs for task: {task.description[:50]}...")
        
        # Run the swarm with the researcher as the initial agent
        try:
            swarm_result = self.run_swarm(
                initial_agent_name="researcher",
                query=f"You're the starting point for our collaborative effort. Analyze this task and either begin working on it or determine which specialist should tackle it first: {task.description}",
                context_variables=context,
                max_rounds=25
            )
        except Exception as e:
            import traceback
            error_tb = traceback.format_exc()
            logger.error(f"Exception before swarm execution in VersatileTeam: {str(e)}")
            logger.error(f"Traceback: {error_tb}")
            return {
                "error": str(e),
                "traceback": error_tb,
                "status": "failed"
            }
        
        # Save the results
        # Create a file name based on the first few words of the description
        task_file_name = "task_" + "_".join(task.description.split()[:5]).lower()
        task_file_name = "".join(c if c.isalnum() or c == "_" else "_" for c in task_file_name)
        results_path = os.path.join(self.fs.base_dir, f"{task_file_name}_results.md")
        
        if "error" not in swarm_result:
            chat_result = swarm_result.get("chat_result", "")
            
            # Extract and format the collaboration analysis
            messages = swarm_result.get("messages", [])
            agent_sequence = []
            agent_contributions = {}
            
            for msg in messages:
                agent_name = msg.get("name", "unknown")
                if agent_name not in ["user", "unknown"]:
                    agent_sequence.append(agent_name)
                    content = msg.get("content", "")
                    if agent_name not in agent_contributions:
                        agent_contributions[agent_name] = []
                    agent_contributions[agent_name].append(len(content))
            
            # Write enhanced results file
            with open(results_path, "w") as f:
                f.write(f"# Collaborative Task Results\n\n")
                f.write(f"## Task Description\n{task.description}\n\n")
                f.write(f"## Solution\n{json.dumps(self._chat_result_to_dict(chat_result), indent=2)}\n\n")
                
                # Add collaboration analysis
                f.write(f"## Collaboration Analysis\n\n")
                f.write(f"### Agent Sequence\n{' → '.join(agent_sequence)}\n\n")
                
                f.write(f"### Contribution Summary\n")
                for agent, sizes in agent_contributions.items():
                    f.write(f"- **{agent}**: {len(sizes)} contributions, {sum(sizes)} total characters\n")
            
            logger.info(f"Collaborative session completed with {len(agent_sequence)} agent handoffs")
            logger.info(f"Results saved to {results_path}")
            
            # Format the response to match PlanningTeam's run_chat format
            return {
                "response": self._chat_result_to_dict(chat_result),
                "chat_history": messages,
                "results_path": results_path,
                "collaboration_stats": {
                    "agent_sequence": agent_sequence,
                    "agent_contributions": agent_contributions
                },
                "status": "completed"
            }
        else:
            logger.error(f"Error in collaborative session: {swarm_result.get('error')}")
            return {
                "error": swarm_result.get('error', "Unknown error in collaborative session"),
                "status": "failed"
            }

    def update_project_phase(self, phase: str) -> None:
        """
        Update the project phase in the shared context and toggle available handoffs.
        
        Args:
            phase: The new project phase ('initial', 'development', 'testing', 'integration')
        """
        # Update the project phase
        self.shared_context["project_phase"] = phase
        
        # Update available handoffs based on project phase
        if phase == "initial":
            self.shared_context.update({
                "allow_research": True,
                "allow_creation": True,
                "allow_evaluation": False,
                "allow_integration": False
            })
        elif phase == "development":
            self.shared_context.update({
                "allow_research": True,
                "allow_creation": True,
                "allow_evaluation": True,
                "allow_integration": False
            })
        elif phase == "testing":
            self.shared_context.update({
                "allow_research": True,
                "allow_creation": True,
                "allow_evaluation": True,
                "allow_integration": True
            })
        elif phase == "integration":
            self.shared_context.update({
                "allow_research": False,
                "allow_creation": False,
                "allow_evaluation": True,
                "allow_integration": True
            })
        
        logger.info(f"Updated project phase to {phase} with context: {self.shared_context}")