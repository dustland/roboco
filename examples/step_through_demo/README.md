# Step-Through Debugging Demo

This example demonstrates AgentX's step-through debugging capabilities, allowing you to:

- **Pause execution** after each agent turn
- **Inspect task state** at any point
- **Inject user messages** to guide the conversation
- **Set breakpoints** for specific conditions
- **Override agent selection** for debugging
- **Continue execution** step by step or autonomously

## Features Demonstrated

- 🐛 **Interactive Debugging**: Step through agent conversations one turn at a time
- 💬 **User Intervention**: Inject messages to redirect the conversation
- 🔍 **State Inspection**: View detailed task state and conversation history
- 🔴 **Breakpoints**: Set breakpoints for handoffs, tool calls, or errors
- 🎯 **Agent Override**: Force specific agent selection for testing
- ⏯️ **Execution Control**: Pause, resume, and step through execution

## Quick Start

1. **Set up environment**:

   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   # or
   export DEEPSEEK_API_KEY="your-deepseek-api-key-here"
   ```

2. **Run the demo**:

   ```bash
   cd examples/step_through_demo
   python main.py
   ```

3. **Follow the interactive prompts** to explore debugging features

The demo starts with a simple project planning task and demonstrates core step-through debugging capabilities.

## Interactive Commands

During step-through execution, you can:

- **Press Enter**: Continue to next step
- **Type message**: Inject user intervention
- **`/help`**: Show available commands
- **`/status`**: Show current task status
- **`/history`**: Show conversation history
- **`/continue`**: Switch to autonomous mode
- **`/quit`**: Exit demo

## Example Usage

```bash
$ python main.py

🐛 AgentX Step-Through Debugging Demo
========================================
✅ Loaded team: Debug Team

📝 Task: Create a project plan for a mobile app
🎯 Mode: Step-through debugging

💡 Instructions:
   • Press Enter to continue to next step
   • Type a message to inject user feedback
   • Type /help for debug commands
   • Type /quit to exit

⏸️ Step 1 - Execution paused
👤 Current Agent: planner
📊 Round: 1

💭 Planner says:
I'll help you create a comprehensive project plan for a mobile app...

debug>
```

## Configuration

The demo uses a specialized team configuration optimized for debugging:

- **Planner**: Creates project plans and task breakdowns
- **Designer**: Focuses on UI/UX and design decisions
- **Developer**: Handles technical implementation details
- **Reviewer**: Provides feedback and quality assurance

Each agent has clear handoff rules to demonstrate the step-through process.

## Files

```
step_through_demo/
├── README.md              # This file
├── main.py                # Main demo script
└── config/
    ├── team.yaml          # Team configuration for debugging
    └── prompts/           # Agent prompts optimized for demo
        ├── planner.md
        ├── designer.md
        ├── developer.md
        └── reviewer.md
```

## Learning Objectives

After completing this demo, you'll understand:

1. **How to use step-through mode** for debugging multi-agent conversations
2. **When and how to inject user messages** to guide agent behavior
3. **How to set and use breakpoints** for specific debugging scenarios
4. **How to inspect task state** and conversation history
5. **How to override agent selection** for testing purposes
6. **Best practices for debugging** multi-agent workflows

## Advanced Features

### Custom Breakpoints

```python
# Set breakpoint on handoffs
await orchestrator.set_breakpoints(task_id, ["handoff"])

# Set breakpoint on tool calls
await orchestrator.set_breakpoints(task_id, ["tool_call"])

# Set breakpoint on errors
await orchestrator.set_breakpoints(task_id, ["error"])
```

### State Inspection

```python
# Get detailed task state
state = orchestrator.inspect_task_state(task_id)
print(f"Current agent: {state['current_agent']}")
print(f"Round: {state['round_count']}")
print(f"Breakpoints: {state['breakpoints']}")
```

### User Intervention

```python
# Inject user message
await orchestrator.inject_user_message(
    task_id,
    "Please focus more on security considerations",
    context={"priority": "high", "topic": "security"}
)
```

## Troubleshooting

**Demo won't start**: Check that your API key is set correctly
**Agents not responding**: Verify team configuration is valid
**Breakpoints not working**: Ensure execution mode is set to "debug"
**State inspection fails**: Check that task ID is valid and active

## Next Steps

- Try the [SuperWriter Example](../superwriter/) for production-ready multi-agent collaboration
- Explore the [Simple Team Example](../simple_team/) for memory and persistence features
- Read the [Debugging Documentation](../../docs/debugging.md) for advanced techniques
