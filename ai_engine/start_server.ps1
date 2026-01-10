# PowerShell script to start AI Engine server
# This sets up the Python path correctly

# Get the directory where this script is located
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Set PYTHONPATH to include src directory
$srcPath = Join-Path $scriptDir "src"
$env:PYTHONPATH = $srcPath

Write-Host "===================================="
Write-Host "Starting AI Engine server..."
Write-Host "Working Directory: $scriptDir"
Write-Host "Python Path: $env:PYTHONPATH"
Write-Host "===================================="
Write-Host ""

# Activate virtual environment if it exists
if (Test-Path ".ven\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..."
    .\.ven\Scripts\Activate.ps1
    Write-Host ""
}

# Run uvicorn
Write-Host "Running uvicorn..."
python -m uvicorn src.main:app --host 0.0.0.0 --port 5000 --reload
