#!/usr/bin/env python3
"""
AgentX Step-Through Debugging Demo

This demo showcases the step-through debugging capabilities of AgentX.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from agentx.core.orchestrator import Orchestrator
from agentx.core.team import Team


class StepThroughDemo:
    """Interactive step-through debugging demo."""
    
    def __init__(self):
        self.orchestrator = None
        self.task_id = None
        self.running = True
    
    async def start(self):
        """Start the demo."""
        print("🐛 AgentX Step-Through Debugging Demo")
        print("=" * 40)
        
        # Check environment
        if not self._check_environment():
            return
        
        # Load team
        try:
            team_config_path = Path(__file__).parent / "config" / "team.yaml"
            team = Team.from_config(str(team_config_path))
            self.orchestrator = Orchestrator(team)
            print(f"✅ Loaded team: {team.name}")
        except Exception as e:
            print(f"❌ Error loading team: {e}")
            return
        
        # Start task
        task_prompt = "Create a project plan for a mobile app"
        self.task_id = await self.orchestrator.start_task(
            prompt=task_prompt,
            initial_agent="planner"
        )
        
        # Set step-through mode
        await self.orchestrator.set_execution_mode(self.task_id, "step_through")
        
        print(f"\n📝 Task: {task_prompt}")
        print("🎯 Mode: Step-through debugging")
        print("\n💡 Instructions:")
        print("   • Press Enter to continue to next step")
        print("   • Type a message to inject user feedback")
        print("   • Type /help for debug commands")
        print("   • Type /quit to exit")
        
        await self._interactive_execution()
    
    def _check_environment(self):
        """Check API keys."""
        if os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY"):
            return True
        print("❌ Please set OPENAI_API_KEY or DEEPSEEK_API_KEY")
        return False
    
    async def _interactive_execution(self):
        """Main execution loop."""
        step_count = 0
        
        while self.running:
            try:
                # Start/resume execution
                if step_count == 0:
                    await self.orchestrator.resume_task(self.task_id)
                    await asyncio.sleep(1)
                
                # Check task state
                task_state = self.orchestrator.get_task_state(self.task_id)
                if not task_state:
                    break
                
                if task_state.is_complete:
                    print("\n✅ Task completed!")
                    break
                
                if not task_state.is_paused:
                    await asyncio.sleep(0.5)
                    continue
                
                step_count += 1
                await self._show_step_status(step_count)
                
                # Get user input
                user_input = input("\ndebug> ").strip()
                
                # Process input
                if user_input == "/quit":
                    break
                elif user_input == "/help":
                    self._show_help()
                elif user_input.startswith("/"):
                    await self._handle_command(user_input)
                elif user_input:
                    # Inject user message
                    await self.orchestrator.inject_user_message(self.task_id, user_input)
                    print(f"💬 Injected: {user_input}")
                    await self.orchestrator.resume_task(self.task_id)
                else:
                    # Continue to next step
                    await self.orchestrator.resume_task(self.task_id)
                
            except KeyboardInterrupt:
                print("\n🛑 Demo interrupted")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                break
        
        print("\n👋 Demo ended")
    
    async def _show_step_status(self, step_count):
        """Show current step status."""
        state_data = self.orchestrator.inspect_task_state(self.task_id)
        task_state = self.orchestrator.get_task_state(self.task_id)
        
        print(f"\n⏸️ Step {step_count} - Execution paused")
        print(f"👤 Current Agent: {state_data['current_agent']}")
        print(f"📊 Round: {state_data['round_count']}")
        
        # Show last response
        if task_state.history:
            last_step = task_state.history[-1]
            print(f"\n💭 {last_step.agent_name.title()} says:")
            for part in last_step.parts:
                if hasattr(part, 'text'):
                    text = part.text[:200] + "..." if len(part.text) > 200 else part.text
                    print(f"   {text}")
    
    def _show_help(self):
        """Show help."""
        print("\n🐛 Debug Commands:")
        print("   /help     - Show this help")
        print("   /status   - Show task status")
        print("   /history  - Show conversation history")
        print("   /continue - Switch to autonomous mode")
        print("   /quit     - Exit demo")
        print("\n💬 User Actions:")
        print("   <Enter>   - Continue to next step")
        print("   <message> - Inject user feedback")
    
    async def _handle_command(self, command):
        """Handle debug commands."""
        if command == "/status":
            state_data = self.orchestrator.inspect_task_state(self.task_id)
            print(f"\n📊 Status:")
            print(f"   Agent: {state_data['current_agent']}")
            print(f"   Round: {state_data['round_count']}")
            print(f"   Mode: {state_data['execution_mode']}")
        
        elif command == "/history":
            task_state = self.orchestrator.get_task_state(self.task_id)
            print(f"\n📜 History ({len(task_state.history)} steps):")
            for i, step in enumerate(task_state.history[-3:], 1):
                print(f"   {i}. {step.agent_name}: {step.parts[0].text[:50]}...")
        
        elif command == "/continue":
            await self.orchestrator.set_execution_mode(self.task_id, "autonomous")
            await self.orchestrator.resume_task(self.task_id)
            print("▶️ Switched to autonomous mode")
            self.running = False


async def main():
    """Main entry point."""
    demo = StepThroughDemo()
    await demo.start()


if __name__ == "__main__":
    asyncio.run(main()) 