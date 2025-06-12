# /Users/hugh/dustland/roboco/src/roboco/tool/bridge.py
import inspect
import functools
from typing import Callable, List, Dict, Any, Coroutine, get_type_hints, _GenericAlias # type: ignore
from pydantic import BaseModel

from autogen import ConversableAgent

from .interfaces import AbstractTool
from ..config.models import ToolParameterConfig

# Mapping from schema types to Python types
# This will need to be more robust, especially for complex types like array/object
_TYPE_MAP = {
    "string": str,
    "integer": int,
    "boolean": bool,
    "number": float,  # JSON schema "number" can be float or int, float is safer
    "array": list,
    "object": dict,
}

def _map_type_to_python_hint(param_config: ToolParameterConfig) -> type:
    """Maps a ToolParameterConfig type string to a Python type hint."""
    hint = _TYPE_MAP.get(param_config.type.lower())
    if hint is None:
        # Fallback for unknown types or more complex Pydantic models
        # For now, default to Any, but this could be enhanced
        return Any 
    
    if param_config.type.lower() == "array":
        # For List, try to specify List[<item_type>] if possible
        # This is a simplified version. A real implementation would parse param_config.items
        return List[Any] # Placeholder, ideally inspect param_config.items
    elif param_config.type.lower() == "object":
        # For Dict, try to specify Dict[str, <value_type>] if possible
        return Dict[str, Any] # Placeholder

    return hint

async def _execute_tool_wrapper(tool_instance: AbstractTool, **kwargs) -> Any:
    """
    The actual wrapper that calls the tool's run method.
    This is what the dynamically created function will eventually call.
    """
    # TODO: Potentially transform kwargs if the tool expects 'input_data' dict
    # For now, assume tool.run can handle kwargs directly if they match parameter names
    return await tool_instance.run(input_data=kwargs)


