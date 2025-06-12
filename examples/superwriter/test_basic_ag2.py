#!/usr/bin/env python3
"""
Basic AG2 Test

This script tests basic AG2 tool execution to isolate the issue.
"""

import os
from autogen import ConversableAgent, register_function

def test_basic_ag2():
    """Test basic AG2 tool execution."""
    print("🧪 Testing Basic AG2 Tool Execution")
    print("=" * 50)
    
    try:
        # Create simple agents
        caller = ConversableAgent(
            name='caller',
            system_message='You are helpful.',
            llm_config={
                'config_list': [{'model': 'gpt-4o-mini', 'api_key': os.getenv('OPENAI_API_KEY')}]
            }
        )

        executor = ConversableAgent(
            name='executor',
            system_message='I execute tools.',
            llm_config=False,
            human_input_mode='NEVER'
        )

        # Simple test function
        def test_func(message: str) -> str:
            return f'Processed: {message}'

        # Register function
        register_function(test_func, caller=caller, executor=executor, name='test_func', description='Test function')

        print("✅ Function registered")

        # Test conversation
        result = caller.initiate_chat(
            recipient=executor,
            message='Please use test_func with message: hello',
            max_turns=2,
            clear_history=True
        )
        
        print('✅ Chat completed')
        print(f'📝 Result: {result}')
        
        return True
        
    except Exception as e:
        print(f'❌ ERROR: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_basic_ag2() 