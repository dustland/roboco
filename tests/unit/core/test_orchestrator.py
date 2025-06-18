import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path
import json

from agentx.core.orchestrator import Orchestrator
from agentx.core.team import Team
from agentx.core.agent import Agent
from agentx.tool.executor import ToolResult

@pytest.fixture
def mock_team():
    """Fixture for a mock Team object."""
    # Create mock agents
    agent1 = Mock()
    agent1.name = "agent1"
    
    agent2 = Mock()
    agent2.name = "agent2"
    
    # Create mock team
    team = Mock()
    team.name = "test_team"
    team.agents = {"agent1": agent1, "agent2": agent2}
    team.config = Mock()
    team.config.orchestrator = None  # No orchestrator config for simple tests
    
    return team 

@pytest.fixture
def mock_single_agent_team():
    """Fixture for a single-agent team."""
    agent1 = Mock()
    agent1.name = "solo_agent"
    
    team = Mock()
    team.name = "solo_team"
    team.agents = {"solo_agent": agent1}
    team.config = Mock()
    team.config.orchestrator = None
    
    return team

@pytest.fixture
def orchestrator_with_team(mock_team):
    """Fixture for orchestrator with team."""
    return Orchestrator(mock_team)

@pytest.fixture
def orchestrator_without_team():
    """Fixture for orchestrator without team."""
    return Orchestrator()

class TestOrchestratorInitialization:
    """Test orchestrator initialization."""
    
    def test_orchestrator_with_team(self, mock_team):
        """Test orchestrator initialization with team."""
        orchestrator = Orchestrator(mock_team)
        
        assert orchestrator.team == mock_team
        assert orchestrator.tool_executor is not None
        assert orchestrator.tool_registry is not None
        assert orchestrator.routing_brain is None  # No brain config in mock
    
    def test_orchestrator_without_team(self):
        """Test orchestrator initialization without team."""
        orchestrator = Orchestrator()
        
        assert orchestrator.team is None
        assert orchestrator.tool_executor is not None
        assert orchestrator.tool_registry is not None
        assert orchestrator.routing_brain is None
    
    @patch('agentx.core.orchestrator.Brain')
    def test_orchestrator_with_brain_config(self, mock_brain_class):
        """Test orchestrator initialization with brain configuration."""
        # Mock team with brain config
        team = Mock()
        team.config = Mock()
        orchestrator_config = Mock()
        brain_config = Mock()
        orchestrator_config.brain_config = brain_config
        orchestrator_config.get_default_brain_config = Mock(return_value=brain_config)
        team.config.orchestrator = orchestrator_config
        
        mock_brain = Mock()
        mock_brain_class.return_value = mock_brain
        
        orchestrator = Orchestrator(team)
        
        assert orchestrator.routing_brain == mock_brain
        mock_brain_class.assert_called_once_with(brain_config)

