#!/bin/bash
# Simple script to run roboco examples

# No need to load .env anymore since all configs are in config.toml

# If no arguments provided, default to web browsing example
if [ $# -eq 0 ]; then
  # Run web browsing example
  echo "Running web browsing example..."
  python examples/web_surf/main.py
  exit 0
fi

EXAMPLE=$1

case $EXAMPLE in
  team)
    echo "Running team chat example..."
    python examples/team_chat/main.py
    ;;
  web)
    echo "Running web browsing example..."
    python examples/web_surf/main.py
    ;;
  market)
    echo "Running market research example..."
    python examples/market_research/main.py
    ;;
  *)
    echo "Unknown example: $EXAMPLE"
    echo "Available examples: team, web, market"
    echo "Running default web browsing example instead..."
    python examples/web_surf/main.py
    ;;
esac 