#!/usr/bin/env python3
"""
SuperWriter Demo with Event Monitoring

This demo showcases a multi-agent collaboration system for content creation,
enhanced with comprehensive event monitoring and analytics.

Features:
- Real-time collaboration monitoring
- Agent activity tracking  
- Tool usage analytics
- Performance metrics
- Error monitoring and debugging
"""

import asyncio
import os
from roboco import run_team, InMemoryEventBus, EventMonitor

async def main():
    """Run the SuperWriter demo with comprehensive monitoring."""
    
    # Set up event monitoring
    event_bus = InMemoryEventBus()
    monitor = EventMonitor(print_interval=30.0)  # Print stats every 30 seconds
    
    try:
        # Start monitoring
        await monitor.start(event_bus)
        print("🔍 Event monitoring started - tracking collaboration in real-time...")
        
        # Run the team collaboration with a simple task
        # The planner will expand this into complete requirements
        # All collaboration settings (max_rounds, human_input_mode) are configured in config/default.yaml
        result = await run_team(
            config_path="config/default.yaml",  # Fixed: point to actual YAML file
            task="Write a comprehensive article about the future of AI in healthcare",
            event_bus=event_bus
        )
        
        # Print final results
        print("\n" + "="*60)
        print("📝 COLLABORATION COMPLETE!")
        print("="*60)
        print(f"Summary: {result.summary}")
        
        # Print comprehensive analytics
        print("\n" + "="*60)
        print("📊 FINAL COLLABORATION ANALYTICS")
        print("="*60)
        
        metrics = monitor.get_metrics()
        
        # Overall stats
        print(f"\n🎯 Overall Performance:")
        print(f"   • Total events processed: {metrics.total_events}")
        print(f"   • Collaboration duration: {metrics.duration_seconds:.1f} seconds")
        print(f"   • Average events per second: {metrics.events_per_second:.2f}")
        
        # Agent activity analysis
        if metrics.agent_stats:
            print(f"\n🤖 Agent Activity Analysis:")
            for agent_id, stats in metrics.agent_stats.items():
                active_duration = (stats['last_activity'] - stats['first_activity']).total_seconds()
                print(f"   • {agent_id}:")
                print(f"     - Messages sent: {stats['messages_sent']}")
                print(f"     - Messages received: {stats['messages_received']}")
                print(f"     - Total events: {stats['total_events']}")
                print(f"     - Active duration: {active_duration:.1f}s")
        
        # Tool usage analysis
        if metrics.tool_stats:
            print(f"\n🔧 Tool Usage Analysis:")
            for tool_name, stats in metrics.tool_stats.items():
                success_rate = (stats['calls_completed'] / max(1, stats['calls_initiated'])) * 100
                avg_time = stats['average_execution_time']
                print(f"   • {tool_name}:")
                print(f"     - Calls initiated: {stats['calls_initiated']}")
                print(f"     - Calls completed: {stats['calls_completed']}")
                print(f"     - Calls failed: {stats['calls_failed']}")
                print(f"     - Success rate: {success_rate:.1f}%")
                if avg_time > 0:
                    print(f"     - Average execution time: {avg_time:.0f}ms")
        
        # Error analysis
        if metrics.error_count > 0:
            print(f"\n⚠️  Error Analysis:")
            print(f"   • Total errors: {metrics.error_count}")
            error_events = monitor.get_error_events()
            for error in error_events[-3:]:  # Show last 3 errors
                print(f"   • {error['timestamp']}: {error.get('error_type', 'Unknown')} - {error.get('message', 'No details')}")
        
        # Timeline highlights
        timeline = monitor.get_timeline_events(limit=10)
        if timeline:
            print(f"\n📅 Recent Activity Timeline:")
            for event in timeline[-5:]:  # Show last 5 events
                event_type = event.get('type', 'unknown')
                timestamp = event.get('timestamp', 'unknown')
                if event_type == 'message_sent':
                    print(f"   • {timestamp}: {event.get('agent')} sent message to {event.get('recipient')}")
                elif event_type == 'tool_call_completed':
                    success = "✅" if event.get('success') else "❌"
                    print(f"   • {timestamp}: {event.get('agent')} used {event.get('tool')} {success}")
                else:
                    print(f"   • {timestamp}: {event_type}")
        
        print(f"\n🎉 Collaboration monitoring complete!")
        
    except Exception as e:
        print(f"❌ Error during collaboration: {e}")
        
        # Even on error, show what we captured
        metrics = monitor.get_metrics()
        if metrics.total_events > 0:
            print(f"\n📊 Partial Analytics (before error):")
            print(f"   • Events captured: {metrics.total_events}")
            print(f"   • Duration: {metrics.duration_seconds:.1f}s")
            
            error_events = monitor.get_error_events()
            if error_events:
                print(f"   • Errors logged: {len(error_events)}")
                latest_error = error_events[-1]
                print(f"   • Latest error: {latest_error.get('message', 'No details')}")
        
        raise
        
    finally:
        # Clean up monitoring
        await monitor.stop()
        print("🔍 Event monitoring stopped")

if __name__ == "__main__":
    # Check required environment variables
    required_vars = ["OPENAI_API_KEY", "SERPAPI_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables and try again.")
        exit(1)
    
    print("🚀 Starting SuperWriter collaboration with comprehensive monitoring...")
    asyncio.run(main()) 