def create_tool_function_for_ag2(
    tool_instance: AbstractTool,
    # caller_agent: ConversableAgent, # The agent that can call this function
    # executor_agent: ConversableAgent # The agent that will execute this function
) -> Callable[..., Coroutine[Any, Any, Any]]:
    """
    Dynamically creates an async Python function from an AbstractTool instance
    that is suitable for registration with autogen.register_function.

    The created function will have a signature and docstring derived from the
    tool's metadata and invocation schema.
    """
    tool_name = tool_instance.name
    tool_description = tool_instance.description
    invocation_schema = tool_instance.get_invocation_schema()

    parameters = []
    docstring_params_lines = ["Parameters:", "-----------"]

    for param_config in invocation_schema:
        param_name = param_config.name
        param_type_hint = _map_type_to_python_hint(param_config)
        
        if param_config.required:
            default_value = inspect.Parameter.empty
        else:
            default_value = param_config.default
            # Ensure pydantic models are not used as default directly in signature
            if isinstance(default_value, BaseModel):
                default_value = default_value.model_dump()


        parameters.append(
            inspect.Parameter(
                name=param_name,
                kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=default_value,
                annotation=param_type_hint,
            )
        )
        type_str = param_config.type
        if isinstance(param_type_hint, _GenericAlias): # For List[Any], Dict[str, Any]
             type_str = str(param_type_hint)
        elif hasattr(param_type_hint, '__name__'):
            type_str = param_type_hint.__name__


        desc = f"    {param_name} ({type_str}){(', optional' if not param_config.required else '')}: "
        desc += param_config.description or "No description."
        if not param_config.required and param_config.default is not None:
            desc += f" (default: {param_config.default})"
        docstring_params_lines.append(desc)

    # Construct the full docstring
    full_docstring = f"{tool_description}\n\n" + "\n".join(docstring_params_lines)

    # Create the dynamic function
    # We use functools.partial to bind the tool_instance to our wrapper
    # The signature is applied to a lambda that then calls the partial.
    # This is a common pattern for creating functions with dynamic signatures.

    # Define the core logic that will be wrapped
    async def execution_core(**kwargs):
        return await tool_instance.run(input_data=kwargs) # Pass args as input_data dictionary

    # Dynamically create the signature for the new function
    # The name of the dynamic function should be valid (e.g., tool_instance.name)
    # and often made "safe" (e.g. replace spaces or invalid chars)
    # AG2 uses the function.__name__ for registration.
    safe_func_name = tool_name.replace("-", "_").replace(" ", "_")


    # Create the function with the dynamic signature
    # Using a string definition and exec can be one way, but let's try to build it with `types.FunctionType`
    # For simplicity in this step, let's define a template and fill it.
    # A more robust solution might involve AST manipulation or more complex `inspect` usage.

    # Simpler approach: Define a wrapper and then set its __signature__ and __doc__
    # The actual call to tool.run will be handled by _execute_tool_wrapper
    
    @functools.wraps(execution_core) # This helps preserve some metadata but signature is key
    async def dynamic_tool_func(**kwargs):
        # This is where arguments passed by AG2 will arrive.
        # They should match the parameters defined in the signature.
        result = await tool_instance.run(input_data=kwargs)
        
        # Convert result to string format for AG2 conversation
        if isinstance(result, dict):
            # Format dictionary results as readable strings
            if result.get("success", True):
                # Success case - format the main content
                if "message" in result:
                    response = result["message"]
                    if "result" in result and result["result"]:
                        response += f"\nDetails: {result['result']}"
                    if "memories" in result and result["memories"]:
                        response += f"\nFound {len(result['memories'])} memories"
                        for i, memory in enumerate(result["memories"][:3], 1):  # Show first 3
                            content = memory.get('content', '')[:100]
                            response += f"\n{i}. {content}..."
                    return response
                else:
                    # Fallback for success without message
                    return f"Operation completed successfully: {result}"
            else:
                # Error case
                error_msg = result.get("error", "Unknown error occurred")
                return f"Error: {error_msg}"
        else:
            # Non-dictionary results (strings, etc.) pass through
            return str(result) if result is not None else "Operation completed"

    # Set the dynamic signature and docstring
    # Note: The name of the function is also important for AG2.
    # We can't easily change dynamic_tool_func.__name__ after definition without specific tricks.
    # AG2 typically expects the function to be registered with the name it will be called by.
    # So, the function object itself should ideally have the 'safe_func_name'.
    # One way is to use 'exec', but let's try to avoid it for now.
    # For AG2, when you register, you provide the function object. The name it's registered under
    # is what the LLM uses. The function object's internal __name__ is less critical for AG2's direct use
    # but good for introspection.

    sig = inspect.Signature(parameters=parameters)
    dynamic_tool_func.__signature__ = sig
    dynamic_tool_func.__doc__ = full_docstring
    # dynamic_tool_func.__name__ = safe_func_name # This is tricky to set directly on existing func

    # To ensure the function object has the correct name for registration if needed:
    # One common pattern is to create it via exec or to return a new function
    # compiled with the correct name.
    # For now, the object `dynamic_tool_func` will be registered.
    # The name used in `register_function` will be `safe_func_name`.

    return dynamic_tool_func

# Example of how to register (actual registration will be in the example script)
# def register_tool_with_agents(
#     tool_function: Callable,
#     tool_name_for_llm: str, # This is the name LLM will use
#     caller_agent: ConversableAgent,
#     executor_agent: ConversableAgent
# ):
#     caller_agent.register_function(
#         function_map={
#             tool_name_for_llm: executor_agent.register_for_execution(name=tool_name_for_llm)(tool_function)
#         }
#     )
#     # Alternative simpler registration if executor agent handles execution directly:
#     # register_function(
#     #    tool_function,
#     #    caller=caller_agent,
#     #    executor=executor_agent,
#     #    name=tool_name_for_llm, # Name for LLM
#     #    description=tool_instance.description # Description for LLM
#     # )
