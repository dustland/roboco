import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from roboco.core.team import Team
from roboco.core.orchestrator import Orchestrator
from roboco.core.tool import ToolResult

# This assumes tests are run from the project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
SIMPLE_TEAM_CONFIG_PATH = PROJECT_ROOT / "examples" / "simple-research-team" / "team.json"

@pytest.mark.integration
@patch('roboco.core.orchestrator.get_tool_registry')
@patch('litellm.completion')
def test_simple_research_task(mock_completion, mock_get_tool_registry):
    """
    Tests an end-to-end scenario where a simple research team is loaded
    and run to answer a basic question. This test mocks both the LLM and
    the tool execution to ensure reliability.
    """
    # 1. Setup workspace and a more intelligent mock tool registry
    temp_workspace = PROJECT_ROOT / "tests" / "test_workspaces"
    
    def mock_tool_executor(tool_name: str, **kwargs):
        if tool_name == "write_file":
            file_path = kwargs.get("file_path")
            content = kwargs.get("content")
            # The orchestrator creates a unique task folder, so we need to find it
            task_dir = next(temp_workspace.glob("task_*"), None)
            if task_dir:
                (task_dir / file_path).write_text(content)
                return ToolResult(success=True, result=f"Successfully wrote to {file_path}")
            return ToolResult(success=False, result="Could not find task workspace.")
        
        if tool_name == "web_search":
            return ToolResult(success=True, result="According to my sources, the capital of France is Paris.")
        
        # Default for any other tool
        return ToolResult(success=True, result="Tool executed successfully.")

    mock_registry = MagicMock()
    mock_registry.execute_tool_sync.side_effect = mock_tool_executor
    mock_get_tool_registry.return_value = mock_registry

    # 2. Mock the sequence of LLM responses
    response1 = MagicMock()
    response1.choices[0].message.content = None
    tool_call1 = MagicMock()
    tool_call1.id = "call_123"
    tool_call1.function.name = "web_search"
    tool_call1.function.arguments = '{"query": "capital of France"}'
    response1.choices[0].message.tool_calls = [tool_call1]

    response2 = MagicMock()
    response2.choices[0].message.content = "I have found the answer and will write it to the file."
    tool_call2 = MagicMock()
    tool_call2.id = "call_456"
    tool_call2.function.name = "write_file"
    tool_call2.function.arguments = '{"file_path": "answer.txt", "content": "The capital of France is Paris."}'
    response2.choices[0].message.tool_calls = [tool_call2]

    response3 = MagicMock()
    response3.choices[0].message.content = "I have successfully written the answer to answer.txt."
    response3.choices[0].message.tool_calls = None

    mock_completion.side_effect = [response1, response2, response3]

    # 3. Load the team from configuration
    assert SIMPLE_TEAM_CONFIG_PATH.exists()
    team = Team.from_config_file(str(SIMPLE_TEAM_CONFIG_PATH))
    team.max_rounds = 6
    
    # 4. Instantiate the orchestrator
    orchestrator = Orchestrator(team, workspace_dir=str(temp_workspace))

    # 5. Start the task and run the loop
    list(orchestrator.start("Initial prompt"))
    while not orchestrator.is_complete:
        list(orchestrator.step())

    # 6. Assert the outcome
    assert orchestrator.is_complete, "Orchestrator should have completed the task"
    
    task_dir = next(temp_workspace.glob("task_*"), None)
    assert task_dir is not None, "Task workspace directory not created"
    answer_file = task_dir / "answer.txt"
    
    assert answer_file.exists(), "The 'answer.txt' file was not created by the mocked tool."
    content = answer_file.read_text().lower()
    assert "paris" in content

    assert mock_completion.call_count == 3 