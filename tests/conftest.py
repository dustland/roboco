"""
Pytest configuration and shared fixtures for AgentX tests.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock

# from agentx.core.brain import BrainConfig, Message, ChatHistory


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


# @pytest.fixture
# def mock_brain_config():
#     """Mock brain configuration for testing."""
#     return BrainConfig(
#         model="gpt-3.5-turbo",
#         api_key="test-key",
#         base_url=None,
#         temperature=0.7,
#         max_tokens=1000,
#         timeout=30
#     )


# @pytest.fixture
# def sample_messages():
#     """Create sample messages for testing."""
#     return [
#         Message(
#             content="Hello, how are you?",
#             sender="User",
#             recipient="TestAgent",
#             role="user"
#         ),
#         Message(
#             content="I'm doing well, thank you!",
#             sender="TestAgent",
#             recipient="User",
#             role="assistant"
#         )
#     ]


# @pytest.fixture
# def chat_history():
#     """Create a test chat history."""
#     history = ChatHistory(task_id="test-task-123")
#     history.add_message(Message(
#         content="Test message 1",
#         sender="User",
#         role="user"
#     ))
#     return history


@pytest.fixture
def mock_agent():
    """Mock agent for testing."""
    from unittest.mock import Mock
    agent = Mock()
    agent.name = "test_agent"
    agent.role = Mock()
    agent.role.value = "assistant"
    agent.is_assistant_agent = True
    agent.is_user_agent = False
    agent.is_system_agent = False
    return agent


@pytest.fixture
def mock_agents():
    """Mock agents list for testing."""
    from unittest.mock import Mock
    agent1 = Mock()
    agent1.name = "agent1"
    agent1.is_assistant_agent = True
    agent1.is_user_agent = False
    agent1.is_system_agent = False
    
    agent2 = Mock()
    agent2.name = "agent2"
    agent2.is_assistant_agent = True
    agent2.is_user_agent = False
    agent2.is_system_agent = False
    
    return [agent1, agent2]


@pytest.fixture
def mock_agent_config():
    """Mock agent config for testing."""
    from agentx.core.agent import AgentConfig, AgentRole
    return AgentConfig(name="test_agent", role=AgentRole.ASSISTANT) 