#!/bin/bash
# RoboCo API Server Launcher
#
# This script starts the RoboCo API server with configurable options.
# Usage: ./start.sh [OPTIONS]
#
# Options:
#   --host=HOST       Host to bind the server to (default: 127.0.0.1)
#   --port=PORT       Port to bind the server to (default: 8000)
#   --reload          Enable auto-reload on code changes
#   --workers=N       Number of worker processes (default: 1)
#   --help            Show this help message

# Default configuration
HOST="127.0.0.1"
PORT=8000
RELOAD=false
WORKERS=1

# Parse command line arguments
for arg in "$@"; do
  case $arg in
    --host=*)
      HOST="${arg#*=}"
      shift
      ;;
    --port=*)
      PORT="${arg#*=}"
      shift
      ;;
    --reload)
      RELOAD=true
      shift
      ;;
    --workers=*)
      WORKERS="${arg#*=}"
      shift
      ;;
    --help)
      echo "RoboCo API Server Launcher"
      echo ""
      echo "Usage: ./start.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --host=HOST       Host to bind the server to (default: 127.0.0.1)"
      echo "  --port=PORT       Port to bind the server to (default: 8000)"
      echo "  --reload          Enable auto-reload on code changes"
      echo "  --workers=N       Number of worker processes (default: 1)"
      echo "  --help            Show this help message"
      exit 0
      ;;
    *)
      # Unknown option
      echo "Unknown option: $arg"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Check if Python is available
if ! command -v python3 &> /dev/null; then
  echo "Error: python3 is not installed or not in PATH"
  exit 1
fi

# Check if uv is available
if ! command -v uv &> /dev/null; then
  echo "Error: uv is not installed or not in PATH"
  echo "Please install uv: https://github.com/astral-sh/uv"
  exit 1
fi

# Check if roboco is installed
if ! command -v roboco &> /dev/null; then
  echo "Installing RoboCo package in development mode..."
  uv pip install -e .
  
  # Double-check if installation succeeded
  if ! command -v roboco &> /dev/null; then
    echo "Warning: 'roboco' command not found after installation."
    echo "Using local module invocation as fallback."
    USE_LOCAL_MODULE=true
  fi
fi

# Build reload option
RELOAD_OPT=""
if [ "$RELOAD" = true ]; then
  RELOAD_OPT="--reload"
  # When reload is enabled, only 1 worker can be used
  WORKERS=1
fi

echo "Starting RoboCo API server..."
echo "URL: http://${HOST}:${PORT}"
echo "Reload mode: ${RELOAD}"
echo "Workers: ${WORKERS}"
echo ""
echo "Press Ctrl+C to stop the server"
echo "API documentation will be available at: http://${HOST}:${PORT}/docs"

# Start the server using the roboco CLI tool
if [ "$USE_LOCAL_MODULE" = true ]; then
  # Fallback to module invocation if CLI command not available
  python3 -m roboco.cli server --host "$HOST" --port "$PORT" --workers "$WORKERS" $RELOAD_OPT
else
  # Use the CLI command directly
  roboco server --host "$HOST" --port "$PORT" --workers "$WORKERS" $RELOAD_OPT
fi 