class TestAgentRouting:
    """Test agent routing functionality."""
    
    @pytest.mark.asyncio
    async def test_get_next_agent_single_agent(self, mock_single_agent_team):
        """Test get_next_agent with single agent team."""
        orchestrator = Orchestrator(mock_single_agent_team)
        
        context = {"current_agent": "solo_agent"}
        next_agent = await orchestrator.get_next_agent(context)
        
        assert next_agent == "solo_agent"
    
    @pytest.mark.asyncio
    async def test_get_next_agent_no_team(self):
        """Test get_next_agent without team."""
        orchestrator = Orchestrator()
        
        context = {"current_agent": "default"}
        next_agent = await orchestrator.get_next_agent(context)
        
        assert next_agent == "default"
    
    @pytest.mark.asyncio
    async def test_decide_next_step_no_team(self):
        """Test decide_next_step without team."""
        orchestrator = Orchestrator()
        
        context = {}
        decision = await orchestrator.decide_next_step(context)
        
        assert decision["action"] == "COMPLETE"
        assert decision["reason"] == "No team configured"
    
    @pytest.mark.asyncio
    async def test_decide_next_step_single_agent(self, mock_single_agent_team):
        """Test decide_next_step with single agent."""
        orchestrator = Orchestrator(mock_single_agent_team)
        
        context = {}
        decision = await orchestrator.decide_next_step(context)
        
        assert decision["action"] == "COMPLETE"
        assert decision["reason"] == "Single agent task completed"
    
    @pytest.mark.asyncio
    async def test_decide_next_step_max_rounds(self, mock_team):
        """Test decide_next_step when max rounds reached."""
        orchestrator = Orchestrator(mock_team)
        
        context = {"round_count": 100, "max_rounds": 50}
        decision = await orchestrator.decide_next_step(context)
        
        assert decision["action"] == "COMPLETE"
        assert decision["reason"] == "Maximum rounds reached"
    
    @pytest.mark.asyncio
    async def test_decide_next_step_heuristic_routing(self, mock_team):
        """Test heuristic routing when no brain available."""
        orchestrator = Orchestrator(mock_team)
        
        context = {
            "round_count": 1,
            "max_rounds": 10,
            "current_agent": "agent1"
        }
        last_response = "I have completed my analysis. Now the writer should create the final document."
        
        decision = await orchestrator.decide_next_step(context, last_response)
        
        # Should detect handoff signal and route accordingly
        assert decision["action"] in ["HANDOFF", "CONTINUE", "COMPLETE"]
        assert "reason" in decision
    
    @patch('agentx.core.orchestrator.Brain')
    async def test_decide_next_step_intelligent_routing(self, mock_brain_class):
        """Test intelligent routing with brain."""
        # Mock brain
        mock_brain = AsyncMock()
        mock_brain.generate_response.return_value = '{"action": "HANDOFF", "next_agent": "agent2", "reason": "Task requires different expertise"}'
        mock_brain_class.return_value = mock_brain
        
        # Mock team with brain config
        team = Mock()
        team.config = Mock()
        orchestrator_config = Mock()
        brain_config = Mock()
        orchestrator_config.brain_config = brain_config
        team.config.orchestrator = orchestrator_config
        team.agents = {"agent1": Mock(), "agent2": Mock()}
        
        orchestrator = Orchestrator(team)
        
        context = {
            "round_count": 1,
            "max_rounds": 10,
            "current_agent": "agent1",
            "available_agents": ["agent1", "agent2"]
        }
        last_response = "I need help with writing."
        
        decision = await orchestrator.decide_next_step(context, last_response)
        
        assert decision["action"] == "HANDOFF"
        assert decision["next_agent"] == "agent2"
        assert decision["reason"] == "Task requires different expertise"

class TestToolExecution:
    """Test tool execution functionality."""
    
    @pytest.mark.asyncio
    async def test_execute_tool_calls(self, orchestrator_with_team):
        """Test dispatching tool calls to executor."""
        # Mock tool executor
        orchestrator_with_team.tool_executor = AsyncMock()
        orchestrator_with_team.tool_executor.execute_tool_calls.return_value = [
            {"success": True, "result": "Tool executed successfully"}
        ]
        
        tool_calls = [Mock()]
        result = await orchestrator_with_team.execute_tool_calls(tool_calls, "test_agent")
        
        assert len(result) == 1
        assert result[0]["success"] is True
        orchestrator_with_team.tool_executor.execute_tool_calls.assert_called_once_with(tool_calls, "test_agent")
    
    @pytest.mark.asyncio
    async def test_execute_single_tool(self, orchestrator_with_team):
        """Test executing single tool."""
        # Mock tool executor
        mock_result = Mock()
        mock_result.success = True
        mock_result.result = "Single tool executed"
        
        orchestrator_with_team.tool_executor = AsyncMock()
        orchestrator_with_team.tool_executor.execute_tool.return_value = mock_result
        
        result = await orchestrator_with_team.execute_single_tool("test_tool", "test_agent", arg1="value1")
        
        assert result == mock_result
        orchestrator_with_team.tool_executor.execute_tool.assert_called_once_with("test_tool", "test_agent", arg1="value1")
    
    def test_get_available_tools(self, orchestrator_with_team):
        """Test getting available tools for agent."""
        # Mock tool registry and security policy
        orchestrator_with_team.tool_registry.list_tools.return_value = ["tool1", "tool2", "tool3"]
        orchestrator_with_team.tool_executor.security_policy = Mock()
        orchestrator_with_team.tool_executor.security_policy.TOOL_PERMISSIONS = {
            "test_agent": ["tool1", "tool2"],
            "default": ["tool1"]
        }
        
        tools = orchestrator_with_team.get_available_tools("test_agent")
        assert tools == ["tool1", "tool2"]
        
        tools = orchestrator_with_team.get_available_tools("other_agent")
        assert tools == ["tool1"]  # Falls back to default
    
    @patch('agentx.core.orchestrator.get_tool_schemas')
    def test_get_tool_schemas_for_agent(self, mock_get_schemas, orchestrator_with_team):
        """Test getting tool schemas for agent."""
        mock_schemas = [{"name": "tool1", "description": "Test tool"}]
        mock_get_schemas.return_value = mock_schemas
        
        # Mock available tools
        orchestrator_with_team.get_available_tools = Mock(return_value=["tool1"])
        
        schemas = orchestrator_with_team.get_tool_schemas_for_agent("test_agent")
        
        assert schemas == mock_schemas
        mock_get_schemas.assert_called_once_with(["tool1"])
    
    def test_get_execution_stats(self, orchestrator_with_team):
        """Test getting execution statistics."""
        mock_stats = {"total_executions": 10}
        orchestrator_with_team.tool_executor.get_execution_stats.return_value = mock_stats
        
        stats = orchestrator_with_team.get_execution_stats()
        assert stats == mock_stats
    
    def test_clear_execution_history(self, orchestrator_with_team):
        """Test clearing execution history."""
        orchestrator_with_team.clear_execution_history()
        orchestrator_with_team.tool_executor.clear_history.assert_called_once()

