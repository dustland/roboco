#!/usr/bin/env python3
"""
Simple Chat Example

Demonstrates the clean AgentX configuration structure with:
- Assistant agent with search capabilities
- Memory integration
- Clean Team.from_config() API (AG2-consistent)
- Event system integration for observability
"""

import os
import sys
import asyncio
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / ".env")
except ImportError:
    print("💡 Note: python-dotenv not installed, skipping .env file loading")

# Add the src directory to the path so we can import agentx
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import agentx
from agentx.core.team import Team
from agentx.event import subscribe_to_events, get_event_stats, initialize_event_bus


async def setup_event_monitoring():
    """Set up event monitoring for the chat session."""
    def handle_task_events(event_data):
        """Handle task-related events."""
        if event_data.type == "event_task_start":
            print(f"🚀 Task started: {event_data.task_id}")
        elif event_data.type == "event_task_complete":
            print(f"✅ Task completed: {event_data.task_id} ({event_data.total_steps} steps)")
    
    def handle_agent_events(event_data):
        """Handle agent-related events."""
        if event_data.type == "event_agent_start":
            print(f"🤖 Agent {event_data.agent_name} started processing...")
        elif event_data.type == "event_agent_complete":
            print(f"✨ Agent {event_data.agent_name} completed turn")
    
    # Subscribe to events
    subscribe_to_events(
        event_types=["event_task_start", "event_task_complete"],
        handler=handle_task_events
    )
    
    subscribe_to_events(
        event_types=["event_agent_start", "event_agent_complete"],
        handler=handle_agent_events
    )


async def main():
    """Run the simple chat example."""
    print("🤖 Simple Chat Example with Event System")
    print("=" * 60)
    
    try:
        # Initialize AgentX framework
        print("🔧 Initializing AgentX framework...")
        agentx.initialize()
        
        # Initialize event system
        print("📡 Initializing event system...")
        await initialize_event_bus()
        await setup_event_monitoring()
        
        # Clean, simple API - just like AG2!
        print("🚀 Creating team from config...")
        config_path = Path(__file__).parent / "team.yaml"
        team = Team.from_config(config_path)
        
        print(f"✅ Team created: {team.name}")
        print(f"👥 Agents: {', '.join(team.get_agent_names())}")
        print(f"🔢 Max rounds: {team.config.execution.max_rounds}")
        print(f"🧠 Memory enabled: {team.config.memory.enabled}")
        
        print("\n" + "=" * 60)
        print("✅ Configuration loaded successfully!")
        print("🎯 Team ready to run conversations.")
        print("📊 Event monitoring active - you'll see real-time updates!")
        
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
                        print("⏳ Processing your message...")
                        chat_history = await team.run(
                            initial_message=user_input
                        )
                        
                        print("\n📋 Conversation Results:")
                        print(f"📝 Total messages: {len(chat_history.messages)}")
                        print(f"🆔 Task ID: {chat_history.task_id}")
                        
                        # Show the conversation
                        if chat_history.messages:
                            print("\n💬 Conversation:")
                            for msg in chat_history.messages[-3:]:  # Show last 3 messages
                                role_emoji = "🤖" if msg['role'] == 'assistant' else "👤"
                                agent_name = msg.get('agent', 'unknown')
                                print(f"   {role_emoji} {agent_name}: {msg['content'][:100]}...")
                        
                        # Show event statistics
                        stats = get_event_stats()
                        print(f"\n📊 Event Stats: {stats.total_events_published} published, {stats.total_events_processed} processed")
                        
                    except Exception as e:
                        print(f"❌ Conversation error: {e}")
                        print("💡 Note: This demonstrates the event system and config loading.")
                        print("   Full LLM integration would handle the actual conversation.")
                        import traceback
                        traceback.print_exc()
                
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