@echo off
chcp 65001 >nul
echo ========================================
echo   TVBox Source Studio - Environment Setup
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

echo [INFO] Python version check passed
python --version
echo.

REM Create virtual environment
if not exist "%~dp0venv" (
    echo [INFO] Creating virtual environment...
    python -m venv "%~dp0venv"
    echo [SUCCESS] Virtual environment created
) else (
    echo [INFO] Virtual environment already exists
)
echo.

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call "%~dp0venv\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [SUCCESS] Virtual environment activated
echo.

REM Install dependencies
echo [INFO] Installing dependencies...
set REQUIREMENTS_FILE="%~dp0config\requirements.txt"
if exist %REQUIREMENTS_FILE% (
    pip install -r %REQUIREMENTS_FILE%
) else (
    set REQUIREMENTS_FILE="%~dp0requirements.txt"
    if exist %REQUIREMENTS_FILE% (
        pip install -r %REQUIREMENTS_FILE%
    ) else (
        echo [ERROR] requirements.txt not found
        pause
        exit /b 1
    )
)

if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Run: start.bat
echo   2. Or manually:
echo      .\venv\Scripts\activate
echo      python src\app.py
echo.
echo Config file: config\.env
echo ========================================
echo.
pause
