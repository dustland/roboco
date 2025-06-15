import pytest
import asyncio
from pathlib import Path

from agentx.core.team import Team
from agentx.core.orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_basic_task_execution():
    """Test basic task execution workflow."""
    
    # Load team configuration
    team_config_path = "tests/test_workspaces/sample_team/team.yaml"
    team = Team.from_config(team_config_path)
    
    # Verify team loaded correctly
    assert team.name == "sample_team"
    assert len(team.agents) == 3
    assert "coordinator" in team.agents
    
    # Create orchestrator
    orchestrator = Orchestrator(team)
    
    # Start a task
    task_id = await orchestrator.start_task(
        prompt="Analyze the current state of AI development and write a brief summary",
        initial_agent="coordinator"
    )
    
    # Verify task was created
    assert task_id is not None
    assert task_id in orchestrator.active_tasks
    
    # Get task state
    task_state = orchestrator.get_task_state(task_id)
    assert task_state is not None
    assert task_state.task_id == task_id
    assert task_state.initial_prompt == "Analyze the current state of AI development and write a brief summary"
    assert task_state.current_agent == "coordinator"
    assert task_state.round_count == 0
    assert not task_state.is_complete
    assert not task_state.is_paused
    
    # Execute one step
    events = []
    
    async def event_callback(event):
        events.append(event)
    
    # Execute the task (this will run the placeholder implementation)
    final_state = await orchestrator.execute_task(task_id, event_callback=event_callback)
    
    # Verify execution completed
    assert final_state.is_complete
    assert final_state.round_count > 0
    assert len(final_state.history) > 0
    
    # Verify events were emitted
    assert len(events) > 0
    
    # Check that we got the expected event types
    event_types = [event.type for event in events]
    assert "event_task_start" in event_types
    assert "event_agent_start" in event_types
    assert "event_agent_complete" in event_types
    assert "event_task_complete" in event_types
    
    # Verify task workspace was created
    workspace_path = orchestrator.workspace_dir / task_id
    assert workspace_path.exists()
    assert (workspace_path / "task_state.json").exists()


@pytest.mark.asyncio
async def test_task_pause_resume():
    """Test task pause and resume functionality."""
    
    # Load team and create orchestrator
    team = Team.from_config("tests/test_workspaces/sample_team/team.yaml")
    orchestrator = Orchestrator(team)
    
    # Start a task
    task_id = await orchestrator.start_task(
        prompt="Test task for pause/resume",
        initial_agent="coordinator"
    )
    
    # Pause the task
    await orchestrator.pause_task(task_id)
    
    # Verify task is paused
    task_state = orchestrator.get_task_state(task_id)
    assert task_state.is_paused
    
    # Resume the task
    await orchestrator.resume_task(task_id)
    
    # Verify task is no longer paused
    task_state = orchestrator.get_task_state(task_id)
    assert not task_state.is_paused


def test_team_configuration_loading():
    """Test comprehensive team configuration loading."""
    
    # Load team configuration
    team = Team.from_config("tests/test_workspaces/sample_team/team.yaml")
    
    # Verify team properties
    assert team.name == "sample_team"
    assert team.max_rounds == 20
    
    # Verify agents
    assert len(team.agents) == 3
    coordinator = team.get_agent("coordinator")
    assert coordinator is not None
    assert coordinator.description == "Main coordinator agent that manages task flow"
    assert "file_operations" in coordinator.tools
    assert "web_search" in coordinator.tools
    
    analyst = team.get_agent("analyst")
    assert analyst is not None
    assert analyst.description == "Data analysis and research specialist"
    assert "file_operations" in analyst.tools
    assert "data_analysis" in analyst.tools
    
    writer = team.get_agent("writer")
    assert writer is not None
    assert writer.description == "Content creation and documentation specialist"
    assert "file_operations" in writer.tools
    
    # Verify tools
    assert len(team.tools) == 3
    file_ops = team.get_tool("file_operations")
    assert file_ops is not None
    assert file_ops.type == "builtin"
    
    web_search = team.get_tool("web_search")
    assert web_search is not None
    assert web_search.type == "python_function"
    
    # Verify handoff rules
    assert len(team.config.handoff_rules) == 4
    
    # Test handoff validation
    assert team.validate_handoff("coordinator", "analyst")
    assert team.validate_handoff("coordinator", "writer")
    assert team.validate_handoff("analyst", "writer")
    assert team.validate_handoff("writer", "coordinator")
    assert not team.validate_handoff("coordinator", "nonexistent")
    
    # Test agent tools retrieval
    coordinator_tools = team.get_agent_tools("coordinator")
    assert len(coordinator_tools) == 2
    tool_names = [tool.name for tool in coordinator_tools]
    assert "file_operations" in tool_names
    assert "web_search" in tool_names
    
    # Test handoff targets
    coordinator_targets = team.get_handoff_targets("coordinator")
    assert "analyst" in coordinator_targets
    assert "writer" in coordinator_targets


def test_prompt_rendering():
    """Test agent prompt template rendering."""
    
    # Load team
    team = Team.from_config("tests/test_workspaces/sample_team/team.yaml")
    
    # Prepare context
    context = {
        'task_prompt': 'Test task prompt',
        'history': [],
        'available_tools': team.get_agent_tools('coordinator'),
        'handoff_targets': team.get_handoff_targets('coordinator'),
        'artifacts': {}
    }
    
    # Render coordinator prompt
    prompt = team.render_agent_prompt('coordinator', context)
    
    # Verify prompt contains expected content
    assert 'Test task prompt' in prompt
    assert 'Coordinator agent' in prompt
    assert 'file_operations' in prompt
    assert 'web_search' in prompt
    assert 'Analyst' in prompt
    assert 'Writer' in prompt
    
    # Test with different agent
    analyst_context = {
        'task_prompt': 'Test task prompt',
        'history': [],
        'available_tools': team.get_agent_tools('analyst'),
        'handoff_targets': team.get_handoff_targets('analyst'),
        'artifacts': {}
    }
    analyst_prompt = team.render_agent_prompt('analyst', analyst_context)
    assert 'Analyst agent' in analyst_prompt
    assert 'data_analysis' in analyst_prompt


if __name__ == "__main__":
    # Run a simple test
    asyncio.run(test_basic_task_execution()) 