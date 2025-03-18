# Roboco Examples

This directory contains example scripts demonstrating how to use the Roboco system.

## Directory Structure

Each example is organized in its own directory with a consistent structure:

```
examples/
├── example_name/
│   ├── main.py         # Main entry point for the example
│   ├── README.md       # Documentation for the example
│   └── ...             # Additional files specific to the example
```

## Available Examples

### Team Chat

The `team_chat` directory contains an example of how to use the Roboco system to create a team of agents and initiate a chat with automatic handoffs between them.

```bash
# Run the team chat example
python examples/team_chat/main.py
```

### Web Surf

The `web_surf` directory contains an example of how to use the Roboco system to perform web research using the BrowserTool.

```bash
# Run the web surf example
python examples/web_surf/main.py
```

### Market Research

The `market_research` directory contains examples of how to use the Roboco system for market research. It demonstrates how to use the various agents to generate comprehensive market research reports.

```bash
# Run market research with swarm orchestration
python examples/market_research/main.py --query "Your research query here"

# Run market research with direct research approach
python examples/market_research/main.py --query "Your research query here" --direct

# Run market research with browser capabilities
python examples/market_research/main.py --query "Your research query here" --direct --browser-type browser-use
```

## Requirements

Different examples may have different requirements. Please refer to the README.md file in each example directory for specific requirements.

### Browser Automation Dependencies

For examples that use browser capabilities:

```bash
# Install browser-use and playwright
uv pip install "ag2[browser-use]"
uv pip install playwright

# Install browser engines
playwright install

# Install system dependencies (Linux only)
playwright install-deps
```

## Standard Command Format

Most examples can be run using:

```bash
python examples/<example_name>/main.py [options]
```

For more detailed instructions, refer to the README.md file in each example directory.
