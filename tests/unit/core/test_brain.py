"""
Unit tests for Brain component.

Tests the core thinking and reasoning functionality of agents.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from roboco.core.brain import Brain, BrainConfig, Message, ChatHistory
from roboco.core import Agent


class TestBrainConfig:
    """Test BrainConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = BrainConfig()
        assert config.model == "deepseek-chat"
        assert config.base_url == "https://api.deepseek.com"
        assert config.temperature == 0.7
        assert config.max_tokens is None
        assert config.timeout == 30
        assert config.enable_reasoning_traces is True
        assert config.enable_memory_integration is True
        assert config.enable_tool_calling is True
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = BrainConfig(
            model="gpt-4",
            temperature=0.5,
            max_tokens=2000,
            enable_reasoning_traces=False
        )
        assert config.model == "gpt-4"
        assert config.temperature == 0.5
        assert config.max_tokens == 2000
        assert config.enable_reasoning_traces is False


class TestMessage:
    """Test Message dataclass."""
    
    def test_message_creation(self):
        """Test basic message creation."""
        msg = Message(
            content="Hello world",
            sender="TestAgent",
            recipient="User",
            role="assistant"
        )
        assert msg.content == "Hello world"
        assert msg.sender == "TestAgent"
        assert msg.recipient == "User"
        assert msg.role == "assistant"
        assert isinstance(msg.timestamp, datetime)
        assert msg.message_id.startswith("msg_")
    
    def test_message_to_openai_format(self):
        """Test conversion to OpenAI format."""
        msg = Message(
            content="Test message",
            sender="Agent",
            role="assistant"
        )
        openai_format = msg.to_openai_format()
        expected = {
            "role": "assistant",
            "content": "Test message"
        }
        assert openai_format == expected
    
    def test_message_with_function_call(self):
        """Test message with function call."""
        function_call = {"name": "test_function", "arguments": '{"param": "value"}'}
        msg = Message(
            content="",
            sender="Agent",
            role="assistant",
            function_call=function_call
        )
        openai_format = msg.to_openai_format()
        assert openai_format["function_call"] == function_call
    
    def test_message_serialization(self):
        """Test message to/from dict conversion."""
        original = Message(
            content="Test content",
            sender="TestSender",
            recipient="TestRecipient",
            role="user",
            metadata={"key": "value"}
        )
        
        # Convert to dict and back
        msg_dict = original.to_dict()
        restored = Message.from_dict(msg_dict)
        
        assert restored.content == original.content
        assert restored.sender == original.sender
        assert restored.recipient == original.recipient
        assert restored.role == original.role
        assert restored.metadata == original.metadata


class TestChatHistory:
    """Test ChatHistory class."""
    
    def test_chat_history_creation(self):
        """Test chat history creation."""
        history = ChatHistory(task_id="test-123")
        assert history.task_id == "test-123"
        assert len(history.messages) == 0
        assert isinstance(history.created_at, datetime)
    
    def test_add_message(self):
        """Test adding messages to history."""
        history = ChatHistory()
        msg = Message(content="Test", sender="User", role="user")
        
        history.add_message(msg)
        assert len(history.messages) == 1
        assert history.messages[0] == msg
    
    def test_get_messages_with_limit(self):
        """Test getting messages with limit."""
        history = ChatHistory()
        
        # Add multiple messages
        for i in range(5):
            msg = Message(content=f"Message {i}", sender="User", role="user")
            history.add_message(msg)
        
        # Test limit
        recent_messages = history.get_messages(limit=3)
        assert len(recent_messages) == 3
        assert recent_messages[0].content == "Message 2"  # Last 3 messages
        assert recent_messages[-1].content == "Message 4"
    
    def test_clear_history(self):
        """Test clearing chat history."""
        history = ChatHistory()
        history.add_message(Message(content="Test", sender="User", role="user"))
        
        assert len(history) == 1
        history.clear_history()
        assert len(history) == 0


