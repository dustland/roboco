#!/usr/bin/env python3
"""
Demo script showing how to use the Roboco event system.

This demonstrates the clean API for publishing and subscribing to events
without needing to know about the underlying event bus implementation.
"""

import asyncio
from datetime import datetime

# Import the clean event API
from roboco.event import (
    publish_event, subscribe_to_events, get_event_stats, 
    initialize_event_bus, EventPriority
)

# Import event types
from roboco.core.event import TaskStartEvent, TaskCompleteEvent, AgentStartEvent


async def demo_event_system():
    """Demonstrate the event system functionality."""
    
    print("🚀 Starting Roboco Event System Demo")
    
    # Initialize the event bus
    await initialize_event_bus()
    
    # Set up event handlers
    def handle_task_events(event_data):
        """Handle task-related events."""
        print(f"📋 Task Event: {event_data.type}")
        if hasattr(event_data, 'task_id'):
            print(f"   Task ID: {event_data.task_id}")
        if hasattr(event_data, 'initial_prompt'):
            print(f"   Prompt: {event_data.initial_prompt}")
    
    def handle_agent_events(event_data):
        """Handle agent-related events."""
        print(f"🤖 Agent Event: {event_data.type}")
        if hasattr(event_data, 'agent_name'):
            print(f"   Agent: {event_data.agent_name}")
        if hasattr(event_data, 'step_id'):
            print(f"   Step ID: {event_data.step_id}")
    
    async def handle_all_events(event_data):
        """Handle all events (async handler example)."""
        print(f"📡 All Events Monitor: {event_data.type} at {datetime.now().strftime('%H:%M:%S')}")
    
    # Subscribe to events
    print("\n📡 Setting up event subscriptions...")
    
    task_sub_id = subscribe_to_events(
        event_types=["event_task_start", "event_task_complete"],
        handler=handle_task_events,
        priority=EventPriority.HIGH
    )
    
    agent_sub_id = subscribe_to_events(
        event_types=["event_agent_start"],
        handler=handle_agent_events
    )
    
    all_events_sub_id = subscribe_to_events(
        event_types=["event_task_start", "event_task_complete", "event_agent_start"],
        handler=handle_all_events,
        priority=EventPriority.LOW  # Lower priority, runs after specific handlers
    )
    
    print(f"   ✅ Task subscription: {task_sub_id}")
    print(f"   ✅ Agent subscription: {agent_sub_id}")
    print(f"   ✅ All events subscription: {all_events_sub_id}")
    
    # Publish some events
    print("\n🎯 Publishing events...")
    
    # Publish a task start event
    task_start_event = TaskStartEvent(
        task_id="demo_task_123",
        timestamp=datetime.now(),
        initial_prompt="Create a simple Python script",
        execution_mode="autonomous",
        team_config={"agents": ["coder", "reviewer"]}
    )
    
    event_id1 = await publish_event(
        task_start_event,
        source="demo_script",
        correlation_id="demo_session",
        tags={"demo": "true", "environment": "development"}
    )
    print(f"   📤 Published task start event: {event_id1}")
    
    # Wait a bit for processing
    await asyncio.sleep(0.1)
    
    # Publish an agent start event
    agent_start_event = AgentStartEvent(
        agent_name="coder",
        step_id="step_456",
        timestamp=datetime.now()
    )
    
    event_id2 = await publish_event(
        agent_start_event,
        source="agent:coder",
        correlation_id="demo_session",
        tags={"agent": "coder", "demo": "true"}
    )
    print(f"   📤 Published agent start event: {event_id2}")
    
    # Wait a bit for processing
    await asyncio.sleep(0.1)
    
    # Publish a task complete event
    task_complete_event = TaskCompleteEvent(
        task_id="demo_task_123",
        timestamp=datetime.now(),
        final_status="success",
        total_steps=5,
        total_duration_ms=2500,
        artifacts_created=["script.py", "README.md"]
    )
    
    event_id3 = await publish_event(
        task_complete_event,
        source="demo_script",
        correlation_id="demo_session",
        tags={"demo": "true", "status": "completed"}
    )
    print(f"   📤 Published task complete event: {event_id3}")
    
    # Wait for all events to be processed
    await asyncio.sleep(0.2)
    
    # Show statistics
    print("\n📊 Event System Statistics:")
    stats = get_event_stats()
    print(f"   Total events published: {stats.total_events_published}")
    print(f"   Total events processed: {stats.total_events_processed}")
    print(f"   Active subscriptions: {stats.active_subscriptions}")
    print(f"   Average processing time: {stats.average_processing_time_ms:.2f}ms")
    
    if stats.event_types_count:
        print("   Event types:")
        for event_type, count in stats.event_types_count.items():
            print(f"     {event_type}: {count}")
    
    print("\n✨ Demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(demo_event_system()) 