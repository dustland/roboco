from __future__ import annotations
import json
import importlib
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from roboco.core.task_step import TaskStep
from roboco.core.agent import Agent
from roboco.core.config import TeamConfig
from roboco.core.tool import get_tool_registry

# For now, we'll keep a reference to Agent, but the config will change
# to be AgentConfig as per the design.

class Team(BaseModel):
    """
    A passive data structure that holds the complete state and configuration for a task.
    This includes the agents, their relationships, available tools, and the full
    history of TaskSteps. It is the "what" and the "who" of the collaboration.
    """
    name: str
    agents: Dict[str, Agent] = Field(default_factory=dict)
    max_rounds: int = 10
    # The 'tools' field will be added later once ToolConfig is defined.
    history: List[TaskStep] = Field(default_factory=list)
    # Other config like collaboration graph can be added here.

    @classmethod
    def from_config_file(cls, config_path: str) -> "Team":
        """
        Loads team configuration from a JSON file and returns a Team instance.
        """
        config_file = Path(config_path)
        if not config_file.is_file():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        config_dir = config_file.parent
        config_data = json.loads(config_file.read_text())
        config = TeamConfig.model_validate(config_data)

        # Load and register tools
        tool_registry = get_tool_registry()
        for tool_name, tool_def in config.tool_definitions.items():
            try:
                module_path, class_name = tool_def.source.rsplit(':', 1)
                module = importlib.import_module(module_path)
                tool_class = getattr(module, class_name)
                # We assume tool classes can be instantiated without arguments for now.
                # This could be extended to pass config to tools.
                tool_instance = tool_class()
                tool_registry.register_tool(tool_instance)
                print(f"Successfully loaded and registered tool: {tool_name}")
            except Exception as e:
                print(f"Failed to load tool {tool_name} from {tool_def.source}: {e}")
                # Decide if we should raise an error or just warn
                raise ImportError(f"Could not load tool {tool_name}") from e

        # Create agents
        agents = {}
        all_available_tools = tool_registry.list_tools()
        for agent_config in config.agents:
            # Load system message from file
            prompt_path = config_dir / agent_config.system_message_prompt
            if not prompt_path.is_file():
                raise FileNotFoundError(f"System message file not found for agent {agent_config.name}: {prompt_path}")
            system_message = prompt_path.read_text()

            # Get tool schemas for the agent
            agent_tool_names = agent_config.tools
            # Validate that the agent's tools are available
            for tool_name in agent_tool_names:
                if tool_name not in all_available_tools:
                    raise ValueError(f"Agent '{agent_config.name}' requires tool '{tool_name}' which is not defined or loaded.")
            
            agent_tools_schema = tool_registry.get_tool_schemas(agent_tool_names)

            agent = Agent(
                name=agent_config.name,
                system_message=system_message,
                model=agent_config.model,
                tools=agent_tools_schema
            )
            agents[agent.name] = agent

        # Assemble and return the team
        return cls(
            name=config.name,
            agents=agents,
            max_rounds=config.max_rounds
        )

    def add_step(self, step: TaskStep) -> None:
        """Adds a new TaskStep to the team's history."""
        self.history.append(step)

    def get_agent(self, name: str) -> Agent | None:
        """Retrieves an agent by name."""
        return self.agents.get(name)

    class Config:
        arbitrary_types_allowed = True 