# Roboco Examples

This directory contains example scripts demonstrating how to use the Roboco system.

## Market Research

The `market_research` directory contains examples of how to use the Roboco system for market research. It demonstrates how to use the various agents to generate comprehensive market research reports.

### Usage

```bash
# Run market research with swarm orchestration
python -m examples.market_research.main --query "Your research query here"

# Run market research with direct research approach
python -m examples.market_research.main --query "Your research query here" --direct

# Run market research with browser capabilities
python -m examples.market_research.main --query "Your research query here" --direct --browser-type browser-use
```

### Requirements

To run the market research examples, you need to install the following dependencies:

```bash
# Using Poetry (recommended)
poetry add "ag2[browser-use]"  # For browser-use

# Install Playwright
poetry run playwright install
# For Linux only
poetry run playwright install-deps

# Install nest_asyncio for Jupyter notebooks
poetry add nest_asyncio
```
