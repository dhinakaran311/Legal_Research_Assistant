@echo off
REM Batch script to start AI Engine server
REM This sets up the Python path correctly

set PYTHONPATH=%CD%\src
cd /d %~dp0

echo Starting AI Engine server...
echo Python Path: %PYTHONPATH%

REM Activate virtual environment if it exists
if exist .ven\Scripts\activate.bat (
    echo Activating virtual environment...
    call .ven\Scripts\activate.bat
)

REM Run uvicorn
python -m uvicorn src.main:app --host 0.0.0.0 --port 5000 --reload
