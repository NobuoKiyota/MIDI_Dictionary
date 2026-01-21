@echo off
cd /d %~dp0

echo ライブラリをインストールしています...
pip install pytesseract Pillow

echo.
echo インストールが完了しました。
pause