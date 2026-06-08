# bi-cohost — Windows one-time setup
# Run this from the project folder: .\setup.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "bi-cohost setup" -ForegroundColor Cyan
Write-Host "===============" -ForegroundColor Cyan

# 1. Check Python
try {
    $pyver = python --version 2>&1
    Write-Host "  Python: $pyver" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Python not found. Install from https://python.org (check 'Add to PATH')" -ForegroundColor Red
    exit 1
}

# 2. Create venv
if (-not (Test-Path ".venv")) {
    Write-Host "  Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
} else {
    Write-Host "  Virtual environment already exists" -ForegroundColor Green
}

# 3. Install dependencies
Write-Host "  Installing dependencies..." -ForegroundColor Yellow
& .\.venv\Scripts\pip.exe install -r requirements.txt --quiet
Write-Host "  Dependencies installed" -ForegroundColor Green

# 4. Set up .env
if (-not (Test-Path ".env")) {
    Copy-Item .env.example .env
    Write-Host ""
    Write-Host "  .env created from template." -ForegroundColor Yellow
    Write-Host "  Opening it now — paste your ANTHROPIC_API_KEY and save." -ForegroundColor Yellow
    Write-Host ""
    Start-Process notepad .env -Wait
} else {
    Write-Host "  .env already exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "Setup complete. Next steps:" -ForegroundColor Cyan
Write-Host "  1. Open Power BI Desktop"
Write-Host "     File -> Options -> Preview features -> enable 'Store reports using enhanced metadata format (PBIR)'"
Write-Host "  2. Create a blank report and save it as a .pbip project — note the .Report folder path"
Write-Host "  3. Run the pipeline:"
Write-Host "     .\run.ps1 --brief 'Your brief here' --build-id test-001 --pbip-path 'C:\path\to\MyReport.Report'" -ForegroundColor White
Write-Host ""
