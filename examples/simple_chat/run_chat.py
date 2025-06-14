#!/usr/bin/env python3
"""
Simple Chat Example

Demonstrates the clean Roboco configuration structure with:
- User agent (human input)
- Assistant agent with search capabilities
- Memory integration
- Clean Team.from_config() API (AG2-consistent)
"""

import os
import sys
import asyncio
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

# Add the src directory to the path so we can import roboco
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from roboco.core.team import Team


async def main():
    """Run the simple chat example."""
    print("🤖 Simple Chat Example")
    print("=" * 50)
    
    try:
        # Clean, simple API - just like AG2!
        print("🚀 Creating team from config...")
        team = Team.from_config(".")
        
        print(f"✅ Team created: {team.name}")
        print(f"👥 Agents: {', '.join(team.get_agent_names())}")
        print(f"🔢 Max rounds: {team.config.max_rounds}")
        print(f"🔄 Speaker selection: {team.config.speaker_selection.value}")
        
        print("\n" + "=" * 50)
        print("✅ Configuration loaded successfully!")
        print("🎯 Team ready to run conversations.")
        
        # Interactive chat loop
        print("\n💬 Simple Chat Interface:")
        print("Type your message to start a conversation")
        print("Type 'quit' to exit")
        
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                    
                elif user_input:
                    print("🤖 Starting team conversation...")
                    
                    # AG2-consistent API: team.run()
                    try:
                        chat_history = await team.run(
                            initial_message=user_input
                        )
                        
                        print("✅ Conversation completed!")
                        print(f"📝 Total messages: {len(chat_history.messages)}")
                        
                    except Exception as e:
                        print(f"❌ Conversation error: {e}")
                        print("💡 Note: This is a config validation demo.")
                        print("   Full AI integration would handle the conversation.")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break
                
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 This example demonstrates the clean config API:")
        print("   team = Team.from_config('.')")
        print("   await team.run(message)")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main())) 