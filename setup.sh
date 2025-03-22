#!/bin/bash
#
# RoboCo Setup Script
# This script sets up the development environment for RoboCo
#

# Exit on error
set -e

# Display welcome message
echo "===== RoboCo Setup Script ====="
echo "Setting up development environment..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv package manager..."
    curl -fsS https://raw.githubusercontent.com/astral-sh/uv/main/install.sh | bash
    # Update PATH to include ~/.cargo/bin
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv -p 3.10
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
uv pip install -e ".[dev]"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Please edit .env file to add your API keys."
fi

echo "===== Setup Complete! ====="
echo ""
echo "To activate the environment:"
echo "  source .venv/bin/activate"
echo ""
echo "To run an example:"
echo "  python examples/test_config.py"
echo "" 