class TestGlobalOrchestrator:
    """Test global orchestrator functionality."""
    
    @patch('agentx.core.orchestrator._global_orchestrator', None)
    def test_get_orchestrator_creates_instance(self):
        """Test that get_orchestrator creates global instance."""
        from agentx.core.orchestrator import get_orchestrator
        
        orchestrator = get_orchestrator()
        assert orchestrator is not None
        assert orchestrator.team is None  # Global orchestrator has no team
    
    def test_get_orchestrator_returns_same_instance(self):
        """Test that get_orchestrator returns same instance."""
        from agentx.core.orchestrator import get_orchestrator
        
        orchestrator1 = get_orchestrator()
        orchestrator2 = get_orchestrator()
        
        assert orchestrator1 is orchestrator2

class TestHeuristicRouting:
    """Test heuristic routing logic."""
    
    @pytest.mark.asyncio
    async def test_heuristic_detects_completion_signals(self, mock_team):
        """Test that heuristic routing detects completion signals."""
        orchestrator = Orchestrator(mock_team)
        
        context = {"round_count": 1, "current_agent": "agent1"}
        
        # Test completion signal
        completion_response = "The task is now complete and ready for submission."
        decision = await orchestrator.decide_next_step(context, completion_response)
        assert decision["action"] == "COMPLETE"
        
        # Test finished signal
        finished_response = "I have finished all the required work."
        decision = await orchestrator.decide_next_step(context, finished_response)
        assert decision["action"] == "COMPLETE"
    
    @pytest.mark.asyncio
    async def test_heuristic_detects_handoff_signals(self, mock_team):
        """Test that heuristic routing detects handoff signals."""
        orchestrator = Orchestrator(mock_team)
        
        context = {
            "round_count": 1,
            "current_agent": "agent1",
            "available_agents": ["agent1", "agent2"]
        }
        
        # Test handoff signal
        handoff_response = "Now I need to hand this off to agent2 for the next step."
        decision = await orchestrator.decide_next_step(context, handoff_response)
        assert decision["action"] == "HANDOFF"
        assert decision["next_agent"] == "agent2"
    
    @pytest.mark.asyncio
    async def test_heuristic_defaults_to_continue(self, mock_team):
        """Test that heuristic routing defaults to continue."""
        orchestrator = Orchestrator(mock_team)
        
        context = {"round_count": 1, "current_agent": "agent1"}
        normal_response = "I am working on the analysis and making good progress."
        
        decision = await orchestrator.decide_next_step(context, normal_response)
        assert decision["action"] == "CONTINUE" 