# bi-cohost — run the pipeline
# Usage:
#   .\run.ps1 --brief "Sales dashboard" --build-id test-001 --pbip-path "C:\...\MyReport.Report"
#   .\run.ps1 --brief "Sales dashboard" --build-id test-001   (writes scaffold to artifacts/ instead)
#   .\run.ps1 --brief "..." --build-id test-001 --force       (re-run all stages)

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Virtual environment not found. Run .\setup.ps1 first." -ForegroundColor Red
    exit 1
}

& .\.venv\Scripts\python.exe agents\conductor.py @args
