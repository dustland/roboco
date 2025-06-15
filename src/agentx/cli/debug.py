"""
AgentX Debugging CLI

Provides step-through debugging capabilities for AgentX tasks including
breakpoints, state inspection, and context modification.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..core.orchestrator import Orchestrator, TaskState
from ..core.team import Team
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DebugSession:
    """Interactive debugging session for AgentX tasks."""
    
    def __init__(self, orchestrator: Orchestrator, task_id: str):
        self.orchestrator = orchestrator
        self.task_id = task_id
        self.running = True
    
    async def start(self):
        """Start the interactive debugging session."""
        print(f"🐛 AgentX Debug Session - Task: {self.task_id}")
        print("=" * 60)
        
        # Show initial state
        await self._show_status()
        
        print("\n💡 Debug Commands:")
        print("  status     - Show current task status")
        print("  inspect    - Inspect detailed task state")
        print("  history    - Show conversation history")
        print("  breakpoint - Set/list breakpoints")
        print("  step       - Execute one step")
        print("  continue   - Continue execution")
        print("  inject     - Inject user message")
        print("  override   - Override next agent")
        print("  context    - Modify debug context")
        print("  pause      - Pause execution")
        print("  resume     - Resume execution")
        print("  quit       - Exit debug session")
        print()
        
        # Interactive loop
        while self.running:
            try:
                command = input("debug> ").strip().lower()
                await self._handle_command(command)
            except KeyboardInterrupt:
                print("\n🛑 Debug session interrupted")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    async def _handle_command(self, command: str):
        """Handle debug commands."""
        parts = command.split()
        if not parts:
            return
        
        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        if cmd == "quit" or cmd == "exit":
            self.running = False
            print("👋 Exiting debug session")
        
        elif cmd == "status":
            await self._show_status()
        
        elif cmd == "inspect":
            await self._inspect_state()
        
        elif cmd == "history":
            await self._show_history(int(args[0]) if args else 10)
        
        elif cmd == "breakpoint" or cmd == "bp":
            await self._handle_breakpoint(args)
        
        elif cmd == "step":
            await self._step_execution()
        
        elif cmd == "continue" or cmd == "cont":
            await self._continue_execution()
        
        elif cmd == "inject":
            if not args:
                print("Usage: inject <message>")
                return
            message = " ".join(args)
            await self._inject_message(message)
        
        elif cmd == "override":
            if not args:
                print("Usage: override <agent_name>")
                return
            await self._override_agent(args[0])
        
        elif cmd == "context":
            await self._modify_context(args)
        
        elif cmd == "pause":
            await self._pause_task()
        
        elif cmd == "resume":
            await self._resume_task()
        
        elif cmd == "help":
            await self._show_help()
        
        else:
            print(f"Unknown command: {cmd}. Type 'help' for available commands.")
    
    async def _show_status(self):
        """Show current task status."""
        try:
            state_data = self.orchestrator.inspect_task_state(self.task_id)
            
            print(f"📊 Task Status: {self.task_id}")
            print(f"  Current Agent: {state_data['current_agent']}")
            print(f"  Round: {state_data['round_count']}")
            print(f"  Complete: {state_data['is_complete']}")
            print(f"  Paused: {state_data['is_paused']}")
            print(f"  Execution Mode: {state_data['execution_mode']}")
            print(f"  History Length: {state_data['history_length']}")
            print(f"  Artifacts: {len(state_data['artifacts'])}")
            print(f"  Breakpoints: {state_data['breakpoints']}")
            if state_data['last_breakpoint']:
                print(f"  Last Breakpoint: {state_data['last_breakpoint']}")
        except Exception as e:
            print(f"❌ Error getting status: {e}")
    
    async def _inspect_state(self):
        """Show detailed task state inspection."""
        try:
            state_data = self.orchestrator.inspect_task_state(self.task_id)
            
            print("🔍 Detailed Task Inspection:")
            print(json.dumps(state_data, indent=2, default=str))
        except Exception as e:
            print(f"❌ Error inspecting state: {e}")
    
    async def _show_history(self, limit: int = 10):
        """Show conversation history."""
        try:
            task_state = self.orchestrator.get_task_state(self.task_id)
            if not task_state:
                print("❌ Task not found")
                return
            
            history = task_state.history[-limit:] if limit > 0 else task_state.history
            
            print(f"📜 Conversation History (last {len(history)} steps):")
            for i, step in enumerate(history, 1):
                timestamp = step.timestamp.strftime("%H:%M:%S") if step.timestamp else "N/A"
                print(f"  {i}. [{timestamp}] {step.agent_name}:")
                for part in step.parts:
                    if hasattr(part, 'text'):
                        text = part.text[:100] + "..." if len(part.text) > 100 else part.text
                        print(f"     {text}")
                print()
        except Exception as e:
            print(f"❌ Error showing history: {e}")
    
    async def _handle_breakpoint(self, args: List[str]):
        """Handle breakpoint commands."""
        if not args:
            # List current breakpoints
            try:
                state_data = self.orchestrator.inspect_task_state(self.task_id)
                breakpoints = state_data['breakpoints']
                if breakpoints:
                    print(f"🔴 Active Breakpoints: {', '.join(breakpoints)}")
                else:
                    print("🟢 No breakpoints set")
            except Exception as e:
                print(f"❌ Error listing breakpoints: {e}")
            return
        
        action = args[0]
        if action == "set":
            if len(args) < 2:
                print("Usage: breakpoint set <type>")
                print("Types: all, agent_turn, tool_call, handoff, error, before_agent_turn, after_agent_turn")
                return
            
            breakpoint_type = args[1]
            try:
                current_state = self.orchestrator.inspect_task_state(self.task_id)
                new_breakpoints = current_state['breakpoints'] + [breakpoint_type]
                await self.orchestrator.set_breakpoints(self.task_id, new_breakpoints)
                print(f"✅ Set breakpoint: {breakpoint_type}")
            except Exception as e:
                print(f"❌ Error setting breakpoint: {e}")
        
        elif action == "clear":
            try:
                await self.orchestrator.set_breakpoints(self.task_id, [])
                print("✅ Cleared all breakpoints")
            except Exception as e:
                print(f"❌ Error clearing breakpoints: {e}")
        
        else:
            print("Usage: breakpoint [set <type> | clear]")
    
    async def _step_execution(self):
        """Execute one step."""
        try:
            # Set to step-through mode and resume
            await self.orchestrator.set_execution_mode(self.task_id, "step_through")
            await self.orchestrator.resume_task(self.task_id)
            print("⏭️ Executing one step...")
            
            # Wait a moment for execution
            await asyncio.sleep(0.5)
            await self._show_status()
        except Exception as e:
            print(f"❌ Error stepping: {e}")
    
    async def _continue_execution(self):
        """Continue execution."""
        try:
            await self.orchestrator.set_execution_mode(self.task_id, "autonomous")
            await self.orchestrator.resume_task(self.task_id)
            print("▶️ Continuing execution...")
        except Exception as e:
            print(f"❌ Error continuing: {e}")
    
    async def _inject_message(self, message: str):
        """Inject a user message."""
        try:
            await self.orchestrator.inject_user_message(self.task_id, message)
            print(f"💬 Injected message: {message[:50]}...")
        except Exception as e:
            print(f"❌ Error injecting message: {e}")
    
    async def _override_agent(self, agent_name: str):
        """Override the next agent."""
        try:
            await self.orchestrator.override_next_agent(self.task_id, agent_name)
            print(f"🔄 Overrode next agent: {agent_name}")
        except Exception as e:
            print(f"❌ Error overriding agent: {e}")
    
    async def _modify_context(self, args: List[str]):
        """Modify debug context."""
        if len(args) < 2:
            print("Usage: context <key> <value>")
            return
        
        key = args[0]
        value = " ".join(args[1:])
        
        try:
            # Try to parse as JSON, otherwise use as string
            try:
                parsed_value = json.loads(value)
            except:
                parsed_value = value
            
            await self.orchestrator.modify_task_context(self.task_id, {key: parsed_value})
            print(f"🔧 Updated context: {key} = {parsed_value}")
        except Exception as e:
            print(f"❌ Error modifying context: {e}")
    
    async def _pause_task(self):
        """Pause task execution."""
        try:
            await self.orchestrator.pause_task(self.task_id)
            print("⏸️ Task paused")
        except Exception as e:
            print(f"❌ Error pausing task: {e}")
    
    async def _resume_task(self):
        """Resume task execution."""
        try:
            await self.orchestrator.resume_task(self.task_id)
            print("▶️ Task resumed")
        except Exception as e:
            print(f"❌ Error resuming task: {e}")
    
    async def _show_help(self):
        """Show help information."""
        print("🐛 AgentX Debug Commands:")
        print("  status              - Show current task status")
        print("  inspect             - Show detailed task state")
        print("  history [N]         - Show last N conversation steps (default: 10)")
        print("  breakpoint          - List active breakpoints")
        print("  breakpoint set TYPE - Set breakpoint (all, agent_turn, tool_call, handoff, error)")
        print("  breakpoint clear    - Clear all breakpoints")
        print("  step                - Execute one step")
        print("  continue            - Continue autonomous execution")
        print("  inject MESSAGE      - Inject user message into conversation")
        print("  override AGENT      - Override next agent selection")
        print("  context KEY VALUE   - Modify debug context")
        print("  pause               - Pause task execution")
        print("  resume              - Resume task execution")
        print("  quit                - Exit debug session")


async def debug_task(team_config_path: str, task_id: str):
    """Start a debugging session for a task."""
    try:
        # Load team configuration
        team = Team.from_config(team_config_path)
        
        # Create orchestrator
        orchestrator = Orchestrator(team)
        
        # Check if task exists
        if task_id not in orchestrator.list_active_tasks():
            # Try to load from workspace
            workspace_dir = Path(f"workspace/{task_id}")
            if workspace_dir.exists():
                loaded_task_id = await orchestrator.load_task(workspace_dir)
                print(f"📂 Loaded task from workspace: {loaded_task_id}")
            else:
                print(f"❌ Task not found: {task_id}")
                return
        
        # Start debug session
        debug_session = DebugSession(orchestrator, task_id)
        await debug_session.start()
        
    except Exception as e:
        print(f"❌ Error starting debug session: {e}")
        logger.exception("Debug session error")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python -m agentx.cli.debug <team_config_path> <task_id>")
        sys.exit(1)
    
    team_config_path = sys.argv[1]
    task_id = sys.argv[2]
    
    asyncio.run(debug_task(team_config_path, task_id)) 