#!/bin/bash
# Setup script for Roboco workspace directory structure

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Setting up Roboco workspace...${NC}"

# Create essential directories
directories=(
  "workspace"
  "workspace/data"
  "workspace/models"
  "workspace/outputs"
  "workspace/logs"
  "workspace/cache"
  "workspace/configs"
  "user_data"
  "user_data/profiles"
)

for dir in "${directories[@]}"; do
  if [ ! -d "$dir" ]; then
    mkdir -p "$dir"
    echo -e "${GREEN}Created directory:${NC} $dir"
  else
    echo -e "${YELLOW}Directory already exists:${NC} $dir"
  fi
done

# Create .gitkeep files to preserve directory structure in git
for dir in "${directories[@]}"; do
  if [ ! -f "$dir/.gitkeep" ]; then
    touch "$dir/.gitkeep"
    echo -e "${GREEN}Created .gitkeep in:${NC} $dir"
  fi
done

# Create a default config file if it doesn't exist
if [ ! -f "config/config.yaml" ]; then
  mkdir -p config
  cat > config/config.yaml << EOF
# Roboco default configuration
company:
  name: "Roboco Robotics Corporation"
  description: "AI-Powered Robotics Development Platform"

core:
  workspace_root: "./workspace"
  debug: false

llm:
  model: "gpt-4"
  api_key: "\${OPENAI_API_KEY}"
  temperature: 0.7
  max_tokens: 4000
  
server:
  host: "127.0.0.1"
  port: 8000
  workers: 4
  
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  console: true
EOF
  echo -e "${GREEN}Created default config file:${NC} config/config.yaml"
else
  echo -e "${YELLOW}Config file already exists:${NC} config/config.yaml"
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
  cat > .env << EOF
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here
EOF
  echo -e "${GREEN}Created .env file${NC}"
  echo -e "${YELLOW}Don't forget to add your API keys to the .env file${NC}"
else
  echo -e "${YELLOW}.env file already exists${NC}"
fi

echo -e "${BLUE}Workspace setup complete!${NC}"
echo -e "${BLUE}To get started:${NC}"
echo -e "1. Add your API keys to the .env file"
echo -e "2. Activate your virtual environment"
echo -e "3. Run your first example with: python examples/web_surf/main.py" 