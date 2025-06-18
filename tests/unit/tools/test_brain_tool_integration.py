"""
Test Brain integration with tool schemas.

This test verifies that tool schemas are correctly passed from 
the framework to the Brain and then to the LLM.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from weather_tool import WeatherTool
from agentx.tool.registry import ToolRegistry
from agentx.tool.manager import ToolManager
from agentx.core.brain import Brain, BrainConfig
from agentx.core.agent import Agent, AgentConfig


class TestBrainToolIntegration:
    """Test that tool schemas flow correctly through the Brain."""
    
    @pytest.mark.asyncio
    async def test_brain_receives_complete_tool_schemas(self):
        """Test that Brain receives complete tool schemas with descriptions."""
        # Set up tool manager with weather tool
        tool_manager = ToolManager("test_task")
        weather_tool = WeatherTool()
        tool_manager.register_tool(weather_tool)
        
        # Get tool schemas
        tool_schemas = tool_manager.get_tool_schemas(['get_weather'])
        print(f"Tool schemas from manager: {tool_schemas}")
        
        # Verify the schema is complete
        assert len(tool_schemas) == 1
        schema = tool_schemas[0]
        assert 'function' in schema
        assert 'parameters' in schema['function']
        assert 'properties' in schema['function']['parameters']
        assert 'location' in schema['function']['parameters']['properties']
        
        location_param = schema['function']['parameters']['properties']['location']
        assert 'description' in location_param
        assert len(location_param['description']) > 0
        
        print(f"✅ Tool schema is complete with parameter descriptions")
    
    @pytest.mark.asyncio
    @patch('litellm.acompletion')
    async def test_brain_passes_schemas_to_litellm(self, mock_acompletion):
        """Test that Brain passes complete schemas to LiteLLM."""
        # Mock LiteLLM response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].delta = MagicMock()
        mock_response.choices[0].delta.content = "I'll check the weather for you."
        mock_response.choices[0].delta.tool_calls = None
        mock_response.choices[0].finish_reason = "stop"
        
        # Make it async iterable
        async def async_iter():
            yield mock_response
        
        mock_acompletion.return_value = async_iter()
        
        # Set up Brain
        brain_config = BrainConfig(
            model="deepseek/deepseek-chat",
            supports_function_calls=True
        )
        brain = Brain(brain_config)
        
        # Set up tool schemas
        tool_manager = ToolManager("test_task")
        weather_tool = WeatherTool()
        tool_manager.register_tool(weather_tool)
        tool_schemas = tool_manager.get_tool_schemas(['get_weather'])
        
        # Call Brain with tools
        messages = [{"role": "user", "content": "What's the weather in Shanghai?"}]
        
        # Use stream_response to capture the LiteLLM call
        response_chunks = []
        async for chunk in brain.stream_response(messages, tools=tool_schemas):
            response_chunks.append(chunk)
        
        # Verify LiteLLM was called with tools
        assert mock_acompletion.called
        call_args = mock_acompletion.call_args
        
        print(f"LiteLLM call args: {call_args}")
        
        # Check if tools were passed
        if 'tools' in call_args[1]:  # kwargs
            passed_tools = call_args[1]['tools']
            print(f"Tools passed to LiteLLM: {passed_tools}")
            
            # Verify the tools are complete
            assert len(passed_tools) == 1
            assert passed_tools[0]['function']['name'] == 'get_weather'
            assert 'parameters' in passed_tools[0]['function']
            assert 'properties' in passed_tools[0]['function']['parameters']
            
            location_param = passed_tools[0]['function']['parameters']['properties']['location']
            assert 'description' in location_param
            print(f"✅ Complete tool schema passed to LiteLLM: {location_param}")
        else:
            pytest.fail("Tools were not passed to LiteLLM!")
    
    @pytest.mark.asyncio
    async def test_agent_tool_schema_flow(self):
        """Test the complete Agent → Brain → Tool schema flow."""
        # Set up tool manager
        tool_manager = ToolManager("test_task")
        weather_tool = WeatherTool()
        tool_manager.register_tool(weather_tool)
        
        # Set up Agent
        agent_config = AgentConfig(
            name="test_agent",
            description="A test agent for tool schema testing",
            prompt_template="You are a helpful assistant.",
            tools=['get_weather'],
            brain_config=BrainConfig(
                model="deepseek/deepseek-chat",
                supports_function_calls=True
            )
        )
        
        agent = Agent(agent_config, tool_manager=tool_manager)
        
        # Get tool schemas from agent
        tool_schemas = agent.get_tools_json()
        print(f"Tool schemas from agent: {tool_schemas}")
        
        # Verify schemas are complete
        assert len(tool_schemas) == 1
        schema = tool_schemas[0]
        
        # Check complete structure
        assert schema['type'] == 'function'
        assert 'function' in schema
        assert 'name' in schema['function']
        assert 'description' in schema['function']
        assert 'parameters' in schema['function']
        
        # Check parameter details
        params = schema['function']['parameters']
        assert 'properties' in params
        assert 'location' in params['properties']
        
        location_param = params['properties']['location']
        assert 'description' in location_param
        assert location_param['type'] == 'string'
        
        print(f"✅ Agent provides complete tool schemas: {location_param}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"]) 