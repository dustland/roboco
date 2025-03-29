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
            "allow_development": True,
            "allow_writing": True,
            "allow_evaluation": False,
            "allow_leadership": False
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
        
        # Developer implements the solution
        developer = agent_factory.create_agent(
            role_key="developer",  # Updated from creator to developer
            terminate_msg="DEVELOPMENT_COMPLETE"  # Updated from CREATION_COMPLETE
        )
        
        # Writer creates written content and documentation
        writer = agent_factory.create_agent(
            role_key="writer",
            terminate_msg="WRITING_COMPLETE"
        )
        
        # Evaluator tests and validates the implementation
        evaluator = agent_factory.create_agent(
            role_key="evaluator",
            terminate_msg="EVALUATION_COMPLETE"
        )
        
        # Lead finalizes and delivers the complete solution
        lead = agent_factory.create_agent(
            role_key="lead",  # Updated from integrator to lead
            terminate_msg="LEADERSHIP_COMPLETE"  # Updated from INTEGRATION_COMPLETE
        )
        
        # Human Proxy - Interface for human input when needed
        executor = HumanProxy(
            name="executor",
            human_input_mode="NEVER"
        )
        
        # Add all agents to the team
        self.add_agent("executor", executor)
        self.add_agent("lead", lead)  # Updated from integrator to lead
        self.add_agent("researcher", researcher)
        self.add_agent("developer", developer)
        self.add_agent("writer", writer)
        self.add_agent("evaluator", evaluator)
    
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
                # Skip registering the executor with itself
                if agent_name != "executor":
                    fs_tool.register_with_agents(agent, executor_agent=self.get_agent("executor"))
            
            # Register web search tool if available
            try:
                from roboco.tools.web_search import WebSearchTool
                web_search_tool = WebSearchTool(
                    name="web_search",
                    description="Search the web for information"
                )
                
                # Register with researcher for research capabilities
                web_search_tool.register_with_agents(
                    self.get_agent("researcher"),
                    executor_agent=self.get_agent("executor")
                )
            except ImportError:
                logger.warning("WebSearchTool not available")
            except Exception as e:
                logger.warning(f"Could not initialize WebSearchTool: {str(e)}")
            
            # Register code tool with developer, evaluator, and lead
            try:
                from roboco.tools.browser_use import BrowserUseTool
                browser_tool = BrowserUseTool(
                    fs=self.fs,
                    name="browser",
                    description="Use the web browser to search the web or navigate to a specific URL"
                )
                
                # Register with appropriate agents
                browser_tool.register_with_agents(
                    self.get_agent("researcher"),
                    executor_agent=self.get_agent("executor")
                )
                
            except ImportError:
                logger.warning("BrowserUseTool not available")
            except Exception as e:
                logger.warning(f"Could not initialize BrowserUseTool: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error registering tools: {str(e)}")
    
    def _register_handoffs(self):
        """Register handoffs between agents for a collaborative swarm pattern."""
        researcher = self.get_agent("researcher")
        developer = self.get_agent("developer")
        writer = self.get_agent("writer")
        evaluator = self.get_agent("evaluator")
        lead = self.get_agent("lead")
        executor = self.get_agent("executor")
        
        # Researcher can handoff to Developer, Writer, or self (for more research)
        register_hand_off(researcher, [
            # If research identifies implementation approach for code, go to Developer
            OnCondition(
                condition="Message contains RESEARCH_COMPLETE and mentions code implementation or development",
                target=developer,
                available="allow_development"
            ),
            # If research identifies content writing needs, go to Writer
            OnCondition(
                condition="Message contains RESEARCH_COMPLETE and mentions documentation or writing needs",
                target=writer,
                available="allow_writing"
            ),
            # Default to Developer if no specific conditions are met
            AfterWork(agent=developer)
        ])
        
        # Developer can handoff to Evaluator, Researcher (if stuck), or self (to continue work)
        register_hand_off(developer, [
            # If implementation needs research help, go back to Researcher
            OnCondition(
                condition="Message contains DEVELOPMENT_BLOCKED and mentions research or design issues",
                target=researcher,
                available="allow_research"
            ),
            # If implementation is ready for testing, go to Evaluator
            OnCondition(
                condition="Message contains DEVELOPMENT_COMPLETE",
                target=evaluator,
                available="allow_evaluation"
            ),
            # Otherwise, continue implementation
            AfterWork(agent=developer)
        ])
        
        # Writer can handoff to Evaluator, Researcher (if stuck), or self (to continue work)
        register_hand_off(writer, [
            # If writing needs research help, go back to Researcher
            OnCondition(
                condition="Message contains WRITING_BLOCKED and mentions research or information needs",
                target=researcher,
                available="allow_research"
            ),
            # If writing is ready for review, go to Evaluator
            OnCondition(
                condition="Message contains WRITING_COMPLETE",
                target=evaluator,
                available="allow_evaluation"
            ),
            # Otherwise, continue writing
            AfterWork(agent=writer)
        ])
        
        # Evaluator can handoff to Developer (if code issues), Writer (if document issues),
        # Lead (if approved), or Researcher (if conceptual issues)
        register_hand_off(evaluator, [
            # If evaluation finds implementation issues, go back to Developer
            OnCondition(
                condition="Message contains EVALUATION_ISSUES and mentions code or implementation problems",
                target=developer,
                available="allow_development"
            ),
            # If evaluation finds documentation issues, go back to Writer
            OnCondition(
                condition="Message contains EVALUATION_ISSUES and mentions documentation or writing problems",
                target=writer,
                available="allow_writing"
            ),
            # If evaluation finds conceptual issues, go back to Researcher
            OnCondition(
                condition="Message contains EVALUATION_ISSUES and mentions research or design problems",
                target=researcher,
                available="allow_research"
            ),
            # If evaluation approves, go to Lead for final review
            OnCondition(
                condition="Message contains EVALUATION_COMPLETE and mentions approval or completion",
                target=lead,
                available="allow_leadership"
            ),
            # Otherwise, continue evaluation
            AfterWork(agent=evaluator)
        ])
        
        # Lead can handoff back to any role if issues are found
        register_hand_off(lead, [
            OnCondition(
                condition="Message contains LEADERSHIP_ISSUES and mentions research or design problems",
                target=researcher,
                available="allow_research"
            ),
            OnCondition(
                condition="Message contains LEADERSHIP_ISSUES and mentions code or implementation problems",
                target=developer,
                available="allow_development"
            ),
            OnCondition(
                condition="Message contains LEADERSHIP_ISSUES and mentions documentation or writing problems",
                target=writer,
                available="allow_writing"
            ),
            # Otherwise, continue leadership tasks
            AfterWork(agent=lead)
        ])
        
        logger.info("Registered handoffs between all team roles")
    
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
        task_file_name = "_".join(task.description.split()[:5]).lower()
        task_file_name = "".join(c if c.isalnum() or c == "_" else "_" for c in task_file_name)
        
        # Create logs directory if it doesn't exist
        logs_dir = "logs"
        if not self.fs.exists_sync(logs_dir):
            try:
                # Use the filesystem to create the logs directory
                self.fs.mkdir_sync(logs_dir)
                logger.info(f"Created logs directory at {logs_dir}")
            except Exception as e:
                logger.warning(f"Failed to create logs directory: {str(e)}")
        
        # Save results in the logs directory
        results_file = f"{task_file_name}_results.md"
        results_path_relative = os.path.join(logs_dir, results_file)
        results_path = os.path.join(self.fs.base_dir, results_path_relative)
        
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
            logger.info(f"Results saved to {results_path_relative}")
            
            # Format the response to match PlanningTeam's run_chat format
            return {
                "response": self._chat_result_to_dict(chat_result),
                "chat_history": messages,
                "results_path": results_path_relative,
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
                "allow_development": True,
                "allow_writing": True,
                "allow_evaluation": False,
                "allow_leadership": False
            })
        elif phase == "development":
            self.shared_context.update({
                "allow_research": True,
                "allow_development": True,
                "allow_writing": True,
                "allow_evaluation": True,
                "allow_leadership": False
            })
        elif phase == "testing":
            self.shared_context.update({
                "allow_research": True,
                "allow_development": True,
                "allow_writing": True,
                "allow_evaluation": True,
                "allow_leadership": True
            })
        elif phase == "integration":
            self.shared_context.update({
                "allow_research": False,
                "allow_development": False,
                "allow_writing": False,
                "allow_evaluation": True,
                "allow_leadership": True
            })
        
        logger.info(f"Updated project phase to {phase} with context: {self.shared_context}")

    async def update_task_state(self, task: Task, phase: str, role: str) -> None:
        """Update the task state and trigger appropriate transitions.
        
        Args:
            task: The current task being worked on
            phase: The new phase to transition to
            role: The role that completed their work
        """
        self.update_project_phase(phase)
        
        # Update task tracking
        timestamp = datetime.now().isoformat()
        task_log = {
            "timestamp": timestamp,
            "phase": phase,
            "role": role,
            "status": "completed"
        }
        
        # Save task state
        task_state_path = os.path.join(self.fs.base_dir, "task_state.json")
        try:
            with open(task_state_path, "w") as f:
                json.dump(task_log, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save task state: {str(e)}")
        
        # Trigger appropriate transitions based on phase
        if phase == "research" and role == "researcher":
            # Enable development phase
            self.context.update({"allow_development": True})
            logger.info("Research complete, enabling development phase")
        elif phase == "development" and role == "developer":
            # Enable evaluation phase
            self.context.update({"allow_evaluation": True})
            logger.info("Development complete, enabling evaluation phase")
        elif phase == "writing" and role == "writer":
            # Enable evaluation phase for documentation review
            self.context.update({"allow_evaluation": True})
            logger.info("Writing complete, enabling evaluation phase")
            
        # Update task status
        task.status = f"{phase}_complete"
        
        logger.info(f"Updated task state: {phase} completed by {role}")