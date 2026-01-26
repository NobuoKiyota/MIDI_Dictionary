@echo off
setlocal

set VENV_DIR=.venv

if exist %VENV_DIR%\Scripts\activate.bat (
    call %VENV_DIR%\Scripts\activate.bat
) else (
    echo [INFO] Virtual environment not found. Using system Python.
)

python Launcher.py

if errorlevel 1 (
    echo.
    echo Application exited with error.
    pause
)
