@echo off
cd /d "%~dp0"
call .venv\Scripts\activate
python style_trainer.py
pause
