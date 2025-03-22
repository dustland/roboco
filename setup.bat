@echo off
REM RoboCo Setup Script
REM This script sets up the development environment for RoboCo

echo ===== RoboCo Setup Script =====
echo Setting up development environment...

REM Check if uv is installed
where uv >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Installing uv package manager...
    powershell -Command "Invoke-WebRequest -useb https://astral.sh/uv/install.ps1 | Invoke-Expression"
    REM Add uv to path for this session
    set PATH=%USERPROFILE%\.cargo\bin;%PATH%
)

REM Create virtual environment if it doesn't exist
if not exist .venv (
    echo Creating virtual environment...
    uv venv -p 3.10
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate

REM Install dependencies
echo Installing dependencies...
uv pip install -e .[dev]

REM Create .env file if it doesn't exist
if not exist .env (
    echo Creating .env file from example...
    copy .env.example .env
    echo Please edit .env file to add your API keys.
)

echo ===== Setup Complete! =====
echo.
echo To activate the environment:
echo   .venv\Scripts\activate
echo.
echo To run an example:
echo   python examples\test_config.py
echo. 