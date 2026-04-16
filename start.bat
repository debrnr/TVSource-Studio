@echo off
chcp 65001 >nul

echo ========================================
echo   TVBox Source Studio
echo   TVBox Source Aggregation Service
echo ========================================
echo.

REM Check virtual environment
if not exist "venv" (
    echo [ERROR] Virtual environment not found
    echo Please run: activate_env.bat
    pause
    exit /b 1
)

REM Check main program
if not exist "src\app.py" (
    echo [ERROR] src\app.py not found
    pause
    exit /b 1
)

REM Check config file
if exist "config\.env" (
    echo [INFO] Using config file: config\.env
) else if exist ".env" (
    echo [INFO] Using config file: .env (legacy)
) else (
    echo [WARNING] No .env file found, using defaults
)

echo.
echo [INFO] Starting service...
echo [INFO] Access URL: http://localhost:8080
echo [INFO] Press Ctrl+C to stop
echo.
echo ========================================
echo.

REM Start service
.\venv\Scripts\python.exe src\app.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Service failed to start
    pause
    exit /b 1
)
