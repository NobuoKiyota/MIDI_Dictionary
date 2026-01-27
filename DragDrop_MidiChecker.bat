@echo off
setlocal
cd /d "%~dp0"

echo [Debug] Starting MIDI Checker
echo [Debug] Current Directory: %CD%

set "PYTHON_EXE=.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [Error] Python executable not found at: %PYTHON_EXE%
    echo Please ensure the setup_and_run.bat has been run successfully.
    pause
    exit /b 1
)

echo [Info] Found Python at: %PYTHON_EXE%
echo [Info] Launching Script...

"%PYTHON_EXE%" "Scripts\midi_checker.py" "%~1"

if %errorlevel% neq 0 (
    echo [Error] Execution failed with code %errorlevel%.
    pause
    exit /b %errorlevel%
)

echo [Success] Application finished.
pause
