import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json

from agentx.core.orchestrator import Orchestrator
from agentx.core.team import Team
from agentx.core.agent import Agent
from agentx.core.tool import ToolResult
from agentx.core.task_step import TaskStep, TextPart, ToolCallPart, ToolResultPart

@pytest.fixture
def mock_team():
    """Fixture for a mock Team object."""
    agent1 = Agent(
        name="test_agent",
        system_message="You are a test agent.",
        model="test-model",
        tools=[{"type": "function", "function": {"name": "test_tool", "description": "A test tool"}}]
    )
    team = Team(name="Test Team", agents={"test_agent": agent1}, max_rounds=5)
    return team

@pytest.fixture
def mock_tool_registry():
    """Fixture to mock the tool registry."""
    with patch('agentx.core.orchestrator.get_tool_registry') as mock_get_registry:
        mock_registry = Mock()
        mock_registry.execute_tool_sync.return_value = ToolResult(success=True, result="Tool executed successfully")
        mock_get_registry.return_value = mock_registry
        yield mock_registry

def test_orchestrator_start(mock_team, tmp_path):
    """Test the start method initializes the task and yields the first step."""
    orchestrator = Orchestrator(team=mock_team, workspace_dir=str(tmp_path))
    
    # Run the start generator
    events = list(orchestrator.start("Initial prompt"))

    assert orchestrator.is_running
    assert len(mock_team.history) == 1
    first_step = mock_team.history[0]
    assert first_step.agent_name == "user"
    assert isinstance(first_step.parts[0], TextPart)
    assert first_step.parts[0].text == "Initial prompt"

    # Check yielded events for the first step
    assert events[0]['type'] == 'step_start'
    assert events[1]['type'] == 'text_part'
    assert events[2]['type'] == 'step_end'

@patch('litellm.completion')
def test_orchestrator_step_text_response(mock_completion, mock_team, tmp_path):
    """Test a single step that results in a text response."""
    orchestrator = Orchestrator(team=mock_team, workspace_dir=str(tmp_path))
    list(orchestrator.start("Initial prompt")) # Consume start events

    # Mock the litellm response
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "This is a text response."
    mock_response.choices[0].message.tool_calls = None
    mock_completion.return_value = mock_response

    # Execute a step
    events = list(orchestrator.step())
    
    # History should now have user prompt + agent response
    assert len(mock_team.history) == 2
    agent_step = mock_team.history[1]
    assert agent_step.agent_name == "test_agent"
    assert agent_step.parts[0].text == "This is a text response."
    mock_completion.assert_called_once()

@patch('litellm.completion')
def test_orchestrator_step_tool_call_response(mock_completion, mock_team, mock_tool_registry, tmp_path):
    """Test a single step that results in a tool call and its execution."""
    orchestrator = Orchestrator(team=mock_team, workspace_dir=str(tmp_path))
    list(orchestrator.start("Initial prompt"))

    # Mock the litellm response to include a tool call
    mock_tool_call = MagicMock()
    mock_tool_call.id = "call_123"
    mock_tool_call.function.name = "test_tool"
    mock_tool_call.function.arguments = '{"arg1": "value1"}'
    
    mock_response = MagicMock()
    mock_response.choices[0].message.content = None
    mock_response.choices[0].message.tool_calls = [mock_tool_call]
    mock_completion.return_value = mock_response

    # Execute the step
    events = list(orchestrator.step())

    # History should contain: 1. user_prompt, 2. agent_tool_call, 3. tool_executor_result
    assert len(mock_team.history) == 3
    
    # Verify the agent's tool call step (history item 2)
    agent_step = mock_team.history[1]
    assert agent_step.agent_name == "test_agent"
    assert isinstance(agent_step.parts[0], ToolCallPart)
    assert agent_step.parts[0].tool_call.tool_name == "test_tool"
    
    # Verify the tool execution result step (history item 3)
    tool_step = mock_team.history[2]
    assert tool_step.agent_name == "tool_executor"
    assert isinstance(tool_step.parts[0], ToolResultPart)
    assert tool_step.parts[0].tool_result.result == "Tool executed successfully"
    mock_tool_registry.execute_tool_sync.assert_called_once_with("test_tool", arg1="value1")

@patch('litellm.completion')
def test_orchestrator_interruption_flow(mock_completion, mock_team, tmp_path):
    """Test that a user interruption correctly alters the conversation flow."""
    orchestrator = Orchestrator(team=mock_team, workspace_dir=str(tmp_path))
    list(orchestrator.start("Initial prompt"))

    # Mock a standard text response for the first step
    mock_response1 = MagicMock()
    mock_response1.choices[0].message.content = "Agent's first response"
    mock_response1.choices[0].message.tool_calls = None
    mock_completion.return_value = mock_response1
    
    # Execute the first step
    list(orchestrator.step())
    assert len(mock_team.history) == 2
    assert mock_team.history[-1].parts[0].text == "Agent's first response"

    # Now, the user interrupts
    interruption_events = list(orchestrator.add_user_message("Stop. Do this instead."))
    assert len(mock_team.history) == 3
    assert mock_team.history[-1].agent_name == "user"
    assert mock_team.history[-1].parts[0].text == "Stop. Do this instead."

    # Mock a new response that considers the interruption
    mock_response2 = MagicMock()
    mock_response2.choices[0].message.content = "Okay, I will do that instead."
    mock_response2.choices[0].message.tool_calls = None
    mock_completion.return_value = mock_response2

    # Execute the next step
    list(orchestrator.step())
    assert len(mock_team.history) == 4
    
    # Verify the agent's response is to the interruption
    last_agent_message = mock_team.history[-1]
    assert last_agent_message.agent_name == "test_agent"
    assert last_agent_message.parts[0].text == "Okay, I will do that instead."
    
    # Verify litellm was called twice
    assert mock_completion.call_count == 2
    # The second to last message should be the agent's previous turn.
    # The last message should be the user interruption.
    last_call_messages = mock_completion.call_args.kwargs['messages']
    assert last_call_messages[-2]['role'] == 'assistant'
    assert last_call_messages[-1]['role'] == 'user'
    assert "Stop. Do this instead" in last_call_messages[-1]['content'] 