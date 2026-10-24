# EVanta OS ⚡

**EV Charging Intelligence & Business Management Platform**

EVanta OS is an enterprise-grade electric vehicle (EV) charging infrastructure and business intelligence operating system. It provides real-time telemetry, charging session tracking, hardware status monitoring, and financial KPI analytics for charging hub operators.

---

## 🚀 Quick Start (Ready to Run)

### Option 1: One-Click Launch (Windows)
Double-click `run.bat` or run in PowerShell:
```powershell
.\run.ps1
```
This automatically verifies database tables, seeds initial data, launches the FastAPI backend on `http://127.0.0.1:8000`, and starts the Vite frontend at `http://localhost:5173`.

### Option 2: Manual Start

#### 1. Backend (FastAPI + PostgreSQL)
```powershell
cd backend
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run database migrations and seed default data
python -c "from app.db.seed import seed_database; seed_database()"

# Start the API server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

#### 2. Frontend (React + Vite)
```powershell
cd frontend
npm install
npm run dev
```
- Web Application: [http://localhost:5173](http://localhost:5173)

---

## 🔐 Default Credentials

The system seeds an administrator account on first startup:

- **Email:** `admin@evanta.os`
- **Password:** `Admin@123456`
- **Role:** Administrator

Click the profile menu in the top-right corner to authenticate or manage workspace sessions.

---

## 📂 Architecture & Stack

```
EVanta OS/
├── backend/                       # FastAPI REST API & SQLAlchemy ORM
│   ├── alembic/                   # Database migrations
│   ├── app/
│   │   ├── api/v1/endpoints/      # Stations, Chargers, Sessions, Analytics, Settings, Auth
│   │   ├── core/                  # Security (JWT, Argon2) & Settings
│   │   ├── db/                    # Session management & Database Seeding
│   │   ├── models/                # SQLAlchemy Models (PostgreSQL)
│   │   ├── schemas/               # Pydantic v2 validation models
│   │   └── services/              # Business logic & KPI aggregations
│   ├── tests/                     # Pytest suite
│   ├── requirements.txt           # Python dependencies
│   └── .env                       # Backend database configuration
│
├── frontend/                      # React 19 + Vite Application
│   ├── src/
│   │   ├── components/            # AppShell, Topbar, Sidebar, Badges, Charts
│   │   ├── context/               # AppDataContext (Live PostgreSQL synchronization)
│   │   ├── pages/                 # Dashboard, Stations, Chargers, Sessions, Energy, Analytics, Settings
│   │   ├── services/              # API Client (typed async requests)
│   │   └── utils/                 # Currency, energy, date & CSV exporters
│   └── vite.config.js             # Vite config with backend proxy (/api -> 8000)
│
├── run.bat                        # One-click Windows batch launcher
├── run.ps1                        # PowerShell automated launcher
└── package.json                   # Root convenience scripts
```

---

## 🧪 Testing & Validation

### Backend Tests
```powershell
cd backend
.\.venv\Scripts\pytest
```

### Frontend Validation
```powershell
cd frontend
npm run lint
npm run build
```

---

## ⚙️ Environment Configuration

Backend configuration is loaded from [backend/.env](file:///backend/.env):
```env
DATABASE_URL=postgresql+psycopg://postgres:<password>@localhost:5432/evanta_os
SECRET_KEY=<your-secret-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
PROJECT_NAME="EVanta OS"
ENVIRONMENT=development
```
