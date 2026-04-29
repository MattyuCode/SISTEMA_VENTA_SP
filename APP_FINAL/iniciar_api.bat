@echo off

cd /d "%~dp0API_WhatsApp"

start "" cmd /c ""%~dp0node\node.exe" app.js >nul 2>&1"

timeout /t 5 >nul

cd /d "%~dp0"

start "" SISTEMA_SP.exe

exit