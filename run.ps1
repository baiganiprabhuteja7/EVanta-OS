# EVanta OS - Automated Launcher
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "           Starting EVanta OS             " -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan

$backendDir = Join-Path $PSScriptRoot "backend"
$frontendDir = Join-Path $PSScriptRoot "frontend"

$pythonExe = Join-Path $backendDir ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = Join-Path $backendDir "venv\Scripts\python.exe"
}
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

Write-Host "[1/3] Checking and seeding database..." -ForegroundColor Yellow
& $pythonExe -c "from app.db.seed import seed_database; seed_database(); print('Database ready.')"

Write-Host "[2/3] Launching FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Yellow
Start-Process -FilePath $pythonExe -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000" -WorkingDirectory $backendDir

Start-Sleep -Seconds 2

Write-Host "[3/3] Launching Vite Frontend on http://localhost:5173 ..." -ForegroundColor Yellow
Set-Location $frontendDir
npm run dev
