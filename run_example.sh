#!/bin/bash
# Simple script to run roboco examples

# No need to load .env anymore since all configs are in config.toml

# Default to running the web_surf example if no arguments are provided
if [ -z "$1" ]; then
  echo "Running default example (web browsing)..."
  
  # Check if virtual environment is active
  if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
  fi
  
  python examples/tool/web_surf.py
  exit 0
fi

# Otherwise run the specified example
example="$1"
shift

echo "Running example: $example"

# Check if virtual environment is active
if [ -z "$VIRTUAL_ENV" ]; then
  echo "Activating virtual environment..."
  source .venv/bin/activate
fi

if [ -f "examples/$example/main.py" ]; then
  python "examples/$example/main.py" "$@"
elif [ -f "examples/$example.py" ]; then
  python "examples/$example.py" "$@"
elif [ -f "examples/tool/$example.py" ]; then
  python "examples/tool/$example.py" "$@"
else
  echo "Error: Example not found: $example"
  echo "Available examples:"
  find examples -name "*.py" | grep -v "__" | sort
  exit 1
fi 