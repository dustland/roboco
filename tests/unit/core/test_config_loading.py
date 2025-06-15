import pytest
from pathlib import Path
import json
from roboco.core.team import Team
from roboco.core.tool import get_tool_registry

# It's better to use absolute paths in tests to avoid issues with the test runner's CWD
# This finds the project root based on the test file's location.
# This assumes tests are run from the project root or the tests folder.
# A more robust solution might use a dedicated fixture in conftest.py
try:
    # This works when tests are run from the project root
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.resolve()
    # Check if a known file exists to validate root
    if not (PROJECT_ROOT / 'pyproject.toml').exists():
        # This works when the CWD is inside the tests folder
        PROJECT_ROOT = Path.cwd().parent 
except FileNotFoundError:
    PROJECT_ROOT = Path.cwd()


SIMPLE_TEAM_CONFIG_PATH = PROJECT_ROOT / "examples" / "simple-research-team" / "team.json"

@pytest.fixture
def tool_registry():
    """Fixture to get a clean tool registry for each test."""
    registry = get_tool_registry()
    registry.clear()
    yield registry
    registry.clear()

def test_load_team_from_config(tool_registry):
    """
    Tests the successful loading and validation of a team from a JSON config file.
    """
    assert SIMPLE_TEAM_CONFIG_PATH.exists(), f"Test config file must exist at {SIMPLE_TEAM_CONFIG_PATH}"
    
    team = Team.from_config_file(str(SIMPLE_TEAM_CONFIG_PATH))
    
    assert isinstance(team, Team)
    assert team.name == "Simple Research Team"
    assert team.max_rounds == 25
    
    # Check agents
    assert len(team.agents) == 1
    assert "researcher" in team.agents
    
    researcher = team.get_agent("researcher")
    assert researcher is not None
    assert researcher.model == "claude-3-haiku-20240307"
    assert "You are a research assistant." in researcher.system_message
    
    # Check tools assigned to the agent
    assert len(researcher.tools) == 3
    agent_tool_names = [tool['function']['name'] for tool in researcher.tools]
    assert "read_file" in agent_tool_names
    assert "write_file" in agent_tool_names
    assert "list_directory" in agent_tool_names
    
    # Check global registry for all tools from the loaded class
    registered_tools = tool_registry.list_tools()
    assert "read_file" in registered_tools
    assert "write_file" in registered_tools
    assert "list_directory" in registered_tools
    # Also check a tool that is part of the class but was NOT assigned to the agent
    assert "echo_message" in registered_tools

def test_load_team_with_nonexistent_config():
    """
    Tests that loading a non-existent config file raises FileNotFoundError.
    """
    with pytest.raises(FileNotFoundError):
        Team.from_config_file("non_existent_config.json")

def test_load_team_with_missing_prompt_file(tool_registry, tmp_path):
    """
    Tests that a missing system prompt file raises FileNotFoundError.
    """
    config = {
        "version": "1.0",
        "name": "Test Team",
        "agents": [{
            "name": "agent1",
            "system_message_prompt": "non_existent_prompt.md",
            "model": "test-model"
        }]
    }
    config_path = tmp_path / "team.json"
    config_path.write_text(json.dumps(config))
    
    with pytest.raises(FileNotFoundError):
        Team.from_config_file(str(config_path))

def test_load_team_with_invalid_tool_source(tool_registry, tmp_path):
    """
    Tests that an invalid tool source string raises an ImportError.
    """
    config = {
        "version": "1.0",
        "name": "Test Team",
        "agents": [],
        "tool_definitions": {
            "bad_tool": {
                "source": "non.existent.module:NonExistentTool"
            }
        }
    }
    config_path = tmp_path / "team.json"
    config_path.write_text(json.dumps(config))

    with pytest.raises(ImportError):
        Team.from_config_file(str(config_path))

def test_load_team_with_undefined_agent_tool(tool_registry, tmp_path):
    """
    Tests that an agent referencing an undefined tool raises a ValueError.
    """
    config = {
        "version": "1.0",
        "name": "Test Team",
        "agents": [{
            "name": "agent1",
            "system_message_prompt": "prompt.md",
            "model": "test-model",
            "tools": ["some_tool_that_does_not_exist"]
        }],
        "tool_definitions": {}
    }
    config_path = tmp_path / "team.json"
    (tmp_path / "prompt.md").write_text("prompt")
    config_path.write_text(json.dumps(config))

    with pytest.raises(ValueError, match="requires tool 'some_tool_that_does_not_exist' which is not defined or loaded"):
        Team.from_config_file(str(config_path)) 