@echo off
setlocal

set VENV_DIR=.venv

if exist %VENV_DIR%\Scripts\activate.bat (
    call %VENV_DIR%\Scripts\activate.bat
) else (
    echo Warning: Virtual environment not found at %VENV_DIR%. Running with system Python.
)

if "%~1"=="" (
    echo Usage: quick_editor.bat [MIDI_FILE]
    echo Opening empty editor...
    python Scripts/quick_editor.py
) else (
    python Scripts/quick_editor.py "%~1"
)

if errorlevel 1 (
    echo Error occurred.
    pause
)
