from typing import Any, Dict, AsyncGenerator, Type, Optional, List

from pydantic import BaseModel, Field

from roboco.tool.interfaces import AbstractTool
from roboco.config.models import ToolParameterConfig

class EchoToolParams(BaseModel):
    """Parameters for invoking the EchoTool."""
    message: str = Field(..., description="The message to be echoed back.")
    prefix: str = Field(default="", description="An optional prefix to add to the echoed message at invocation time.")

class EchoToolInstanceConfig(BaseModel):
    """Configuration parameters for an instance of EchoTool."""
    name: str = Field(default="echo_tool", description="The name of this tool instance.")
    description: str = Field(default="Echoes back a message.", description="The description of this tool instance.")
    default_prefix: str = Field(default="", description="A default prefix configured on the tool instance itself, used if no prefix is provided at invocation.")

class EchoTool(AbstractTool):
    """
    A simple tool that echoes back a message, potentially with a prefix.
    The tool's behavior can be customized via instance configuration (e.g., a default prefix)
    and invocation parameters (e.g., the message and an overriding prefix).
    """
    _name: str
    _description: str
    _default_prefix: str

    def __init__(self, name: str = "echo_tool", description: str = "Echoes back a message.", default_prefix: str = ""):
        self._name = name
        self._description = description
        self._default_prefix = default_prefix

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @classmethod
    def get_config_schema(cls) -> Optional[Type[BaseModel]]:
        return EchoToolInstanceConfig

    def get_invocation_schema(self) -> List[ToolParameterConfig]:
        """Return the schema for tool invocation parameters."""
        return [
            ToolParameterConfig(
                name="message",
                type="string",
                description="The message to be echoed back.",
                required=True
            ),
            ToolParameterConfig(
                name="prefix",
                type="string",
                description="An optional prefix to add to the echoed message at invocation time.",
                required=False,
                default=""
            )
        ]

    async def run(self, **kwargs: Any) -> Dict[str, Any]:
        params = EchoToolParams(**kwargs)
        prefix_to_use = params.prefix if params.prefix else self._default_prefix
        result = f"{prefix_to_use}{params.message}"
        return {"echoed_message": result, "status": "success"}

    async def stream(self, **kwargs: Any) -> AsyncGenerator[Dict[str, Any], None]:
        params = EchoToolParams(**kwargs)
        prefix_to_use = params.prefix if params.prefix else self._default_prefix
        
        if prefix_to_use:
            yield {"type": "prefix", "content": prefix_to_use, "is_final": False}
        
        if params.message:
            yield {"type": "message_part", "content": params.message, "is_final": False}
        
        final_echoed_message = f"{prefix_to_use}{params.message}"
        yield {"type": "final_result", "full_echo": final_echoed_message, "status": "success", "is_final": True}
