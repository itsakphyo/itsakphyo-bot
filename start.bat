@echo off
REM Development start script for Windows

echo Starting Itsakphyo Bot in development mode...

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Check if .env exists
if not exist ".env" (
    echo Creating .env from example...
    copy .env.example .env
    echo Please edit .env with your bot token and configuration
    pause
    exit /b 1
)

REM Create logs directory
if not exist "logs" mkdir logs

REM Start the application
echo Starting application...
python main.py

pause
