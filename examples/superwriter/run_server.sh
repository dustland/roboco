#!/bin/bash
# This script launches the SuperWriter FastAPI server.

# Change to the directory where this script is located to ensure correct paths
cd "$(dirname "$0")"

echo "--- Setting up SuperWriter Environment ---"

# Ensure dependencies are installed using the project's requirements file
# We point to the root requirements.txt file
echo "Installing dependencies from requirements.txt..."
if uv pip install -r ../../requirements.txt; then
    echo "Dependencies are up to date."
else
    echo "Failed to install dependencies. Please check requirements.txt and your uv setup."
    exit 1
fi


echo "\n--- Starting SuperWriter API Server ---"
echo "API will be available at http://127.0.0.1:8000"
echo "View the API docs at http://127.0.0.1:8000/docs"
echo "Press CTRL+C to stop the server."

# Run the server using uvicorn, managed by uv
# --reload will watch for file changes in the current directory and restart the server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
