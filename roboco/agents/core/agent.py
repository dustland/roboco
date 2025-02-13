from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any, Optional
import autogen
from datetime import datetime

class AgentState(BaseModel):
    id: str
    role: str
    capabilities: list[str]
    current_task: Optional[str] = None

class RoboCoAgentConfig(BaseModel):
    role: str
    max_consecutive_auto_reply: int = 5
    code_execution_config: dict = {"work_dir": "coding"}

class RoboCoAgent:
    def __init__(self, config: RoboCoAgentConfig):
        self.agent = autogen.AssistantAgent(
            name=config.role,
            llm_config={
                "config_list": [{"model": "gpt-4o", "api_key": "YOUR_API_KEY"}],
                "temperature": 0.7
            },
            system_message=f"You are a {config.role} for RoboCo robotics systems",
            max_consecutive_auto_reply=config.max_consecutive_auto_reply,
            code_execution_config=config.code_execution_config
        )

    async def execute_task(self, task: str):
        self.agent.send(task, self.agent, request_reply=True)
        return self.agent.last_message()

class BaseAgent(ABC):
    def __init__(self, agent_id: str, role: str, capabilities: list[str], system_prompt: str):
        self.name = agent_id
        self.role = role
        self.capabilities = capabilities
        self.memory = []  # Stores past interactions
        self.iteration_log = []  # Tracks improvement history
        self.state = AgentState(
            id=agent_id,
            role=role,
            capabilities=capabilities
        )
        self.iteration_count = 0
        self.current_task = None

    @abstractmethod
    async def execute_task(self, task: str) -> Any:
        pass

    def add_capability(self, capability: str):
        self.state.capabilities.append(capability)

    def record_outcome(self, task: str, result: Any):
        '''Log successful/unsuccessful task executions'''
        self.iteration_log.append({
            'timestamp': datetime.now(),
            'task': task,
            'result': result
        })

    def begin_iteration(self, task: str):
        self.current_task = task
        self.iteration_count += 1

    def finalize_iteration(self, success_metrics: dict):
        '''Store outcomes and generate improvements'''
        self.record_outcome(self.current_task, {
            'metrics': success_metrics,
            'timestamp': datetime.now()
        })
