@echo off
:: Setup script for Roboco workspace directory structure

echo Setting up Roboco workspace...

:: Create essential directories
set directories=^
workspace ^
workspace\data ^
workspace\models ^
workspace\outputs ^
workspace\logs ^
workspace\cache ^
workspace\configs ^
user_data ^
user_data\profiles

for %%d in (%directories%) do (
    if not exist "%%d" (
        mkdir "%%d"
        echo Created directory: %%d
    ) else (
        echo Directory already exists: %%d
    )
)

:: Create .gitkeep files to preserve directory structure in git
for %%d in (%directories%) do (
    if not exist "%%d\.gitkeep" (
        type nul > "%%d\.gitkeep"
        echo Created .gitkeep in: %%d
    )
)

:: Create a default config file if it doesn't exist
if not exist "config\config.yaml" (
    if not exist "config" mkdir config
    (
        echo # Roboco default configuration
        echo company:
        echo   name: "Roboco Robotics Corporation"
        echo   description: "AI-Powered Robotics Development Platform"
        echo.
        echo core:
        echo   workspace_root: "./workspace"
        echo   debug: false
        echo.
        echo llm:
        echo   model: "gpt-4"
        echo   api_key: "${OPENAI_API_KEY}"
        echo   temperature: 0.7
        echo   max_tokens: 4000
        echo.  
        echo server:
        echo   host: "127.0.0.1"
        echo   port: 8000
        echo   workers: 4
        echo.  
        echo logging:
        echo   level: "INFO"
        echo   format: "%%^(asctime^)s - %%^(name^)s - %%^(levelname^)s - %%^(message^)s"
        echo   console: true
    ) > "config\config.yaml"
    echo Created default config file: config\config.yaml
) else (
    echo Config file already exists: config\config.yaml
)

:: Create .env file if it doesn't exist
if not exist ".env" (
    (
        echo # OpenAI API Configuration
        echo OPENAI_API_KEY=your_openai_api_key_here
    ) > ".env"
    echo Created .env file
    echo Don't forget to add your API keys to the .env file
) else (
    echo .env file already exists
)

echo.
echo Workspace setup complete!
echo To get started:
echo 1. Add your API keys to the .env file
echo 2. Activate your virtual environment
echo 3. Run your first example with: python examples/tool/web_surf.py

pause 