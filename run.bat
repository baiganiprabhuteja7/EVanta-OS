@echo off
title Evanta OS Launcher
echo ==========================================
echo           Starting EVANTA OS             
echo    EV Charging Station Management        
echo      Hyderabad, Telangana, India         
echo ==========================================

cd /d "%~dp0backend"
set PYTHON_EXE=.venv\Scripts\python.exe
if not exist "%PYTHON_EXE%" set PYTHON_EXE=venv\Scripts\python.exe
if not exist "%PYTHON_EXE%" set PYTHON_EXE=python

echo [1/3] Applying database migrations and initializing station...
"%PYTHON_EXE%" -m alembic upgrade head
"%PYTHON_EXE%" -c "from app.db.seed import seed_database; seed_database(); print('Evanta OS database initialized.')"

echo [2/3] Starting FastAPI backend on http://127.0.0.1:8000...
start "Evanta OS - Backend API" "%PYTHON_EXE%" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

echo Waiting for backend API to initialize on port 8000...
timeout /t 3 /nobreak >nul

echo [3/3] Starting Vite frontend on http://localhost:5173...
cd /d "%~dp0frontend"
npm run dev
