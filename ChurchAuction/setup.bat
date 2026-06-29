@echo off
echo ============================================
echo  Church Auction - First-Time Setup
echo ============================================
echo.

REM Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed.
    echo.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo Then run this setup again.
    echo.
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

REM Create virtual environment
echo Setting up virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment.
    pause
    exit /b 1
)

REM Install dependencies
echo.
echo Installing dependencies (this may take a minute)...
.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
.venv\Scripts\pip.exe install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

REM Create data folder
if not exist data mkdir data

echo.
echo ============================================
echo  Setup complete!
echo ============================================
echo.
echo To start the auction, double-click start-auction.bat
echo.
pause
