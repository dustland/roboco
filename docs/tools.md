# RoboCo Tools

This document provides an overview of the tools available in RoboCo for agent interaction with various systems.

## Core Tools

RoboCo includes a variety of built-in tools that agents can use to interact with the environment, perform research, and execute actions.

### FileSystemTool

The FileSystemTool provides capabilities for reading, writing, and managing files and directories.

```python
from roboco.tools import FileSystemTool

fs_tool = FileSystemTool()

# Register with an agent
agent.register_tool(fs_tool)
```

#### Key Functions

- `read_file(path: str) -> str`: Read the contents of a file
- `write_file(path: str, content: str) -> bool`: Write content to a file
- `list_directory(path: str) -> List[str]`: List contents of a directory
- `create_directory(path: str) -> bool`: Create a new directory

### BrowserUseTool

The BrowserUseTool enables web browsing with a fallback mechanism that ensures reliable web access.

```python
from roboco.tools import BrowserUseTool

browser_tool = BrowserUseTool(output_dir="./browser_output")

# Register with an agent
agent.register_tool(browser_tool)
```

#### Key Functions

- `browse(url: str) -> str`: Navigate to a URL and retrieve the page content
- `extract_links(url: str) -> List[str]`: Extract all links from a web page
- `search_page(url: str, query: str) -> str`: Search for specific content on a page

### WebSearchTool

The WebSearchTool provides integration with search engines to find information on the web.

```python
from roboco.tools import WebSearchTool

web_search_tool = WebSearchTool(api_key="your-search-api-key")

# Register with an agent
agent.register_tool(web_search_tool)
```

#### Key Functions

- `search(query: str, num_results: int = 5) -> List[Dict]`: Perform a web search
- `search_news(query: str, num_results: int = 5) -> List[Dict]`: Search news articles

### ArxivTool

The ArxivTool enables research of scientific papers on the arXiv repository.

```python
from roboco.tools import ArxivTool

arxiv_tool = ArxivTool(max_results=5)

# Register with an agent
agent.register_tool(arxiv_tool)
```

#### Key Functions

- `search_arxiv(query: str, max_results: int = 5) -> List[Dict]`: Search arXiv papers
- `download_paper(paper_id: str, output_dir: str = None) -> str`: Download a paper
- `get_paper_metadata(paper_id: str) -> Dict`: Get metadata for a paper

### GitHubTool

The GitHubTool provides integration with GitHub repositories for code analysis and collaboration.

```python
from roboco.tools import GitHubTool

github_tool = GitHubTool(token="your-github-token")

# Register with an agent
agent.register_tool(github_tool)
```

#### Key Functions

- `search_repositories(query: str, language: str = None) -> List[Dict]`: Search GitHub repositories
- `get_repository(owner: str, repo: str) -> Dict`: Get repository information
- `get_file_content(owner: str, repo: str, path: str) -> str`: Get file content
- `search_code(query: str, language: str = None) -> List[Dict]`: Search code on GitHub

### GenesisTool

The GenesisTool enables physics simulations through the Genesis physics engine.

```python
from roboco.tools import GenesisTool

genesis_tool = GenesisTool(genesis_executable="/path/to/genesis")

# Register with an agent
agent.register_tool(genesis_tool)
```

#### Key Functions

- `run_simulation(simulation_code: str) -> Dict`: Run a physics simulation
- `get_world_info() -> Dict`: Get information about the current simulation world
- `create_basic_simulation() -> str`: Create a template for a basic simulation

### TerminalTool

The TerminalTool allows execution of shell commands for system interaction.

```python
from roboco.tools import TerminalTool

terminal_tool = TerminalTool()

# Register with an agent
agent.register_tool(terminal_tool)
```

#### Key Functions

- `execute_command(command: str) -> str`: Execute a shell command
- `get_environment_variable(name: str) -> str`: Get an environment variable
- `set_environment_variable(name: str, value: str) -> bool`: Set an environment variable

### RunTool

The RunTool enables execution of code in various programming languages.

```python
from roboco.tools import RunTool

run_tool = RunTool(supported_languages=["python", "javascript"])

# Register with an agent
agent.register_tool(run_tool)
```

#### Key Functions

- `run_python(code: str) -> str`: Execute Python code
- `run_javascript(code: str) -> str`: Execute JavaScript code

## Creating Custom Tools

You can create custom tools by extending the base `Tool` class:

```python
from roboco.core import Tool

class MyCustomTool(Tool):
    def __init__(self, name="CustomTool", **kwargs):
        super().__init__(name=name, **kwargs)

    def register_functions(self):
        @self.register_function
        async def custom_function(param1: str, param2: int) -> str:
            """
            Custom function description

            Args:
                param1: Description of param1
                param2: Description of param2

            Returns:
                Result description
            """
            # Implementation
            return f"Result: {param1}, {param2}"
```

## Tool Configuration

Tools can be configured through the configuration system:

```yaml
# config/tools.yaml
tools:
  browser:
    output_dir: "./browser_output"
    timeout: 30

  github:
    token: "${GITHUB_TOKEN}"
    cache_dir: "./github_cache"
```

## Tool Execution

Tools can be executed by agents that have access to them:

```python
# Register a tool with an agent
agent.register_tool(web_search_tool)

# Agents can use tools in their conversations
result = await agent.initiate_chat(
    recipient=another_agent,
    message="Find information about quantum computing."
)
```

For more details on specific tools, refer to their respective documentation in the API Reference.