class TestBrain:
    """Test Brain class."""
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing."""
        agent = MagicMock()
        agent.name = "TestAgent"
        agent.system_message = "You are a test agent."
        return agent
    
    @pytest.fixture
    def brain_config(self):
        """Create test brain configuration."""
        return BrainConfig(
            model="gpt-3.5-turbo",
            api_key="test-key",
            temperature=0.5
        )
    
    def test_brain_initialization(self, mock_agent, brain_config):
        """Test brain initialization."""
        with patch('roboco.core.brain.openai.AsyncOpenAI') as mock_openai:
            brain = Brain(mock_agent, brain_config)
            
            assert brain.agent == mock_agent
            assert brain.config == brain_config
            assert len(brain._thinking_history) == 0
            assert len(brain._reasoning_context) == 0
            mock_openai.assert_called_once()
    
    def test_brain_initialization_with_deepseek(self, mock_agent):
        """Test brain initialization with DeepSeek configuration."""
        config = BrainConfig(
            model="deepseek-chat",
            base_url="https://api.deepseek.com",
            api_key="test-key"
        )
        
        with patch('roboco.core.brain.openai.AsyncOpenAI') as mock_openai:
            brain = Brain(mock_agent, config)
            
            mock_openai.assert_called_once_with(
                api_key="test-key",
                base_url="https://api.deepseek.com"
            )
    
    @pytest.mark.asyncio
    async def test_brain_think_success(self, mock_agent, brain_config):
        """Test successful brain thinking process."""
        with patch('roboco.core.brain.openai.AsyncOpenAI') as mock_openai_class:
            # Setup mock LLM response
            mock_client = AsyncMock()
            mock_openai_class.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "This is a test response"
            mock_response.usage = {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25}
            
            mock_client.chat.completions.create.return_value = mock_response
            
            # Create brain and test thinking
            brain = Brain(mock_agent, brain_config)
            
            messages = [
                Message(content="Hello", sender="User", role="user")
            ]
            
            result = await brain.think(messages)
            
            # Verify result
            assert isinstance(result, Message)
            assert result.content == "This is a test response"
            assert result.sender == "TestAgent"
            assert result.role == "assistant"
            assert result.metadata["brain_generated"] is True
            
            # Verify LLM was called correctly
            mock_client.chat.completions.create.assert_called_once()
            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]["model"] == "gpt-3.5-turbo"
            assert call_args[1]["temperature"] == 0.5
            
            # Verify thinking history was recorded
            assert len(brain._thinking_history) == 1
            thinking_step = brain._thinking_history[0]
            assert thinking_step["agent"] == "TestAgent"
            assert thinking_step["input_messages"] == 1
            assert thinking_step["response_generated"] is True
    
    @pytest.mark.asyncio
    async def test_brain_think_with_system_message(self, mock_agent, brain_config):
        """Test brain thinking with system message."""
        with patch('roboco.core.brain.openai.AsyncOpenAI') as mock_openai_class:
            mock_client = AsyncMock()
            mock_openai_class.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Response with system message"
            mock_response.usage = {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30}
            
            mock_client.chat.completions.create.return_value = mock_response
            
            brain = Brain(mock_agent, brain_config)
            
            messages = [
                Message(content="Test message", sender="User", role="user")
            ]
            
            await brain.think(messages)
            
            # Verify system message was included
            call_args = mock_client.chat.completions.create.call_args
            llm_messages = call_args[1]["messages"]
            
            assert len(llm_messages) == 2  # system + user message
            assert llm_messages[0]["role"] == "system"
            assert llm_messages[0]["content"] == "You are a test agent."
            assert llm_messages[1]["role"] == "user"
            assert llm_messages[1]["content"] == "Test message"
    
    @pytest.mark.asyncio
    async def test_brain_think_error_handling(self, mock_agent, brain_config):
        """Test brain error handling during thinking."""
        with patch('roboco.core.brain.openai.AsyncOpenAI') as mock_openai_class:
            mock_client = AsyncMock()
            mock_openai_class.return_value = mock_client
            
            # Simulate API error
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            
            brain = Brain(mock_agent, brain_config)
            
            messages = [
                Message(content="Test", sender="User", role="user")
            ]
            
            result = await brain.think(messages)
            
            # Verify error response
            assert isinstance(result, Message)
            assert "Thinking error" in result.content
            assert result.metadata["error"] is True
            assert result.metadata["error_message"] == "API Error"
    
    @pytest.mark.asyncio
    async def test_reason_with_tools(self, mock_agent, brain_config):
        """Test reasoning with tools."""
        with patch('roboco.core.brain.openai.AsyncOpenAI'):
            brain = Brain(mock_agent, brain_config)
            
            messages = [
                Message(content="Please search for information", sender="User", role="user")
            ]
            
            available_tools = {"search": MagicMock()}
            
            results = await brain.reason_with_tools(messages, available_tools)
            
            # Should return tool reasoning response
            assert len(results) == 1
            assert "would use search tools" in results[0].content
            assert results[0].metadata["tool_reasoning"] is True
    
    @pytest.mark.asyncio
    async def test_integrate_memory(self, mock_agent, brain_config):
        """Test memory integration."""
        with patch('roboco.core.brain.openai.AsyncOpenAI'):
            brain = Brain(mock_agent, brain_config)
            
            messages = [
                Message(content="Remember this", sender="User", role="user")
            ]
            
            memory_context = {"key": "value"}
            
            result = await brain.integrate_memory(messages, memory_context)
            
            assert result["memory_integrated"] is True
            assert result["context_enhanced"] is True
            assert isinstance(result["relevant_memories"], list)
    
    def test_thinking_history_management(self, mock_agent, brain_config):
        """Test thinking history management."""
        with patch('roboco.core.brain.openai.AsyncOpenAI'):
            brain = Brain(mock_agent, brain_config)
            
            # Add some thinking history
            brain._thinking_history.append({"test": "data"})
            brain._reasoning_context["key"] = "value"
            
            # Test getting history
            history = brain.get_thinking_history()
            assert len(history) == 1
            assert history[0]["test"] == "data"
            
            # Test clearing history
            brain.clear_thinking_history()
            assert len(brain._thinking_history) == 0
            assert len(brain._reasoning_context) == 0
    
    def test_brain_string_representation(self, mock_agent, brain_config):
        """Test brain string representations."""
        with patch('roboco.core.brain.openai.AsyncOpenAI'):
            brain = Brain(mock_agent, brain_config)
            
            assert str(brain) == "Brain(TestAgent)"
            assert repr(brain) == "Brain(agent=TestAgent, model=gpt-3.5-turbo)"


# Utility function tests
class TestUtilityFunctions:
    """Test utility functions for message creation."""
    
    def test_create_system_message(self):
        """Test system message creation utility."""
        from roboco.core.brain import create_system_message
        
        msg = create_system_message("System prompt", "Agent")
        assert msg.content == "System prompt"
        assert msg.sender == "System"
        assert msg.recipient == "Agent"
        assert msg.role == "system"
    
    def test_create_user_message(self):
        """Test user message creation utility."""
        from roboco.core.brain import create_user_message
        
        msg = create_user_message("User input", "User", "Agent")
        assert msg.content == "User input"
        assert msg.sender == "User"
        assert msg.recipient == "Agent"
        assert msg.role == "user"
    
    def test_create_assistant_message(self):
        """Test assistant message creation utility."""
        from roboco.core.brain import create_assistant_message
        
        msg = create_assistant_message("Assistant response", "Agent", "User")
        assert msg.content == "Assistant response"
        assert msg.sender == "Agent"
        assert msg.recipient == "User"
        assert msg.role == "assistant" 