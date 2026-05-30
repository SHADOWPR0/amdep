@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_CMD="

where py >nul 2>nul
if not errorlevel 1 (
  py -3.11 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=py -3.11"
  if not defined PYTHON_CMD (
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=py -3"
  )
)

if not defined PYTHON_CMD (
  where python >nul 2>nul
  if not errorlevel 1 (
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=python"
  )
)

if not defined PYTHON_CMD (
  echo.
  echo AMDEP Field Kit needs Python 3.11 or newer.
  echo.
  echo Install Python from:
  echo   https://www.python.org/downloads/windows/
  echo.
  echo During install, check "Add python.exe to PATH" if shown.
  echo Then double-click run_field_kit.bat again.
  echo.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  %PYTHON_CMD% -m venv .venv
  if errorlevel 1 goto fail
  .venv\Scripts\python.exe -m pip install --upgrade pip
  if errorlevel 1 goto fail
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  if errorlevel 1 goto fail
)
.venv\Scripts\python.exe -m amdep.field_kit
if errorlevel 1 goto fail
exit /b 0

:fail
echo.
echo AMDEP Field Kit could not start. If this is a company machine, IT may need to allow Python package installation from requirements.txt.
echo.
pause
exit /b 1
