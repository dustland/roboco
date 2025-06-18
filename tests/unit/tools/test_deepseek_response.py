"""
Test to capture actual DeepSeek responses and analyze the tool call arguments.

This test will make real calls to DeepSeek to see what arguments it's actually returning.
"""

import pytest
import asyncio
import json

from weather_tool import WeatherTool
from agentx.tool.manager import ToolManager
from agentx.core.brain import Brain, BrainConfig


class TestDeepSeekResponse:
    """Test actual DeepSeek responses to understand the empty arguments issue."""
    
    @pytest.mark.asyncio
    async def test_deepseek_streaming_response(self):
        """Test DeepSeek's actual streaming response with tool calling."""
        # Set up tool manager with weather tool
        tool_manager = ToolManager("test_task")
        weather_tool = WeatherTool()
        tool_manager.register_tool(weather_tool)
        tool_schemas = tool_manager.get_tool_schemas(['get_weather'])
        
        print(f"Sending schema to DeepSeek: {json.dumps(tool_schemas[0], indent=2)}")
        
        # Set up Brain with DeepSeek
        brain_config = BrainConfig(
            model="deepseek/deepseek-chat",
            supports_function_calls=True
        )
        brain = Brain(brain_config)
        
        # Test message
        messages = [{"role": "user", "content": "What's the weather in Shanghai tomorrow?"}]
        
        print("\n🔍 Making streaming call to DeepSeek...")
        
        # Capture all streaming chunks
        chunks = []
        tool_calls_found = []
        
        async for chunk in brain.stream_response(messages, tools=tool_schemas):
            chunks.append(chunk)
            print(f"Chunk: {chunk}")
            
            if chunk.get('type') == 'tool-call':
                tool_calls_found.append(chunk.get('tool_call'))
                print(f"🔧 Found tool call: {chunk.get('tool_call')}")
        
        print(f"\n📊 Summary:")
        print(f"Total chunks: {len(chunks)}")
        print(f"Tool calls found: {len(tool_calls_found)}")
        
        if tool_calls_found:
            for i, tc in enumerate(tool_calls_found):
                print(f"Tool call {i+1}:")
                print(f"  ID: {tc.get('id')}")
                print(f"  Function name: {tc.get('function', {}).get('name')}")
                print(f"  Arguments: '{tc.get('function', {}).get('arguments')}'")
                
                # Try to parse arguments
                args_str = tc.get('function', {}).get('arguments', '')
                if args_str:
                    try:
                        parsed_args = json.loads(args_str)
                        print(f"  Parsed arguments: {parsed_args}")
                    except Exception as e:
                        print(f"  Failed to parse arguments: {e}")
                else:
                    print(f"  ❌ EMPTY ARGUMENTS!")
        else:
            print("❌ No tool calls found in streaming response")
    
    @pytest.mark.asyncio
    async def test_deepseek_non_streaming_response(self):
        """Test DeepSeek's non-streaming response for comparison."""
        # Set up tool manager with weather tool
        tool_manager = ToolManager("test_task")
        weather_tool = WeatherTool()
        tool_manager.register_tool(weather_tool)
        tool_schemas = tool_manager.get_tool_schemas(['get_weather'])
        
        # Set up Brain with DeepSeek
        brain_config = BrainConfig(
            model="deepseek/deepseek-chat",
            supports_function_calls=True
        )
        brain = Brain(brain_config)
        
        # Test message
        messages = [{"role": "user", "content": "What's the weather in Shanghai tomorrow?"}]
        
        print("\n🔍 Making non-streaming call to DeepSeek...")
        
        # Make non-streaming call
        response = await brain.generate_response(messages, tools=tool_schemas)
        
        print(f"Response content: {response.content}")
        print(f"Tool calls: {response.tool_calls}")
        
        if response.tool_calls:
            for i, tc in enumerate(response.tool_calls):
                print(f"Tool call {i+1}:")
                print(f"  ID: {tc.id}")
                print(f"  Function name: {tc.function.name}")
                print(f"  Arguments: '{tc.function.arguments}'")
                
                # Try to parse arguments
                if tc.function.arguments:
                    try:
                        parsed_args = json.loads(tc.function.arguments)
                        print(f"  Parsed arguments: {parsed_args}")
                    except Exception as e:
                        print(f"  Failed to parse arguments: {e}")
                else:
                    print(f"  ❌ EMPTY ARGUMENTS!")
        else:
            print("❌ No tool calls found in non-streaming response")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"]) 