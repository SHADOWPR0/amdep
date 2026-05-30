@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  .venv\Scripts\pip.exe install -r requirements.txt
)
.venv\Scripts\python.exe -m amdep.field_kit
