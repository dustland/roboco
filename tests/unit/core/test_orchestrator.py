import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path
import json

from agentx.core.orchestrator import Orchestrator
from agentx.core.task import Task
from agentx.core.config import TeamConfig, AgentConfig, BrainConfig
from agentx.core.agent import Agent

@pytest.fixture
def mock_task():
    """Fixture for a mock Task object."""
    # Create mock agents
    agent1 = Mock()
    agent1.name = "agent1"
    agent1.config = Mock()
    agent1.config.llm_config = Mock()
    
    agent2 = Mock()
    agent2.name = "agent2" 
    agent2.config = Mock()
    agent2.config.llm_config = Mock()
    
    # Create mock task
    task = Mock()
    task.task_id = "test_task_123"
    task.agents = {"agent1": agent1, "agent2": agent2}
    task.team_config = Mock()
    task.team_config.orchestrator = None  # No orchestrator config for simple tests
    task.team_config.name = "test_team"
    
    return task

@pytest.fixture
def mock_single_agent_task():
    """Fixture for a single-agent task."""
    agent1 = Mock()
    agent1.name = "solo_agent"
    agent1.config = Mock()
    agent1.config.llm_config = Mock()
    
    task = Mock()
    task.task_id = "solo_task_123"
    task.agents = {"solo_agent": agent1}
    task.team_config = Mock()
    task.team_config.orchestrator = None
    task.team_config.name = "solo_team"
    
    return task

@pytest.fixture
def orchestrator_with_task(mock_task):
    """Fixture for orchestrator with task."""
    return Orchestrator(mock_task)

@pytest.fixture
def orchestrator_without_task():
    """Fixture for orchestrator without task."""
    return Orchestrator()

class TestOrchestratorInitialization:
    """Test orchestrator initialization."""
    
    def test_orchestrator_with_task(self, mock_task):
        """Test orchestrator initialization with task."""
        orchestrator = Orchestrator(mock_task)

        assert orchestrator.task == mock_task
        assert orchestrator.routing_brain is not None  # Brain is now mandatory for tasks

    def test_orchestrator_without_task(self):
        """Test orchestrator initialization without task."""
        orchestrator = Orchestrator()
        
        assert orchestrator.task is None
        assert orchestrator.routing_brain is None
    
    @patch('agentx.core.orchestrator.Brain')
    def test_orchestrator_with_brain_config(self, mock_brain_class):
        """Test orchestrator initialization with brain configuration."""
        # Mock task with brain config
        task = Mock()
        task.task_id = "test_task_123"
        task.team_config = Mock()
        orchestrator_config = Mock()
        brain_config = Mock()
        orchestrator_config.brain_config = brain_config
        task.team_config.orchestrator = orchestrator_config
        task.agents = {"agent1": Mock()}
        
        mock_brain = Mock()
        mock_brain_class.from_config.return_value = mock_brain
        
        orchestrator = Orchestrator(task)
        
        assert orchestrator.routing_brain == mock_brain
        mock_brain_class.from_config.assert_called_once_with(brain_config)

class TestAgentRouting:
    """Test agent routing functionality."""
    
    @pytest.mark.asyncio
    async def test_get_next_agent_single_agent(self, mock_single_agent_task):
        """Test get_next_agent with single agent task."""
        orchestrator = Orchestrator(mock_single_agent_task)
        
        context = {"current_agent": "solo_agent"}
        next_agent = await orchestrator.get_next_agent(context)
        
        assert next_agent == "solo_agent"
    
    @pytest.mark.asyncio
    async def test_get_next_agent_no_task(self):
        """Test get_next_agent without task."""
        orchestrator = Orchestrator()
        
        context = {"current_agent": "default"}
        next_agent = await orchestrator.get_next_agent(context)
        
        assert next_agent == "default"
    
    @pytest.mark.asyncio
    async def test_decide_next_step_no_task(self):
        """Test decide_next_step without task."""
        orchestrator = Orchestrator()
        
        context = {}
        decision = await orchestrator.decide_next_step(context)
        
        assert decision["action"] == "COMPLETE"
        assert decision["reason"] == "No task configured"
    
    @pytest.mark.asyncio
    async def test_decide_next_step_single_agent(self, mock_single_agent_task):
        """Test decide_next_step with single agent."""
        orchestrator = Orchestrator(mock_single_agent_task)
        
        context = {}
        decision = await orchestrator.decide_next_step(context)
        
        assert decision["action"] == "CONTINUE"
        assert decision["reason"] == "Single agent"
    
    @pytest.mark.asyncio
    async def test_decide_next_step_max_rounds(self, mock_task):
        """Test decide_next_step when max rounds reached."""
        orchestrator = Orchestrator(mock_task)
        
        context = {"round_count": 100, "max_rounds": 50}
        decision = await orchestrator.decide_next_step(context)
        
        assert decision["action"] in ["HANDOFF", "CONTINUE", "COMPLETE"]
        assert "reason" in decision
    
    @pytest.mark.asyncio
    async def test_decide_next_step_multi_agent_routing(self, mock_task):
        """Test routing with multi-agent task."""
        # Mock the brain for the task
        mock_brain = Mock()
        mock_brain.generate_response = AsyncMock()
        mock_brain.generate_response.return_value = Mock(content='{"action": "CONTINUE", "next_agent": "agent1"}')
        
        orchestrator = Orchestrator(mock_task)
        orchestrator.routing_brain = mock_brain
        
        context = {
            "round_count": 1,
            "max_rounds": 10,
            "current_agent": "agent1"
        }
        last_response = "I have completed my analysis."
        
        decision = await orchestrator.decide_next_step(context, last_response)
        
        # Should use brain decision
        assert decision["action"] in ["HANDOFF", "CONTINUE", "COMPLETE"]
        assert "reason" in decision
    
    @pytest.mark.asyncio
    async def test_decide_next_step_intelligent_routing(self, mock_task):
        """Test intelligent routing with brain."""
        # Mock brain response
        mock_response = Mock()
        mock_response.content = '{"action": "HANDOFF", "next_agent": "agent2"}'
        
        mock_brain = Mock()
        mock_brain.generate_response = AsyncMock()
        mock_brain.generate_response.return_value = mock_response
        
        # Set up task with brain
        orchestrator = Orchestrator(mock_task)
        orchestrator.routing_brain = mock_brain
        
        context = {
            "round_count": 1,
            "max_rounds": 10,
            "current_agent": "agent1"
        }
        last_response = "I need to hand this off to agent2."
        
        decision = await orchestrator.determine_handoff(context, last_response)
        
        assert decision["action"] == "HANDOFF"
        assert decision["next_agent"] == "agent2"



 