"""
CLI commands for tool management and discovery.
"""

import click
from ..tool.registry import validate_agent_tools, suggest_tools_for_agent, list_tools, print_available_tools
from ..builtin_tools.web_tools import WebTool
from ..builtin_tools.search_tools import SearchTool
from ..tool.registry import register_tool
from ..utils.logger import get_logger

logger = get_logger(__name__)


@click.group()
def tools():
    """Tool management commands."""
    pass


@tools.command()
def list():
    """List all available tools with descriptions."""
    # Register built-in tools first
    _register_builtin_tools()
    print_available_tools()


@tools.command()
@click.argument('tool_names', nargs=-1)
def validate(tool_names):
    """Validate tool names against available tools."""
    if not tool_names:
        click.echo("Usage: agentx tools validate <tool_name1> <tool_name2> ...")
        return
    
    _register_builtin_tools()
    valid, invalid = validate_agent_tools(list(tool_names))
    
    if valid:
        click.echo(f"✅ Valid tools: {', '.join(valid)}")
    
    if invalid:
        click.echo(f"❌ Invalid tools: {', '.join(invalid)}")
        click.echo("\nRun 'agentx tools list' to see available tools")


@tools.command()
@click.argument('agent_name')
@click.option('--description', '-d', default="", help="Agent description for better suggestions")
def suggest(agent_name, description):
    """Suggest relevant tools for an agent based on name and description."""
    _register_builtin_tools()
    suggestions = suggest_tools_for_agent(agent_name, description)
    
    if suggestions:
        click.echo(f"Suggested tools for '{agent_name}':")
        for tool in suggestions:
            click.echo(f"  - {tool}")
        
        click.echo(f"\nYAML config example:")
        click.echo(f"agents:")
        click.echo(f"  - name: {agent_name}")
        click.echo(f"    tools:")
        for tool in suggestions:
            click.echo(f"      - {tool}")
    else:
        click.echo(f"No specific tool suggestions for '{agent_name}'")
        click.echo("Run 'agentx tools list' to see all available tools")


def _register_builtin_tools():
    """Register built-in tools for CLI commands."""
    try:
        # Register built-in tools
        web_tool = WebTool()
        search_tool = SearchTool()
        
        register_tool(web_tool)
        register_tool(search_tool)
    except Exception as e:
        # Tools might already be registered or have dependency issues
        pass


if __name__ == '__main__':
    tools() 