@echo off
cd /d %~dp0
python auto_demucs.py %*
pause