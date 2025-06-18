#!/bin/bash

# Preview Documentation Script
# This script builds and serves the documentation locally

echo "🔧 AgentX Documentation Preview"
echo "==============================="

# Check if mkdocs is installed
if ! command -v mkdocs &> /dev/null; then
    echo "❌ MkDocs not found. Installing..."
    pip install mkdocs-material mkdocstrings[python]
fi

# Navigate to project root
cd "$(dirname "$0")/.."

# Start the development server
echo "🚀 Starting documentation server..."
echo "📖 Open http://127.0.0.1:8000 in your browser"
echo "🔄 Press Ctrl+C to stop the server"
echo ""

mkdocs serve --dev-addr 127.0.0.1:8000 