# EVANTA OS - Windows Automated Launcher
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "           Starting EVANTA OS             " -ForegroundColor Green
Write-Host "     EV Charging Station Management       " -ForegroundColor Green
Write-Host "       Hyderabad, Telangana, India        " -ForegroundColor Green
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

# Run database setup from backend directory so Alembic finds alembic.ini
Set-Location $backendDir
Write-Host "[1/3] Applying database migrations and baseline setup..." -ForegroundColor Yellow
& $pythonExe -m alembic upgrade head
& $pythonExe -c "from app.db.seed import seed_database; seed_database(); print('Evanta OS database ready.')"

Write-Host "[2/3] Launching FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Yellow
Start-Process -FilePath $pythonExe -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000" -WorkingDirectory $backendDir

# Wait for port 8000 to be ready before starting frontend to avoid 502 proxy errors
Write-Host "Waiting for FastAPI backend to accept connections..." -ForegroundColor Yellow
$maxRetries = 10
$retryCount = 0
$backendReady = $false
while (-not $backendReady -and $retryCount -lt $maxRetries) {
    Start-Sleep -Seconds 1
    try {
        $tcp = Test-NetConnection -ComputerName 127.0.0.1 -Port 8000 -WarningAction SilentlyContinue
        if ($tcp.TcpTestSucceeded) {
            $backendReady = $true
        }
    } catch {}
    $retryCount++
}

if ($backendReady) {
    Write-Host "[+] Backend is active on http://127.0.0.1:8000" -ForegroundColor Green
} else {
    Write-Host "[!] Note: Backend is starting in the background." -ForegroundColor Yellow
}

Write-Host "[3/3] Launching Vite Frontend on http://localhost:5173 ..." -ForegroundColor Yellow
Set-Location $frontendDir
npm run dev
