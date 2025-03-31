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
            human_input_mode="NEVER",
            model_name="gpt-4o"
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
        """Register handoffs for a hybrid Star/Feedback Loop pattern.
        
        This pattern:
        1. Maintains Lead as the central coordinator (hub in Star pattern)
        2. Allows direct feedback loops between specialists for iterative refinement
        3. Ensures Lead has oversight while enabling efficient specialist collaboration
        4. Uses semantic understanding rather than explicit keywords for transitions
        5. Prevents endless back-and-forth loops with loop counting and circuit breakers
        6. Requires explicit handoff reasoning to improve transparency and debuggability
        """
        researcher = self.get_agent("researcher")
        developer = self.get_agent("developer")
        writer = self.get_agent("writer")
        evaluator = self.get_agent("evaluator")
        lead = self.get_agent("lead")
        executor = self.get_agent("executor")
        
        # Clear any existing handoffs first
        for agent in self.agents.values():
            if hasattr(agent, "_hand_to"):
                agent._hand_to = []
        
        # Set up a shared context for tracking feedback loops and handoff reasons
        self.shared_context.update({
            "feedback_loops": {
                "researcher_developer": 0,
                "developer_researcher": 0,
                "max_loops": 3  # Maximum number of loops before forcing a return to Lead
            },
            "last_handoff_reason": "",
            "require_handoff_reason": True
        })
        
        # STAR PATTERN: Lead as central coordinator (Hub)
        register_hand_off(lead, [
            # Lead to Researcher for research tasks
            OnCondition(
                condition="Message indicates a need for research, information gathering, understanding concepts, or exploring solutions. Must include 'HANDOFF REASON:' explaining why research is needed.",
                target=researcher
            ),
            # Lead to Developer for implementation tasks
            OnCondition(
                condition="Message indicates a need for code implementation, development, programming, or building a solution. Must include 'HANDOFF REASON:' explaining why development is needed.",
                target=developer
            ),
            # Lead to Writer for documentation tasks
            OnCondition(
                condition="Message indicates a need for documentation, content creation, explanation, or written material. Must include 'HANDOFF REASON:' explaining why writing is needed.",
                target=writer
            ),
            # Lead to Evaluator for testing tasks
            OnCondition(
                condition="Message indicates a need for testing, evaluation, review, validation, or quality assessment. Must include 'HANDOFF REASON:' explaining why evaluation is needed.",
                target=evaluator
            )
        ])
        
        # FEEDBACK LOOP: Researcher-Developer for iterative research and implementation
        register_hand_off(researcher, [
            # Only go to Developer if handoff reason is provided and loop count is below threshold
            OnCondition(
                condition="Message indicates research is complete and suggests moving to implementation or coding. Must include 'HANDOFF REASON:'. This handoff will only occur if the researcher-to-developer feedback loop count is below the maximum allowed loops.",
                target=developer
            ),
            # Default: Return to Lead - especially important if we've reached max_loops
            AfterWork(
                agent=lead
            )
        ])
        
        # FEEDBACK LOOP: Developer-Researcher for implementation questions
        register_hand_off(developer, [
            # Developer to Researcher only if loop count is below threshold and reason provided
            OnCondition(
                condition="Message indicates implementation challenges that require additional research or information. Must include 'HANDOFF REASON:'. This handoff will only occur if the developer-to-researcher feedback loop count is below the maximum allowed loops.",
                target=researcher
            ),
            # Developer to Evaluator when implementation is ready for testing
            OnCondition(
                condition="Message indicates implementation is complete and ready for testing or evaluation. Must include 'HANDOFF REASON:' explaining why evaluation is needed.",
                target=evaluator
            ),
            # If we've reached max loops or no specific conditions match, go back to Lead
            AfterWork(
                agent=lead
            )
        ])
        
        # FEEDBACK LOOP: Evaluator-Developer for iterative improvement
        register_hand_off(evaluator, [
            # Evaluator to Developer when implementation needs improvement
            OnCondition(
                condition="Message indicates evaluation found issues that require code changes or implementation fixes. Must include 'HANDOFF REASON:' explaining what needs to be improved.",
                target=developer
            ),
            # Default: Evaluator back to Lead when evaluation is complete
            AfterWork(
                agent=lead
            )
        ])
        
        # Writer always returns to Lead (following Star pattern)
        register_hand_off(writer, [
            AfterWork(
                agent=lead
            )
        ])
        
        # Add logging for handoffs and track context
        for agent_name, agent in self.agents.items():
            if hasattr(agent, "_hand_to") and agent._hand_to:
                # Add a message handler to log handoffs
                original_receive = agent.receive
                
                async def receive_with_logging(self, message, sender, config=None):
                    content = message.get("content", "")
                    
                    # Update shared context with handoff information
                    if "HANDOFF REASON:" in content:
                        reason = content.split("HANDOFF REASON:")[1].split("\n")[0].strip()
                        logger.info(f"Handoff from {sender.name if hasattr(sender, 'name') else 'unknown'} to {self.name} with reason: {reason}")
                        
                        # Update context variables that were previously handled by handlers
                        if hasattr(self, "shared_context"):
                            # Save the last handoff reason
                            self.shared_context["last_handoff_reason"] = reason
                            
                            # Update feedback loop counters
                            if hasattr(sender, "name") and self.name == "developer" and sender.name == "researcher":
                                loops = self.shared_context.get("feedback_loops", {})
                                loops["researcher_developer"] = loops.get("researcher_developer", 0) + 1
                                self.shared_context["feedback_loops"] = loops
                                logger.info(f"Incremented researcher_developer loop count to {loops['researcher_developer']}")
                                
                            elif hasattr(sender, "name") and self.name == "researcher" and sender.name == "developer":
                                loops = self.shared_context.get("feedback_loops", {})
                                loops["developer_researcher"] = loops.get("developer_researcher", 0) + 1
                                self.shared_context["feedback_loops"] = loops
                                logger.info(f"Incremented developer_researcher loop count to {loops['developer_researcher']}")
                    
                    # Send a reminder to include handoff reason in the first message
                    elif sender is not None and sender.name != "executor":
                        logger.warning(f"Agent {sender.name} did not provide a handoff reason to {self.name}")
                        # We will let the message through, but the handoff condition should prevent it from triggering a transition
                        
                        if hasattr(self, "shared_context"):
                            self.shared_context["last_handoff_reason"] = "No reason provided"
                    
                    return await original_receive(message, sender, config)
                
                # Replace the receive method with our logging version
                agent.receive = receive_with_logging.__get__(agent)
        
        logger.info("Registered improved handoff pattern with explicit reasoning requirements and loop prevention")
    
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
        
        This method uses a hybrid Star/Feedback Loop pattern where:
        - Lead serves as the central coordinator (hub in Star pattern)
        - Specialists can directly interact in feedback loops for iterative refinement
        - Lead maintains oversight of the overall process
        
        Args:
            query: The user's query
            teams: Optional list of teams to assign
            
        Returns:
            Dict containing the session results
        """
        # Convert string to Task
        from roboco.core.models import Task
        task = Task(description=query)
        
        # Create context variables with task information and tracking vars
        context = {
            "task": task.model_dump() if hasattr(task, 'model_dump') else (
                task.dict() if hasattr(task, 'dict') else {"description": task.description}
            ),
            # Shared tracking variables for hybrid pattern
            "query_analyzed": False,
            "query_completed": False,
            
            # Track task assignments
            "research_needed": False,
            "research_completed": False,
            "development_needed": False,
            "development_completed": False,
            "writing_needed": False,
            "writing_completed": False,
            "evaluation_needed": False,
            "evaluation_completed": False,
            
            # Track feedback loops
            "feedback_loops": {
                "researcher_developer": 0,  # Count of researcher→developer handoffs
                "developer_researcher": 0,  # Count of developer→researcher handoffs
                "developer_evaluator": 0,   # Count of developer→evaluator handoffs
                "evaluator_developer": 0,   # Count of evaluator→developer handoffs
            },
            
            # Content storage
            "research_findings": "",
            "implementation_status": "",
            "evaluation_results": "",
            "final_response": ""
        }
        
        # Log the start of collaborative session
        logger.info(f"Starting hybrid Star/Feedback Loop session for task: {task.description[:50]}...")
        
        # Run the swarm with the lead as the central coordinator
        try:
            swarm_result = self.run_swarm(
                initial_agent_name="lead",
                query=query,
                context_variables=context,
                max_rounds=25
            )
        except Exception as e:
            import traceback
            error_tb = traceback.format_exc()
            logger.error(f"Exception in hybrid pattern execution: {str(e)}")
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
            feedback_loops_detected = {
                "researcher_developer": 0,
                "developer_researcher": 0,
                "developer_evaluator": 0,
                "evaluator_developer": 0
            }
            
            # Analyze the message flow to identify handoffs and feedback loops
            previous_agent = None
            for msg in messages:
                agent_name = msg.get("name", "unknown")
                if agent_name not in ["user", "unknown"]:
                    agent_sequence.append(agent_name)
                    content = msg.get("content", "")
                    
                    # Track agent contributions
                    if agent_name not in agent_contributions:
                        agent_contributions[agent_name] = []
                    agent_contributions[agent_name].append(len(content))
                    
                    # Track feedback loops
                    if previous_agent and previous_agent != agent_name:
                        if previous_agent == "researcher" and agent_name == "developer":
                            feedback_loops_detected["researcher_developer"] += 1
                        elif previous_agent == "developer" and agent_name == "researcher":
                            feedback_loops_detected["developer_researcher"] += 1
                        elif previous_agent == "developer" and agent_name == "evaluator":
                            feedback_loops_detected["developer_evaluator"] += 1
                        elif previous_agent == "evaluator" and agent_name == "developer":
                            feedback_loops_detected["evaluator_developer"] += 1
                    
                    previous_agent = agent_name
            
            # Write enhanced results file
            with open(results_path, "w") as f:
                f.write(f"# Hybrid Star/Feedback Loop Task Results\n\n")
                f.write(f"## Task Description\n{task.description}\n\n")
                f.write(f"## Solution\n{json.dumps(self._chat_result_to_dict(chat_result), indent=2)}\n\n")
                
                # Add collaboration analysis
                f.write(f"## Collaboration Analysis\n\n")
                f.write(f"### Agent Sequence\n{' → '.join(agent_sequence)}\n\n")
                
                f.write(f"### Contribution Summary\n")
                for agent, sizes in agent_contributions.items():
                    f.write(f"- **{agent}**: {len(sizes)} contributions, {sum(sizes)} total characters\n")
                
                # Add feedback loop analysis
                f.write(f"\n### Feedback Loops Detected\n")
                f.write(f"- Researcher → Developer: {feedback_loops_detected['researcher_developer']} handoffs\n")
                f.write(f"- Developer → Researcher: {feedback_loops_detected['developer_researcher']} handoffs\n")
                f.write(f"- Developer → Evaluator: {feedback_loops_detected['developer_evaluator']} handoffs\n")
                f.write(f"- Evaluator → Developer: {feedback_loops_detected['evaluator_developer']} handoffs\n")
                
                # Calculate efficiency metrics
                total_handoffs = len(agent_sequence) - 1
                direct_feedback_loops = sum(feedback_loops_detected.values())
                star_pattern_handoffs = total_handoffs - direct_feedback_loops
                
                f.write(f"\n### Pattern Efficiency\n")
                f.write(f"- Total handoffs: {total_handoffs}\n")
                f.write(f"- Direct feedback loops: {direct_feedback_loops} ({direct_feedback_loops/total_handoffs*100:.1f}%)\n")
                f.write(f"- Star pattern handoffs: {star_pattern_handoffs} ({star_pattern_handoffs/total_handoffs*100:.1f}%)\n")
            
            logger.info(f"Hybrid pattern session completed with {len(agent_sequence)} agent handoffs")
            logger.info(f"Detected {direct_feedback_loops} direct feedback loops")
            logger.info(f"Results saved to {results_path_relative}")
            
            return {
                "response": self._chat_result_to_dict(chat_result),
                "chat_history": messages,
                "results_path": results_path_relative,
                "collaboration_stats": {
                    "agent_sequence": agent_sequence,
                    "agent_contributions": agent_contributions,
                    "feedback_loops": feedback_loops_detected
                },
                "status": "completed"
            }
        else:
            logger.error(f"Error in hybrid pattern session: {swarm_result.get('error')}")
            return {
                "error": swarm_result.get('error', "Unknown error in hybrid pattern session"),
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