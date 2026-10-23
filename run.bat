@echo off
cd /d "%~dp0"
start "" pythonw.exe app.py
if %errorlevel% neq 0 (
    start "" python.exe app.py
)
