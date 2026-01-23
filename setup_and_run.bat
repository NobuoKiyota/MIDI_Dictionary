@echo off
setlocal

set VENV_DIR=.venv

if exist %VENV_DIR%\Scripts\activate.bat (
    echo Virtual environment found. Activating...
    call %VENV_DIR%\Scripts\activate.bat
    if errorlevel 1 (
        echo Error: Failed to activate virtual environment.
        echo Please try deleting the '%VENV_DIR%' folder and running this script again.
        pause
        exit /b 1
    )
    
    echo Checking for new dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Warning: Failed to install/update dependencies.
    )
) else (
    echo Creating virtual environment...
    python -m venv %VENV_DIR%
    if errorlevel 1 (
        echo Error: Failed to create virtual environment. 
        echo Please ensure Python is installed and added to PATH.
        pause
        exit /b 1
    )
    
    call %VENV_DIR%\Scripts\activate.bat
    
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install dependencies.
        echo Please check your internet connection or delete '%VENV_DIR%' and try again.
        pause
        exit /b 1
    )
)

echo Starting MIDI Dictionary...
python main.py

if errorlevel 1 (
    echo.
    echo ========================================================
    echo  An error occurred while running the application.
    echo  Error Code: %errorlevel%
    echo ========================================================
    pause
)
