# Agent Communication Patterns

This document describes the communication patterns used by agents in the Roboco system.

## Termination Messages

Roboco extends AG2's conversation termination pattern with a configurable termination message system. This allows agents to signal when they have completed their task, enabling more efficient conversations.

### How It Works

1. **Configuration**: The termination message is defined in the `config.toml` file:

   ```toml
   # Default termination message for agents
   terminate_msg = "TERMINATE"
   ```

2. **System Message**: The base `Agent` class automatically appends termination instructions to the system message:

   ```
   When you have completed your response, end your message with "TERMINATE" to signal that you are done.
   ```

3. **Detection**: The `HumanProxy` agent checks for the termination message in responses using the `is_termination_msg` parameter:

   ```python
   is_termination_msg=lambda x: terminate_msg in (x.get("content", "") or "")
   ```

4. **Propagation**: When initiating a chat, the termination message is automatically propagated to the recipient agent:
   ```python
   # In HumanProxy.initiate_chat
   recipient.terminate_msg = self.terminate_msg
   ```

### Implementation Details

The termination message system is implemented in three key components:

1. **Base Agent Class**: The `Agent` class in `src/roboco/core/agent.py` handles:

   - Loading the termination message from config if none is provided
   - Storing the termination message as an attribute
   - Appending termination instructions to the system message

2. **HumanProxy Class**: The `HumanProxy` class in `src/roboco/agents/human_proxy.py` handles:

   - Checking for termination messages in responses
   - Propagating termination messages to recipient agents
   - Updating the system message of recipient agents

3. **Configuration**: The `RobocoConfig` class in `src/roboco/core/models.py` defines:
   - The default termination message
   - The configuration structure for the termination message

### Usage Examples

#### Basic Usage

```python
from roboco.agents import ProductManager, HumanProxy

# Create agents with default termination message from config
researcher = ProductManager()
user = HumanProxy()

# Initiate a chat
user.initiate_chat(
    researcher,
    message="What are the latest developments in humanoid robotics?"
)
```

#### Custom Termination Message

```python
from roboco.agents import ProductManager, HumanProxy

# Create agents with custom termination message
researcher = ProductManager(terminate_msg="DONE")
user = HumanProxy(terminate_msg="DONE")

# Initiate a chat
user.initiate_chat(
    researcher,
    message="What are the latest developments in humanoid robotics?"
)
```

### Benefits

1. **Efficient Conversations**: Agents can clearly signal when they have completed their task
2. **Consistent Behavior**: All agents use the same termination pattern
3. **Configurable**: The termination message can be customized through configuration
4. **Automatic Propagation**: Termination messages are automatically propagated between agents

## Other Communication Patterns

Roboco also supports other AG2 communication patterns:

1. **Sequential Chat**: Agents communicate in a sequential manner
2. **Nested Chat**: Agents can initiate nested conversations with other agents
3. **Swarm**: Multiple agents collaborate in a swarm to solve complex problems

For more information on these patterns, see the [AG2 documentation](https://docs.ag2.ai/docs/user-guide/basic-concepts/orchestration/overview).
