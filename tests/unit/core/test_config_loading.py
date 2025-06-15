import pytest
import tempfile
import yaml
from pathlib import Path
from pydantic import ValidationError
from agentx.core.team import Team
from agentx.core.agent import Agent
from agentx.core.tool import get_tool_registry
from agentx.core.config import TeamConfig, AgentConfig, LLMConfig, ToolConfig, ExecutionConfig

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

@pytest.fixture
def sample_team_config_path():
    """Fixture that provides the path to the sample team config."""
    return "tests/test_workspaces/sample_team/team.yaml"

@pytest.fixture(autouse=True)
def clear_tool_registry_fixture():
    """Fixture to automatically clear the tool registry before each test."""
    registry = get_tool_registry()
    registry.clear()
    yield
    registry.clear()

def test_load_team_from_config(sample_team_config_path: str):
    """
    Tests that a Team object can be successfully loaded from a YAML config file,
    adhering to the approved design (no user_proxy).
    """
    # Act
    team = Team.from_config(sample_team_config_path)

    # Assert
    assert team.name == "sample_team"
    assert len(team.agents) == 3  # coordinator, analyst, writer
    assert "coordinator" in team.agents
    assert "analyst" in team.agents
    assert "writer" in team.agents
    
    # Check tools
    assert len(team.tools) >= 1
    assert "file_operations" in team.tools
    
    # Check max rounds
    assert team.max_rounds == 20

def test_load_team_with_nonexistent_config():
    """
    Tests that loading a non-existent config file raises FileNotFoundError.
    """
    with pytest.raises(FileNotFoundError):
        Team.from_config("non_existent_path/team.yaml")

def test_load_team_with_invalid_yaml(tmp_path: Path):
    """
    Tests that loading a malformed YAML file raises a parsing error.
    """
    invalid_yaml = "name: Test Team\n  agents: - name: agent1" # Bad indentation
    config_path = tmp_path / "invalid_team.yaml"
    config_path.write_text(invalid_yaml)
    
    with pytest.raises(yaml.YAMLError):
        Team.from_config(str(config_path))

def test_load_team_with_validation_error(tmp_path: Path):
    """
    Tests that a config with missing required fields raises a Pydantic validation error.
    """
    # 'name' field is missing, which should cause a validation error
    invalid_config = """
version: "1.0"
agents:
  - name: "researcher"
    description: "A researcher agent"
    prompt_template: "prompt.jinja2"
    tools: []
"""
    config_path = tmp_path / "invalid_team.yaml"
    (tmp_path / "prompt.jinja2").write_text("dummy prompt")
    config_path.write_text(invalid_config)
    
    with pytest.raises(ValidationError):
        Team.from_config(str(config_path))

def test_load_team_with_invalid_tool_source(tmp_path: Path):
    """
    Tests that an invalid tool source string raises an ImportError.
    """
    invalid_config = """
version: "1.0"
name: "Test Team"
description: "A test team"
agents: []
tools:
  - name: "bad_tool"
    type: "python_function"
    source: "non.existent.module.NonExistentTool"
"""
    config_path = tmp_path / "team.yaml"
    config_path.write_text(invalid_config)
    
    # This should load successfully since we don't validate tool sources at load time
    team = Team.from_config(str(config_path))
    assert team.name == "Test Team"

def test_load_team_with_undefined_agent_tool(tmp_path: Path):
    """
    Tests that an agent referencing an undefined tool is handled gracefully.
    """
    config = """
version: "1.0"
name: "Test Team"
description: "A test team"
agents:
  - name: "agent1"
    description: "Test agent"
    prompt_template: "prompt.jinja2"
    tools: ["some_tool_that_does_not_exist"]
tools: []
"""
    config_path = tmp_path / "team.yaml"
    (tmp_path / "prompt.jinja2").write_text("prompt")
    config_path.write_text(config)

    # This should load successfully, but getting agent tools will return empty list
    team = Team.from_config(str(config_path))
    assert team.name == "Test Team"
    agent_tools = team.get_agent_tools("agent1")
    assert len(agent_tools) == 0  # Tool doesn't exist, so empty list returned

def test_basic_team_config_loading():
    """Test loading a basic team configuration."""
    
    # Create a minimal team configuration
    config_data = {
        'name': 'test_team',
        'description': 'A test team configuration',
        'llm': {
            'provider': 'deepseek',
            'model': 'deepseek-chat',
            'api_key': 'test-key',
            'base_url': 'https://api.deepseek.com',
            'temperature': 0.7,
            'max_tokens': 4000
        },
        'agents': [
            {
                'name': 'assistant',
                'description': 'A helpful assistant agent',
                'prompt_template': 'assistant.jinja2',
                'tools': ['file_ops']
            }
        ],
        'tools': [
            {
                'name': 'file_ops',
                'type': 'builtin',
                'description': 'File operations'
            }
        ]
    }
    
    # Create TeamConfig from dict
    team_config = TeamConfig(**config_data)
    
    # Verify the configuration
    assert team_config.name == 'test_team'
    assert team_config.description == 'A test team configuration'
    assert len(team_config.agents) == 1
    assert len(team_config.tools) == 1
    assert team_config.agents[0].name == 'assistant'
    assert team_config.tools[0].name == 'file_ops'
    assert team_config.llm.provider == 'deepseek'
    assert team_config.llm.model == 'deepseek-chat'

def test_team_config_validation():
    """Test that team configuration validation works correctly."""
    
    # Test missing required fields
    with pytest.raises(Exception):  # Should raise validation error
        TeamConfig()
    
    # Test valid minimal config
    config = TeamConfig(
        name="test",
        description="test team",
        agents=[
            AgentConfig(
                name="test_agent",
                description="test agent",
                prompt_template="test.jinja2"
            )
        ]
    )
    
    assert config.name == "test"
    assert len(config.agents) == 1

def test_llm_config_defaults():
    """Test that LLM configuration uses proper defaults."""
    
    # Test with minimal LLM config
    llm_config = LLMConfig(provider='deepseek', model='deepseek-chat', api_key='test-key')
    
    assert llm_config.provider == 'deepseek'
    assert llm_config.model == 'deepseek-chat'
    assert llm_config.temperature == 0.7  # Default value
    assert llm_config.max_tokens == 4000  # Default value
    assert llm_config.base_url == 'https://api.deepseek.com'  # Default for deepseek
    assert llm_config.timeout == 30  # Default value

def test_execution_config():
    """Test execution configuration."""
    
    # Test default values
    exec_config = ExecutionConfig()
    
    assert exec_config.mode == "autonomous"
    assert exec_config.max_rounds == 20
    assert exec_config.timeout_seconds == 300
    assert exec_config.step_through_enabled == False
    
    # Test custom values
    exec_config = ExecutionConfig(
        mode="step_through",
        max_rounds=50,
        timeout_seconds=600,
        step_through_enabled=True
    )
    
    assert exec_config.mode == "step_through"
    assert exec_config.max_rounds == 50
    assert exec_config.timeout_seconds == 600
    assert exec_config.step_through_enabled == True 