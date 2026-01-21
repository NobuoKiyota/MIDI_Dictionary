@echo off
cd /d %~dp0

:: pythonw を使うことで黒い画面を出さずに起動します
start "" pythonw app.py

exit