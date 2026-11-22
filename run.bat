@echo off
REM QuantMaven — one-command local launch.
REM Creates a virtual environment on first run, installs dependencies, starts the app.
setlocal
cd /d "%~dp0"

set VENV=.venv
set PY=%VENV%\Scripts\python.exe

if not exist "%PY%" (
    echo Creating virtual environment...
    py -3.12 -m venv %VENV% 2>nul || py -3 -m venv %VENV% || python -m venv %VENV%
    if not exist "%PY%" (
        echo.
        echo Could not create a virtual environment. Is Python installed and on PATH?
        pause
        exit /b 1
    )
    "%PY%" -m pip install --upgrade pip
    echo Installing dependencies...
    "%PY%" -m pip install -r requirements.txt
)

echo.
echo Starting QuantMaven at http://localhost:8501
echo Press Ctrl+C to stop.
echo.
"%PY%" -m streamlit run QuantMaven.py --server.port 8501
endlocal
