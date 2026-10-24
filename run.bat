@echo off
title EVanta OS Launcher
echo ==========================================
echo           Starting EVanta OS              
echo ==========================================

cd /d "%~dp0backend"
set PYTHON_EXE=.venv\Scripts\python.exe
if not exist "%PYTHON_EXE%" set PYTHON_EXE=venv\Scripts\python.exe
if not exist "%PYTHON_EXE%" set PYTHON_EXE=python

echo [1/3] Checking and seeding database...
"%PYTHON_EXE%" -c "from app.db.seed import seed_database; seed_database(); print('Database seeded and ready.')"

echo [2/3] Starting FastAPI backend on http://127.0.0.1:8000...
start "EVanta OS - Backend API" "%PYTHON_EXE%" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

echo [3/3] Starting Vite frontend on http://localhost:5173...
cd /d "%~dp0frontend"
npm run dev
