"""
Unit tests for Agent component.

Tests agent initialization, configuration, and coordination functionality.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from roboco.core.agent import Agent, AgentConfig, AgentRole, create_assistant_agent, create_user_agent, create_code_agent
from roboco.core.brain import BrainConfig, Message
from roboco.core.tool import Tool


class TestAgent:
    """Test Agent class."""
    
    def test_agent_initialization_basic(self):
        """Test basic agent initialization."""
        agent = Agent(
            name="TestAgent",
            role="Test Role",
            system_message="You are a test agent."
        )
        
        assert agent.name == "TestAgent"
        assert agent.role == "Test Role"
        assert agent.system_message == "You are a test agent."
        assert agent.brain is not None
        assert agent.tools is not None
        assert agent.memory is not None
        assert agent.event_bus is not None
    
    def test_agent_initialization_with_config(self):
        """Test agent initialization with custom brain config."""
        brain_config = BrainConfig(
            model="gpt-4",
            temperature=0.5,
            max_tokens=2000
        )
        
        agent = Agent(
            name="ConfigAgent",
            role="Configured Agent",
            system_message="Custom system message",
            brain_config=brain_config
        )
        
        assert agent.brain.config.model == "gpt-4"
        assert agent.brain.config.temperature == 0.5
        assert agent.brain.config.max_tokens == 2000
    
    def test_agent_initialization_with_tools(self):
        """Test agent initialization with custom tools."""
        tool_registry = ToolRegistry()
        
        @tool_registry.register("test_tool")
        def test_tool(input_text: str) -> str:
            return f"Processed: {input_text}"
        
        agent = Agent(
            name="ToolAgent",
            role="Tool User",
            system_message="I use tools",
            tools=tool_registry
        )
        
        assert "test_tool" in agent.tools.list_tools()
    
    @pytest.mark.asyncio
    async def test_agent_process_message(self):
        """Test agent message processing."""
        with patch('roboco.core.brain.openai.AsyncOpenAI') as mock_openai_class:
            # Setup mock LLM response
            mock_client = AsyncMock()
            mock_openai_class.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Hello! I'm ready to help."
            mock_response.usage = {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25}
            
            mock_client.chat.completions.create.return_value = mock_response
            
            agent = Agent(
                name="ProcessAgent",
                role="Message Processor",
                system_message="Process messages efficiently"
            )
            
            input_message = Message(
                content="Hello, agent!",
                sender="User",
                recipient="ProcessAgent",
                role="user"
            )
            
            response = await agent.process_message(input_message)
            
            assert isinstance(response, Message)
            assert response.content == "Hello! I'm ready to help."
            assert response.sender == "ProcessAgent"
            assert response.role == "assistant"
    
    @pytest.mark.asyncio
    async def test_agent_process_message_with_context(self):
        """Test agent message processing with context."""
        with patch('roboco.core.brain.openai.AsyncOpenAI') as mock_openai_class:
            mock_client = AsyncMock()
            mock_openai_class.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "I understand the context."
            mock_response.usage = {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30}
            
            mock_client.chat.completions.create.return_value = mock_response
            
            agent = Agent(
                name="ContextAgent",
                role="Context Processor",
                system_message="Use context effectively"
            )
            
            input_message = Message(
                content="Continue our conversation",
                sender="User",
                recipient="ContextAgent",
                role="user"
            )
            
            context = {"previous_topic": "AI development"}
            
            response = await agent.process_message(input_message, context=context)
            
            assert isinstance(response, Message)
            assert response.content == "I understand the context."
    
    @pytest.mark.asyncio
    async def test_agent_error_handling(self):
        """Test agent error handling during message processing."""
        with patch('roboco.core.brain.openai.AsyncOpenAI') as mock_openai_class:
            mock_client = AsyncMock()
            mock_openai_class.return_value = mock_client
            
            # Simulate processing error
            mock_client.chat.completions.create.side_effect = Exception("Processing failed")
            
            agent = Agent(
                name="ErrorAgent",
                role="Error Handler",
                system_message="Handle errors gracefully"
            )
            
            input_message = Message(
                content="This will cause an error",
                sender="User",
                recipient="ErrorAgent",
                role="user"
            )
            
            response = await agent.process_message(input_message)
            
            # Should return error message
            assert isinstance(response, Message)
            assert "error" in response.content.lower() or "thinking error" in response.content.lower()
    
    def test_agent_tool_integration(self):
        """Test agent integration with tools."""
        tool_registry = ToolRegistry()
        
        @tool_registry.register("calculator")
        def calculator(expression: str) -> str:
            """Simple calculator tool."""
            try:
                result = eval(expression)  # Note: eval is unsafe, just for testing
                return str(result)
            except:
                return "Error in calculation"
        
        agent = Agent(
            name="CalculatorAgent",
            role="Calculator",
            system_message="I can do math",
            tools=tool_registry
        )
        
        # Test tool availability
        available_tools = agent.tools.list_tools()
        assert "calculator" in available_tools
        
        # Test tool execution
        result = agent.tools.execute_tool("calculator", expression="2 + 2")
        assert result == "4"
    
    def test_agent_memory_integration(self):
        """Test agent integration with memory."""
        agent = Agent(
            name="MemoryAgent",
            role="Memory User",
            system_message="I remember things"
        )
        
        # Test memory availability
        assert agent.memory is not None
        
        # Memory operations are tested in memory-specific tests
        # Here we just verify the integration exists
    
    def test_agent_event_integration(self):
        """Test agent integration with event system."""
        agent = Agent(
            name="EventAgent",
            role="Event Handler",
            system_message="I handle events"
        )
        
        # Test event bus availability
        assert agent.event_bus is not None
        
        # Event operations are tested in event-specific tests
        # Here we just verify the integration exists
    
    def test_agent_string_representation(self):
        """Test agent string representations."""
        agent = Agent(
            name="StringAgent",
            role="String Tester",
            system_message="Test string methods"
        )
        
        assert str(agent) == "Agent(StringAgent)"
        assert "StringAgent" in repr(agent)
        assert "String Tester" in repr(agent)
    
    def test_agent_equality(self):
        """Test agent equality comparison."""
        agent1 = Agent(
            name="Agent1",
            role="Role1",
            system_message="Message1"
        )
        
        agent2 = Agent(
            name="Agent1",  # Same name
            role="Role2",   # Different role
            system_message="Message2"  # Different message
        )
        
        agent3 = Agent(
            name="Agent3",  # Different name
            role="Role1",
            system_message="Message1"
        )
        
        # Agents with same name should be equal
        assert agent1 == agent2
        
        # Agents with different names should not be equal
        assert agent1 != agent3
    
    @pytest.mark.asyncio
    async def test_agent_concurrent_processing(self):
        """Test agent handling concurrent message processing."""
        with patch('roboco.core.brain.openai.AsyncOpenAI') as mock_openai_class:
            mock_client = AsyncMock()
            mock_openai_class.return_value = mock_client
            
            # Mock responses for concurrent calls
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Concurrent response"
            mock_response.usage = {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20}
            
            mock_client.chat.completions.create.return_value = mock_response
            
            agent = Agent(
                name="ConcurrentAgent",
                role="Concurrent Processor",
                system_message="Handle multiple requests"
            )
            
            # Create multiple messages
            messages = [
                Message(content=f"Message {i}", sender="User", role="user")
                for i in range(3)
            ]
            
            # Process concurrently
            tasks = [agent.process_message(msg) for msg in messages]
            responses = await asyncio.gather(*tasks)
            
            # Verify all responses
            assert len(responses) == 3
            for response in responses:
                assert isinstance(response, Message)
                assert response.content == "Concurrent response"
                assert response.sender == "ConcurrentAgent"


class TestAgentConfiguration:
    """Test agent configuration and customization."""
    
    def test_agent_with_custom_brain_config(self):
        """Test agent with custom brain configuration."""
        custom_config = BrainConfig(
            model="custom-model",
            temperature=0.9,
            max_tokens=500,
            enable_reasoning_traces=False
        )
        
        agent = Agent(
            name="CustomAgent",
            role="Custom",
            system_message="Custom agent",
            brain_config=custom_config
        )
        
        assert agent.brain.config.model == "custom-model"
        assert agent.brain.config.temperature == 0.9
        assert agent.brain.config.max_tokens == 500
        assert agent.brain.config.enable_reasoning_traces is False
    
    def test_agent_with_no_system_message(self):
        """Test agent creation without system message."""
        agent = Agent(
            name="NoSystemAgent",
            role="No System"
        )
        
        assert agent.name == "NoSystemAgent"
        assert agent.role == "No System"
        assert agent.system_message is None
    
    def test_agent_with_empty_system_message(self):
        """Test agent creation with empty system message."""
        agent = Agent(
            name="EmptySystemAgent",
            role="Empty System",
            system_message=""
        )
        
        assert agent.system_message == ""
