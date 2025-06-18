import pytest
import asyncio
from pathlib import Path

from agentx.core.team import Team
from agentx.core.task import TaskExecutor, create_task


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
    
    # Create task executor directly
    task = create_task(team_config_path)
    
    # Verify task was created
    assert task is not None
    assert task.task_id is not None
    assert not task.is_complete
    
    # Start the task
    task.start_task(
        prompt="Analyze the current state of AI development and write a brief summary",
        initial_agent="coordinator"
    )
    
    # Verify task state after starting
    assert task.initial_prompt == "Analyze the current state of AI development and write a brief summary"
    assert task.current_agent == "coordinator"
    assert task.round_count == 0
    assert not task.is_complete
    
    # Execute one step
    result = None
    async for step_result in task.step():
        result = step_result
        break  # Just test one step
    
    # Verify step execution
    assert result is not None
    assert "status" in result
    assert task.round_count >= 1
    assert len(task.history) > 0
    
    # Verify task workspace was created
    assert task.workspace_dir.exists()


@pytest.mark.asyncio
async def test_task_pause_resume():
    """Test task pause and resume functionality."""
    
    # Load team and create task
    team = Team.from_config("tests/test_workspaces/sample_team/team.yaml")
    task = create_task("tests/test_workspaces/sample_team/team.yaml")
    
    # Start a task
    task.start_task(
        prompt="Test task for pause/resume",
        initial_agent="coordinator"
    )
    
    # Pause the task
    task.is_paused = True
    
    # Verify task is paused
    assert task.is_paused
    
    # Resume the task
    task.is_paused = False
    
    # Verify task is no longer paused
    assert not task.is_paused


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
    assert len(team.config.handoffs) == 4
    
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
    
    # Verify analyst prompt
    assert 'Test task prompt' in analyst_prompt
    assert 'Analyst' in analyst_prompt


@pytest.mark.asyncio
async def test_streaming_execution():
    """Test streaming task execution."""
    
    # Create task
    task = create_task("tests/test_workspaces/sample_team/team.yaml")
    
    # Execute with streaming
    stream_chunks = []
    async for chunk in task.execute_task(
        prompt="Simple test task",
        initial_agent="coordinator",
        stream=True
    ):
        stream_chunks.append(chunk)
        # Break after a few chunks to avoid long execution
        if len(stream_chunks) >= 5:
            break
    
    # Verify we got streaming chunks
    assert len(stream_chunks) > 0
    
    # Check chunk structure
    for chunk in stream_chunks:
        assert isinstance(chunk, dict)
        if "type" in chunk:
            assert chunk["type"] in ["content", "routing_decision", "handoff"]


if __name__ == "__main__":
    # Run a simple test
    asyncio.run(test_basic_task_execution()) 