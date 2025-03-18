@echo off
REM Script to set up roboco project with uv after transitioning from Poetry on Windows

REM Install uv if not already installed
where uv >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing uv...
    pip install uv
)

REM Create virtual environment
echo Creating virtual environment...
uv venv

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install package in development mode with all dependencies
echo Installing package dependencies...
uv pip install -e .

REM Install development dependencies
echo Installing development dependencies...
uv pip install -e .[dev]

REM Install browser dependencies if requested
set /p BROWSER="Do you want to install browser automation dependencies? (y/n) "
if /i "%BROWSER%"=="y" (
    echo Installing browser automation dependencies...
    uv pip install -e .[browser]
    
    REM Install Playwright browsers
    echo Installing Playwright browsers...
    playwright install chromium
)

echo.
echo Setup complete! To activate the environment in the future, run:
echo .venv\Scripts\activate.bat
echo.
echo To run an example:
echo python examples/market_research/main.py --query "Your research query"

pause 