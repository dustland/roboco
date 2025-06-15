#!/usr/bin/env python3
"""
AgentX Orchestration and Handoff Demonstration

This example demonstrates how the AgentX framework orchestrates multi-agent
collaboration with seamless handoffs between agents. 

The workflow shows:
1. Writer creates initial content
2. Writer hands off to Reviewer for feedback
3. Reviewer provides feedback and hands back to Writer
4. Writer implements revisions and hands back to Reviewer
5. Reviewer approves final content

This showcases the core orchestration capabilities of the AgentX framework.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import agentx
from agentx.core.team import Team
from agentx.core.orchestrator import Orchestrator


async def start_streaming_collaboration(config_path: Path, prompt: str):
    """
    Start a collaborative task with real-time streaming.
    
    This demonstrates end-to-end streaming where agent responses
    are displayed in real-time as they're generated.
    """
    # Load team configuration
    team = Team.from_config_file(str(config_path))
    
    # Create orchestrator
    orchestrator = Orchestrator(team)
    
    # Start the task
    task_id = await orchestrator.start_task(prompt)
    
    print(f"🎬 Starting streaming collaboration (Task: {task_id})")
    print()
    
    # Track streaming data
    total_chunks = 0
    agent_responses = {}
    handoffs = []
    
    try:
        # Execute with streaming
        async for update in orchestrator.execute_task_streaming(task_id):
            update_type = update.get("type")
            
            if update_type == "agent_start":
                agent_name = update["agent_name"]
                print(f"\n🤖 {agent_name.upper()} is thinking...")
                print(f"💭 ", end="", flush=True)
                agent_responses[agent_name] = ""
                
            elif update_type == "response_chunk":
                chunk = update["chunk"]
                agent_name = update["agent_name"]
                
                # Print chunk in real-time
                print(chunk, end="", flush=True)
                
                # Track for analysis
                agent_responses[agent_name] += chunk
                total_chunks += 1
                
            elif update_type == "agent_complete":
                agent_name = update["agent_name"]
                response_length = update["response_length"]
                print(f"\n\n✅ {agent_name} completed response ({response_length} characters)")
                
            elif update_type == "handoff":
                from_agent = update["from_agent"]
                to_agent = update["to_agent"]
                handoffs.append(f"{from_agent} → {to_agent}")
                print(f"\n🔄 HANDOFF: {from_agent} → {to_agent}")
                print("=" * 50)
                
            elif update_type == "task_complete":
                total_steps = update["total_steps"]
                print(f"\n🎉 Task completed! ({total_steps} total steps)")
                break
                
            elif update_type == "error":
                error = update["error"]
                print(f"\n❌ Error: {error}")
                return {"success": False, "error": error}
        
        # Return summary
        return {
            "success": True,
            "total_chunks": total_chunks,
            "agent_responses": agent_responses,
            "handoffs": handoffs,
            "conversation_history": []  # Would need to get from orchestrator
        }
        
    except Exception as e:
        print(f"\n💥 Streaming failed: {e}")
        return {"success": False, "error": str(e)}


async def demonstrate_orchestration_and_handoffs():
    """
    Demonstrate orchestration and handoffs between Writer and Reviewer agents.
    
    This function shows how the AgentX orchestrator manages agent collaboration
    with automatic handoffs based on agent decisions.
    """
    print("🚀 AgentX Orchestration & Handoff Demonstration")
    print("=" * 60)
    print()
    
    # Initialize the framework
    agentx.initialize()
    
    # Load team configuration
    config_path = Path(__file__).parent / "config" / "team.yaml"
    
    try:
        
        # Define the writing assignment
        writing_prompt = """
        Write a comprehensive article about "The Future of Remote Work" for a business publication.
        
        Requirements:
        - Target audience: Business leaders and HR professionals
        - Length: 800-1200 words
        - Include practical insights and actionable advice
        - Cover trends, challenges, and opportunities
        - Professional tone with engaging examples
        
        Please create a well-structured article that provides real value to readers.
        After completing your draft, hand off to the reviewer for feedback.
        """
        
        print("🎯 Writing Assignment: 'The Future of Remote Work'")
        print("📝 Starting collaborative writing process...")
        print()
        print("Expected workflow:")
        print("  1. Writer creates initial draft")
        print("  2. Writer → Reviewer (handoff: draft_complete)")
        print("  3. Reviewer provides feedback")
        print("  4. Reviewer → Writer (handoff: feedback_provided)")
        print("  5. Writer implements revisions")
        print("  6. Writer → Reviewer (handoff: revision_complete)")
        print("  7. Reviewer approves final content")
        print()
        print("🔄 Starting orchestrated collaboration...")
        print("-" * 60)
        
        # Start the orchestrated collaboration with streaming
        result = await start_streaming_collaboration(
            config_path=config_path,
            prompt=writing_prompt
        )
        
        print("-" * 60)
        print()
        
        if result and result.get("success"):
            print("✅ Streaming orchestration completed successfully!")
            print()
            print("📊 Streaming Collaboration Summary:")
            print(f"   • Total streaming chunks: {result.get('total_chunks', 0)}")
            print(f"   • Agents participated: {len(result.get('agent_responses', {}))}")
            print(f"   • Handoffs executed: {len(result.get('handoffs', []))}")
            print()
            
            # Show the orchestration flow
            print("🔄 Streaming Orchestration Flow:")
            handoffs = result.get('handoffs', [])
            if handoffs:
                for i, handoff in enumerate(handoffs, 1):
                    print(f"   {i}. {handoff}")
            else:
                print("   • Single-agent workflow (no handoffs)")
            
            print()
            print("📈 Agent Response Statistics:")
            agent_responses = result.get('agent_responses', {})
            for agent, response in agent_responses.items():
                print(f"   • {agent}: {len(response)} characters")
            
            print()
            print("🎉 Streaming Demonstration Complete!")
            print()
            print("Key Streaming Features Demonstrated:")
            print("  ✓ Real-time response streaming (word-by-word)")
            print("  ✓ Live agent handoff notifications")
            print("  ✓ Streaming orchestration with event updates")
            print("  ✓ End-to-end streaming from Brain → Orchestrator → UI")
            print("  ✓ Multi-agent collaboration with live feedback")
            
            return True
            
        else:
            print("❌ Streaming orchestration failed!")
            if result:
                print(f"   Error: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Demonstration failed: {e}")
        logger.exception("Orchestration demonstration error")
        return False


async def show_framework_info():
    """Display information about the AgentX framework and this demonstration."""
    print()
    print("ℹ️  About This Demonstration")
    print("=" * 60)
    print()
    print("This example showcases the core orchestration capabilities of AgentX:")
    print()
    print("🎭 Agent Roles:")
    print("   • Writer: Creates and revises content based on requirements")
    print("   • Reviewer: Provides feedback and quality assurance")
    print()
    print("🔄 Handoff Mechanisms:")
    print("   • Condition-based: Agents decide when to hand off work")
    print("   • Automatic: Orchestrator manages the transitions")
    print("   • Bidirectional: Agents can hand work back and forth")
    print()
    print("🎯 Orchestration Features:")
    print("   • Task-centric workflow management")
    print("   • Event-driven agent coordination")
    print("   • Real-time streaming responses")
    print("   • Multi-round collaboration support")
    print()
    print("📁 Configuration:")
    print("   • Team: config/team.yaml (Writer + Reviewer)")
    print("   • Prompts: config/prompts/ (agent instructions)")
    print("   • Handoffs: Defined in team configuration")
    print()


async def main():
    """Main demonstration function."""
    try:
        # Show framework information
        await show_framework_info()
        
        # Run the orchestration demonstration
        success = await demonstrate_orchestration_and_handoffs()
        
        if success:
            print()
            print("🎊 Orchestration and handoff demonstration completed successfully!")
            print("   Check the workspace/ directory for generated content.")
        else:
            print()
            print("⚠️  Demonstration encountered issues. Check logs for details.")
            
    except KeyboardInterrupt:
        print("\n🛑 Demonstration interrupted by user.")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        logger.exception("Main demonstration error")


if __name__ == "__main__":
    print("🤖 AgentX Framework - Orchestration & Handoff Demo")
    print()
    asyncio.run(main()) 