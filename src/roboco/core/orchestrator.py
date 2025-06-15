from __future__ import annotations
from typing import List, Dict, Any, Generator
import os
import uuid
from pathlib import Path
import json

from roboco.core.team import Team
from roboco.core.task_step import TaskStep, TextPart, StepPart, ToolCallPart, ToolResultPart, ToolCall, ToolResult
from roboco.core.agent import Agent
from roboco.core.tool import get_tool_registry

# Add litellm for LLM calls
import litellm

class Orchestrator:
    """
    The active execution engine that drives the task forward on a step-by-step basis.
    It takes a Team object as input and exposes methods to start and step through
    the execution, yielding events for UI and logging.
    """
    def __init__(self, team: Team, workspace_dir: str = "./workspaces"):
        self.team = team
        self.workspace_dir = Path(workspace_dir)
        self.history_file: Path | None = None
        self.is_running = False

    @property
    def is_complete(self) -> bool:
        """Checks if the task has completed or should be stopped."""
        if not self.is_running:
            return True
        if len(self.team.history) >= self.team.max_rounds:
            print(f"Task finished after reaching max rounds: {self.team.max_rounds}")
            return True
        return False

    def start(self, initial_prompt: str) -> Generator[Dict[str, Any], None, None]:
        """
        Sets up the task workspace and yields the initial user prompt as the first step.
        """
        task_id = f"task_{uuid.uuid4().hex}"
        task_workspace = self.workspace_dir / task_id
        task_workspace.mkdir(parents=True, exist_ok=True)
        (task_workspace / "artifacts").mkdir(exist_ok=True)
        
        self.history_file = task_workspace / "history.jsonl"
        self.is_running = True

        initial_step = TaskStep(agent_name="user", parts=[TextPart(text=initial_prompt)])
        yield from self._add_and_yield_step(initial_step)
    
    def add_user_message(self, message: str) -> Generator[Dict[str, Any], None, None]:
        """Allows a user to interrupt the flow with a new message."""
        if not self.is_running:
            raise RuntimeError("Cannot add a message to a task that has not been started.")
        
        user_step = TaskStep(agent_name="user", parts=[TextPart(text=message)])
        yield from self._add_and_yield_step(user_step)

    def step(self) -> Generator[Dict[str, Any], None, None]:
        """
        Executes a single step of the task, which includes:
        1. Selecting an agent.
        2. Running the agent (LLM call).
        3. Processing the response (including executing any tool calls).
        """
        if self.is_complete:
            return

        # 1. Select the next agent to act
        last_step = self.team.history[-1]
        next_agent_name = self._select_next_agent(last_step.agent_name)
        if not next_agent_name:
            print("No more agents to run. Ending task.")
            self.is_running = False
            return
        
        agent = self.team.agents[next_agent_name]

        # 2. Compile context and format for LLM
        prompt_history = self._compile_prompt_history(self.team.history)
        messages = self._format_history_for_llm(prompt_history, agent.system_message)
        
        # 3. Get the next action from the agent's "brain" (LLM call)
        response = litellm.completion(
            model=agent.model, messages=messages, tools=agent.tools,
        )
        
        response_choice = response.choices[0].message
        response_text = response_choice.content
        tool_calls = response_choice.tool_calls

        # 4. Create the new TaskStep for the agent's response
        new_step_parts: list[StepPart] = []
        if response_text:
            new_step_parts.append(TextPart(text=response_text))
        if tool_calls:
            for tc in tool_calls:
                new_step_parts.append(
                    ToolCallPart(tool_call=ToolCall(
                        id=tc.id,
                        tool_name=tc.function.name,
                        args=json.loads(tc.function.arguments)
                    ))
                )

        if not new_step_parts:
            print("Agent returned an empty response. Ending task.")
            self.is_running = False
            return

        agent_step = TaskStep(agent_name=next_agent_name, parts=new_step_parts)
        yield from self._add_and_yield_step(agent_step)

        # 5. If there are tool calls, execute them and create a result step
        if tool_calls:
            # We will create a single step that holds all the tool results
            # from this turn.
            result_parts = []
            tool_registry = get_tool_registry()
            
            for tc in tool_calls:
                tool_name = tc.function.name
                tool_args = json.loads(tc.function.arguments)
                execution_result = tool_registry.execute_tool_sync(tool_name, **tool_args)
                result_parts.append(ToolResultPart(tool_result=ToolResult(
                    tool_call_id=tc.id, result=str(execution_result.result)
                )))

            tool_step = TaskStep(
                agent_name="tool_executor", parts=result_parts
            )
            yield from self._add_and_yield_step(tool_step)

    def _add_and_yield_step(self, step: TaskStep) -> Generator[Dict[str, Any], None, None]:
        """Helper to add a step to history, save it, and yield its events."""
        self.team.history.append(step)
        if self.history_file:
            with open(self.history_file, "a") as f:
                f.write(step.model_dump_json() + "\n")

        yield { "type": "step_start", "data": {"id": step.id, "agent_name": step.agent_name}}
        for part in step.parts:
            yield {"type": f"{part.type}_part", "data": part.model_dump()}
        yield {"type": "step_end", "data": {"id": step.id}}

    def _compile_prompt_history(self, full_history: list[TaskStep]) -> list[TaskStep]:
        """(Placeholder) Implements the Context Compilation Strategy."""
        return full_history

    def _format_history_for_llm(self, history: list[TaskStep], system_message: str) -> list[dict]:
        """Converts our internal TaskStep history into the format required by LLMs."""
        llm_messages = [{"role": "system", "content": system_message}]
        for step in history:
            role = "user" if step.agent_name == "user" else "assistant"
            
            content_parts = []
            tool_call_parts = []
            
            for part in step.parts:
                if isinstance(part, TextPart):
                    content_parts.append({"type": "text", "text": part.text})
                elif isinstance(part, ToolCallPart):
                    # Append the single tool_call to the list for the message
                    tool_call_parts.append({
                        "id": part.tool_call.id,
                        "type": "function",
                        "function": {"name": part.tool_call.tool_name, "arguments": json.dumps(part.tool_call.args)}
                    })
                elif isinstance(part, ToolResultPart):
                    # This role is 'tool', not 'assistant' or 'user'
                    res = part.tool_result
                    llm_messages.append({
                        "role": "tool",
                        "tool_call_id": res.tool_call_id,
                        "content": res.result
                    })

            message: Dict[str, Any] = {"role": role}
            has_content = False
            if content_parts:
                message["content"] = content_parts[0]['text'] # Simplified for now
                has_content = True
            if tool_call_parts:
                message["tool_calls"] = tool_call_parts
                has_content = True
            
            if has_content:
                llm_messages.append(message)

        return llm_messages

    def _select_next_agent(self, last_agent_name: str) -> str | None:
        """Selects the next agent to run in a simple round-robin fashion."""
        agent_names = list(self.team.agents.keys())
        if not agent_names:
            return None
        
        # If the last step was a tool result, the original caller should speak next.
        # This is a simplification; a more robust way would be to track the tool requester.
        if last_agent_name == "tool_executor":
            for step in reversed(self.team.history):
                if step.agent_name != "tool_executor":
                    return step.agent_name

        try:
            last_index = agent_names.index(last_agent_name)
            next_index = (last_index + 1) % len(agent_names)
        except ValueError:
            next_index = 0
            
        return agent_names[next_index]

    def _execute_step(self, step: TaskStep) -> TaskStep | None:
        """
        (This method will be removed or refactored into the main loop)
        """
        print(f"Executing step: {step.id}")
        return None

    def _is_task_complete(self, step: TaskStep) -> bool:
        # Placeholder for termination logic
        return "finished" in step.parts[0].text.lower() 