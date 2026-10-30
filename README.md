# PRABHU'S GRID ⚡

**Personal EV Charging Station Monitoring & Management Prototype**  
**Location:** Hyderabad, Telangana, India  
**Station Owner:** Prabhu  
**Station Code:** `PRABHU-HYD-01`  
**Data Mode:** Deterministic Simulated Telemetry (`SIMULATED_DEMO_SOURCE`)  

> **DEMO MODE — SIMULATED DATA — NOT LIVE STATION TELEMETRY**  
> Prabhu's Grid is a personal operational prototype engineered exclusively for Prabhu's single EV charging station business in Hyderabad, Telangana. All measurements, sessions, load curves, and tariffs are simulated demo telemetry. No physical charging hardware is controlled.

---

## ⚡ 1. Product Scope & Architecture

Prabhu's Grid manages **exactly ONE station**:
- **Station Name:** Prabhu's Grid
- **Location:** HITEC City / Madhapur Corridor, Hyderabad, Telangana, India
- **Owner:** Prabhu
- **Chargers:** Multiple configurable AC & DC chargers under the single station (AC-01, AC-02, AC-03, DC-01, DC-02, DC-03)
- **Station Isolation:** Single-station boundary strictly enforced across backend services, database foreign keys, and frontend state. Multi-station directories, station search, and coaching modules have been permanently removed.

### Primary Navigation Destinations
1. **Overview (`/overview`)**: Instantaneous aggregate charging power (kW), energy delivered today (kWh), total installed capacity (kW), operational charger status badges, 24h hourly power trend chart, active sessions, station fault alerts, and demo mode indicator.
2. **Chargers (`/chargers`)**: Full CRUD for all AC & DC chargers belonging to Prabhu's Grid with rated power (kW), voltage (V), current (A), connector types, and operational states.
3. **Sessions (`/sessions`)**: Real-time tracking of active and historical charging sessions, interactive Start / Complete simulated session actions, and CSV export (`prabhus-grid-sessions.csv`).
4. **Energy & Reports (`/energy`)**: Station load profiles, 24-hour demand curves, AC vs. DC energy breakdowns, electrical formulas ($P = \sqrt{3} \times V \times I \times \cos\varphi$ for AC, $P = V \times I$ for DC), and downloadable audit reports (`prabhus-grid-energy-report.csv`).
5. **Settings (`/settings`)**: Station location, EV charging tariff (₹/kWh), bulk grid electricity cost (₹/kWh), telemetry polling interval, and one-click demo data reset.

---

## 🚀 2. Quick Start (Windows)

### Option 1: Automated Launcher (One-Click)
Double-click `run.bat` or run in PowerShell:
```powershell
.\run.ps1
```
This automatically initializes/seeds the PostgreSQL database with Prabhu's Grid station and chargers, starts the FastAPI backend on `http://127.0.0.1:8000`, and starts the Vite frontend on `http://localhost:5173`.

### Option 2: Separate Terminals

#### Terminal 1: Backend (FastAPI + PostgreSQL)
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -c "from app.db.seed import seed_database; seed_database()"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- **API Documentation (Swagger UI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check:** [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

#### Terminal 2: Frontend (React 19 + Vite)
```powershell
cd frontend
npm run dev
```
- **Web Application:** [http://localhost:5173](http://localhost:5173)

---

## 🔐 3. Authentication & Station Credentials

The database seeds Prabhu's owner credentials automatically:

- **Email:** `admin@prabhusgrid.in`
- **Password:** `Prabhu@Grid2026`
- **Station Code:** `PRABHU-HYD-01`
- **Role:** Station Owner

---

## 🧪 4. Testing & Validation

### Backend Pytest Suite
```powershell
cd backend
.\.venv\Scripts\pytest -v
```
*Result: 14 passed in 2.55s.*

### Frontend Code Quality & Production Build
```powershell
cd frontend
npm run lint
npm run build
```
*Result: 0 errors, 0 warnings. Production bundle built in 2.92s.*

---

## 🔧 5. Environment & Compatibility Resolution

- **Windows Application Control Fix:** On Windows with Python 3.14, SQLAlchemy's compiled Cython extension (`_cache_key_cy.pyd`) is blocked by Windows Code Integrity / App Control. Resolved cleanly by configuring `DISABLE_SQLALCHEMY_CEXT=1` in `backend/app/core/config.py` and `backend/.env`, allowing SQLAlchemy to use its official pure-Python fallback with zero security downgrades.
- **Electrical Clarity:** EV charging consumes grid power (kW) and accumulates energy (kWh). Charging power is electrical grid consumption, not generation.
