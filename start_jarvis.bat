@echo off
cd /d "%~dp0"

:: Check if user passed CLI flags
if "%1"=="--cli" goto CLI
if "%1"=="-c" goto CLI
if "%1"=="--voice" goto CLI
if "%1"=="-v" goto CLI
if "%1"=="--doctor" goto CLI
if "%1"=="-q" goto CLI
if "%1"=="--query" goto CLI

:: Default GUI launch: Run without persistent background terminal window
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" main.py %*
    exit /b 0
)
if exist ".venv\Scripts\python.exe" (
    start "" ".venv\Scripts\python.exe" main.py %*
    exit /b 0
)
start "" pythonw main.py %* 2>nul || python main.py %*
exit /b 0

:CLI
title J.A.R.V.I.S. AI Assistant
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)
python main.py %*
if errorlevel 1 (
    echo.
    echo J.A.R.V.I.S. encountered an issue. Press any key to exit.
    pause >nul
)
