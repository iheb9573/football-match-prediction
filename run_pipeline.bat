@echo off
REM Quick Install and Run Script
REM ==============================

echo.
echo ========════════════════════════════════════════
echo   Football Match Prediction - Setup Script
echo ========════════════════════════════════════════
echo.

REM Check if venv exists
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found
    echo Please activate: .\.venv\Scripts\activate
    exit /b 1
)

echo [1/3] Installing dependencies (this may take a few minutes)...
.\.venv\Scripts\python.exe -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo ERROR: Installation failed
    exit /b 1
)
echo ^✓ Dependencies installed

echo.
echo [2/3] Running complete pipeline with 300 simulations...
echo.
.\.venv\Scripts\python.exe code\08_run_all.py --simulations 300
if errorlevel 1 (
    echo ERROR: Pipeline execution failed
    exit /b 1
)

echo.
echo ========════════════════════════════════════════
echo ^✓ PIPELINE COMPLETED SUCCESSFULLY
echo ========════════════════════════════════════════
echo.
echo Results saved to:
echo   • data/processed/football_bi/
echo   • reports/football_bi/
echo   • models/football_bi/
echo.
echo To view the dashboard:
echo   python code/09_run_api.py
echo.

pause
