@echo off
title Sofzenix HackFest — Starting Server
color 0B
echo.
echo   ========================================
echo     SOFZENIX HACKFEST — SERVER STARTUP
echo   ========================================
echo.

:: Check if .env exists
IF NOT EXIST backend\.env (
    echo   [SETUP] Creating .env from example...
    copy backend\.env.example backend\.env
    echo   [SETUP] Please edit backend\.env with your MySQL password and settings!
    echo   Opening .env for editing...
    notepad backend\.env
    pause
)

:: Check Python
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo   [ERROR] Python is not installed or not in PATH.
    echo   Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Install dependencies
echo   [SETUP] Installing Python dependencies...
cd backend
pip install -r requirements.txt --quiet
IF ERRORLEVEL 1 (
    echo   [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo   ========================================
echo   [READY] Sofzenix HackFest is starting!
echo   Open your browser at: http://localhost:5000
echo   Admin Panel: http://localhost:5000/admin.html
echo   ========================================
echo.

python app.py
pause
