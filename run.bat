@echo off
cd /d %~dp0

rem もし .venv (仮想環境) があるなら有効化する
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat

echo Starting...
python Scripts/main.py

rem エラー終了した時だけ画面を残す
if errorlevel 1 pause
