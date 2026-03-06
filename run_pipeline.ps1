# PowerShell Script to Install and Run Pipeline
# Bypass execution policy issues by running python directly

param(
    [int]$Simulations = 300
)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Football Match Prediction - Pipeline" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$PythonExe = ".\.venv\Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Host "ERROR: Virtual environment not found" -ForegroundColor Red
    Write-Host "Please activate: .\.venv\Scripts\activate" -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/2] Installing dependencies..." -ForegroundColor Yellow
& $PythonExe -m pip install -q -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Installation failed" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Dependencies installed" -ForegroundColor Green
Write-Host ""

Write-Host "[2/2] Running pipeline with $Simulations simulations..." -ForegroundColor Yellow
Write-Host ""
& $PythonExe code/08_run_all.py --simulations $Simulations
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Pipeline execution failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Pipeline Completed Successfully" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Results saved to:" -ForegroundColor Cyan
Write-Host "  • Data: data/processed/football_bi/" -ForegroundColor Gray
Write-Host "  • Reports: reports/football_bi/" -ForegroundColor Gray
Write-Host "  • Models: models/football_bi/" -ForegroundColor Gray
Write-Host ""
Write-Host "View dashboard:" -ForegroundColor Cyan
Write-Host "  $PythonExe code/09_run_api.py" -ForegroundColor White
Write-Host ""
