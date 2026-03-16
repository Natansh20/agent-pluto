@echo off
cd /d "%~dp0"

REM Try venv python first, fall back to system python
if exist "ai_agent\Scripts\pythonw.exe" (
    start "" "ai_agent\Scripts\pythonw.exe" agent_ui.py
) else (
    start "" pythonw agent_ui.py
)