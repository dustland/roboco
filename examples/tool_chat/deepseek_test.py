"""
Direct test of DeepSeek's function calling capabilities.

This script tests DeepSeek's function calling without the AgentX framework
to isolate whether issues are with the model or our implementation.
Tests both streaming and non-streaming modes to identify differences.
"""

import asyncio
import json
import litellm
from typing import Dict, Any, List


def get_weather_schema() -> Dict[str, Any]:
    """Get the OpenAI function calling schema for weather tool."""
    return {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather forecast for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city name"
                    }
                },
                "required": ["location"]
            }
        }
    }


def mock_get_weather(location: str) -> str:
    """Mock weather function for testing."""
    return f"Weather forecast for {location}: Tomorrow will be sunny with a high of 25°C and low of 18°C. Light breeze from the east."


async def test_deepseek_non_streaming():
    """Test DeepSeek function calling in non-streaming mode."""
    print("\n🔍 Testing DeepSeek Non-Streaming Function Calling")
    print("=" * 50)
    
    model = "deepseek/deepseek-chat"
    supports_fc = litellm.supports_function_calling(model=model)
    print(f"Function calling support: {supports_fc}")
    
    messages = [{"role": "user", "content": "What is the weather in Shanghai tomorrow?"}]
    tools = [get_weather_schema()]
    
    print(f"Sending schema: {json.dumps(tools[0], indent=2)}")
    
    try:
        response = await litellm.acompletion(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            stream=False  # Explicitly non-streaming
        )
        
        message = response.choices[0].message
        print(f"Response content: '{message.content}'")
        
        if hasattr(message, 'tool_calls') and message.tool_calls:
            print(f"✅ Tool calls found: {len(message.tool_calls)}")
            for i, tc in enumerate(message.tool_calls):
                print(f"  Tool call {i+1}:")
                print(f"    Function: {tc.function.name}")
                print(f"    Arguments: '{tc.function.arguments}'")
                try:
                    if tc.function.arguments:
                        args = json.loads(tc.function.arguments)
                        print(f"    ✅ Parsed successfully: {args}")
                        return True
                    else:
                        print("    ❌ Empty arguments!")
                        return False
                except Exception as e:
                    print(f"    ❌ Parse error: {e}")
                    return False
        else:
            print("❌ No tool calls detected")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_deepseek_streaming():
    """Test DeepSeek function calling in streaming mode."""
    print("\n🔍 Testing DeepSeek Streaming Function Calling")
    print("=" * 50)
    
    model = "deepseek/deepseek-chat"
    messages = [{"role": "user", "content": "What is the weather in Shanghai tomorrow?"}]
    tools = [get_weather_schema()]
    
    print(f"Sending schema: {json.dumps(tools[0], indent=2)}")
    
    try:
        response = await litellm.acompletion(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            stream=True  # Streaming mode
        )
        
        # Collect streaming chunks
        tool_calls = {}
        chunks_received = 0
        
        async for chunk in response:
            chunks_received += 1
            print(f"Chunk {chunks_received}: {chunk}")
            
            if chunk.choices and len(chunk.choices) > 0:
                choice = chunk.choices[0]
                delta = choice.delta
                
                # Look for tool calls in the delta
                if hasattr(delta, 'tool_calls') and delta.tool_calls:
                    for tool_call_delta in delta.tool_calls:
                        tool_call_id = getattr(tool_call_delta, 'id', None)
                        
                        if tool_call_id:
                            # Initialize new tool call with ID
                            if tool_call_id not in tool_calls:
                                tool_calls[tool_call_id] = {
                                    'id': tool_call_id,
                                    'type': getattr(tool_call_delta, 'type', 'function'),
                                    'function': {
                                        'name': '',
                                        'arguments': ''
                                    }
                                }
                            
                            # Accumulate function data for this specific tool call
                            if hasattr(tool_call_delta, 'function'):
                                func = tool_call_delta.function
                                if hasattr(func, 'name') and func.name:
                                    tool_calls[tool_call_id]['function']['name'] = func.name
                                if hasattr(func, 'arguments') and func.arguments is not None:
                                    tool_calls[tool_call_id]['function']['arguments'] += func.arguments
                        
                        elif hasattr(tool_call_delta, 'function') and tool_calls:
                            # Handle chunks without ID - accumulate to the most recent tool call
                            # This handles DeepSeek's pattern where first chunk has ID, subsequent chunks don't
                            most_recent_id = list(tool_calls.keys())[-1]
                            func = tool_call_delta.function
                            
                            if hasattr(func, 'name') and func.name:
                                tool_calls[most_recent_id]['function']['name'] = func.name
                            if hasattr(func, 'arguments') and func.arguments is not None:
                                tool_calls[most_recent_id]['function']['arguments'] += func.arguments
        
        print(f"\n📊 Streaming Summary:")
        print(f"Total chunks received: {chunks_received}")
        print(f"Tool calls accumulated: {len(tool_calls)}")
        
        if tool_calls:
            success = True
            for tool_call_id, tc in tool_calls.items():
                print(f"  Tool call {tool_call_id}:")
                print(f"    Function: {tc['function']['name']}")
                print(f"    Arguments: '{tc['function']['arguments']}'")
                
                try:
                    if tc['function']['arguments']:
                        args = json.loads(tc['function']['arguments'])
                        print(f"    ✅ Parsed successfully: {args}")
                    else:
                        print("    ❌ Empty arguments!")
                        success = False
                except Exception as e:
                    print(f"    ❌ Parse error: {e}")
                    success = False
            
            return success
        else:
            print("❌ No tool calls found in streaming response")
            return False
            
    except Exception as e:
        print(f"❌ Streaming error: {e}")
        return False


async def main():
    """Main function to run both streaming and non-streaming tests."""
    print("🧪 DeepSeek Function Calling Comparison Test")
    print("=" * 60)
    
    # Test non-streaming mode
    non_streaming_success = await test_deepseek_non_streaming()
    
    # Test streaming mode  
    streaming_success = await test_deepseek_streaming()
    
    # Summary
    print("\n🎯 Test Results Summary")
    print("=" * 30)
    print(f"Non-streaming mode: {'✅ SUCCESS' if non_streaming_success else '❌ FAILED'}")
    print(f"Streaming mode:     {'✅ SUCCESS' if streaming_success else '❌ FAILED'}")
    
    if non_streaming_success and not streaming_success:
        print("\n🚨 CONFIRMED: DeepSeek streaming function calling bug!")
        print("   - Non-streaming mode works correctly")
        print("   - Streaming mode returns empty arguments")
    elif not non_streaming_success and not streaming_success:
        print("\n⚠️  Both modes failed - may be a broader issue")
    elif non_streaming_success and streaming_success:
        print("\n✅ Both modes working - no bug detected")
    else:
        print("\n🤔 Unexpected result pattern")


if __name__ == "__main__":
    asyncio.run(main()) 