@echo off
cd /d %~dp0

echo ===================================================
echo  Force Re-installing MIDI Dictionary Environment
echo ===================================================
echo.
echo This will delete the existing '.venv' folder and re-install everything.
echo.

if exist .venv (
    echo Deleting existing .venv...
    rmdir /s /q .venv
    
    if exist .venv (
        echo.
        echo [ERROR] Could not delete '.venv' folder.
        echo Please close any running MIDI Dictionary windows or terminals using it.
        echo Then try again.
        echo.
        pause
        exit /b 1
    )
    echo Deleted old environment.
)

echo.
echo Re-running setup script...
call setup_and_run.bat
