#!/bin/bash
# Script to set up roboco project with uv after transitioning from Poetry

# Check if this script is running with bash
if [ -z "$BASH_VERSION" ]; then
    echo "This script must be run with bash"
    exit 1
fi

# Check if we're already in a virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    echo "Already in a virtual environment: $VIRTUAL_ENV"
    
    # Install uv if not already installed
    if ! command -v uv &> /dev/null; then
        echo "Installing uv in current environment..."
        python -m pip install uv
    else
        echo "uv is already installed."
    fi
else
    # Install uv if not already installed
    if ! command -v uv &> /dev/null; then
        echo "Installing uv..."
        python -m pip install uv
    fi

    # Create virtual environment
    echo "Creating virtual environment..."
    uv venv

    # Activate virtual environment
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Verify we have uv available now
if ! command -v uv &> /dev/null; then
    echo "Error: uv command not found. Please install uv manually with: python -m pip install uv"
    exit 1
fi

# Install package in development mode with all dependencies
echo "Installing package dependencies..."
uv pip install -e .

# Install development dependencies
echo "Installing development dependencies..."
uv pip install -e ".[dev]"

# Install browser dependencies if requested
read -p "Do you want to install browser automation dependencies? (y/n) " BROWSER
if [[ $BROWSER == "y" || $BROWSER == "Y" ]]; then
    echo "Installing browser automation dependencies..."
    uv pip install -e ".[browser]"
    
    # Install Playwright browsers
    echo "Installing Playwright browsers..."
    playwright install chromium
    
    # Install system dependencies if on Linux
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        read -p "Do you want to install Playwright system dependencies (requires sudo)? (y/n) " SYSDEPS
        if [[ $SYSDEPS == "y" || $SYSDEPS == "Y" ]]; then
            playwright install-deps
        fi
    fi
fi

echo ""
echo "Setup complete! To activate the environment in the future, run:"
echo "source .venv/bin/activate"
echo ""
echo "To run an example:"
echo "python examples/market_research/main.py --query \"Your research query\"" 