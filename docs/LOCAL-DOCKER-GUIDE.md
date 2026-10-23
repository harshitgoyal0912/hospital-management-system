# 🏥 Hospital Management System - Local & Docker Setup Guide

A complete, beginner-friendly guide to running the **Hospital Management System** locally on Windows using PowerShell, Python, React (Vite), and Docker.

---

## 📋 Table of Contents
1. [System Prerequisites & Verified Versions](#1-system-prerequisites--verified-versions)
2. [Verified URLs & Access Points](#2-verified-urls--access-points)
3. [Verified Test Credentials](#3-verified-test-credentials)
4. [Architecture & How It Works](#4-architecture--how-it-works)
5. [Environment Variables Setup](#5-environment-variables-setup)
6. [Option A: Running Locally with PowerShell & Docker Database (Recommended)](#6-option-a-running-locally-with-powershell--docker-database-recommended)
7. [Option B: Running the Entire Application via Docker Compose](#7-option-b-running-the-entire-application-via-docker-compose)
8. [Stopping and Restarting the System](#8-stopping-and-restarting-the-system)
9. [Safe Database Backup & Reset](#9-safe-database-backup--reset)
10. [Troubleshooting & Common Errors](#10-troubleshooting--common-errors)

---

## 1. System Prerequisites & Verified Versions

| Component | Tested Version | Status / Notes |
| :--- | :--- | :--- |
| **Operating System** | Windows 11 (64-bit) | PowerShell 5.1 / 7+ |
| **Python** | 3.13.x / 3.12.x | Virtual environment in `backend-python/.venv` |
| **Package Manager (Python)** | `uv` 0.x | `$env:APPDATA\Python\Python313\Scripts\uv.exe` |
| **Node.js** | 20+ (v22 tested) | Frontend build & dev server |
| **npm** | 10+ | Used in `frontend/` directory |
| **Docker Desktop** | 4.95.0+ | Engine 29.8.2, Docker Compose v5.6.0 |
| **WSL 2** | Ubuntu (Version 2) | Backend engine for Docker Desktop |
| **PostgreSQL** | 15 (Alpine) | Containerized on port `5432` with persistent volume |

---

## 2. Verified URLs & Access Points

| Service | Local Dev URL | Docker Compose URL | Description |
| :--- | :--- | :--- | :--- |
| **Frontend UI** | [http://localhost:5173](http://localhost:5173) | [http://localhost:3000](http://localhost:3000) | Hospital Management React dashboard |
| **Backend API** | [http://localhost:8000](http://localhost:8000) | [http://localhost:8000](http://localhost:8000) | Multi-Agent FastMCP + FastAPI server |
| **Health Check** | [http://localhost:8000/health](http://localhost:8000/health) | [http://localhost:8000/health](http://localhost:8000/health) | Server, DB & Multi-Agent status |
| **Tools Directory** | [http://localhost:8000/tools/list](http://localhost:8000/tools/list) | [http://localhost:8000/tools/list](http://localhost:8000/tools/list) | List of 122+ available medical & CRUD tools |
| **Discharge Reports**| [http://localhost:8000/discharge/](http://localhost:8000/discharge/) | [http://localhost:8000/discharge/](http://localhost:8000/discharge/) | Static generated PDF report endpoint |

---

## 3. Verified Test Credentials

The database comes pre-seeded with 30 diverse hospital staff accounts across all roles. Use any of the verified accounts below to log in:

| Role | Username / Email | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Admin** | `robert.williams3` *(or `robert.williams3@hospital.com`)* | `cGSGg9zArS61ol4yy7aZ` | Full hospital administration & tool access |
| **Doctor** | `david.thomas10` *(or `david.thomas10@hospital.com`)* | `rm23i6FhILLvXkuTMMl8` | Patient care, clinical notes, discharge reports |
| **Nurse** | `emily.brown16` *(or `emily.brown16@hospital.com`)* | `ErToUrHlqcewAalVN898` | Bed assignments, patient intake, vitals |
| **Manager** | `elizabeth.brown1` *(or `elizabeth.brown1@hospital.com`)* | `ux1LjFtFs1z2lXD4HhF5` | Staff management, department overview |
| **Receptionist** | `lisa.ramirez15` *(or `lisa.ramirez15@hospital.com`)* | `tjrgZwtHgXJAZrcgPnRi` | Patient admissions, room appointments |

> [!NOTE]
> All credentials use bcrypt hashes stored in PostgreSQL. To view or regenerate new passwords at any time, run:
> ```powershell
> python scripts/reset_dev_users.py --apply
> ```

---

## 4. Architecture & How It Works

- **Frontend**: Single-Page Application (SPA) built with React 19, Tailwind CSS, Lucide icons, and Vite. Runs on port 5173 (dev) or 3000 (Docker).
- **Backend**: Python multi-agent system exposing FastMCP tools over HTTP/SSE via Starlette/FastAPI on port 8000.
- **Authentication**: JWT Bearer tokens issued by `POST /auth/login` and verified by `hms_agent.auth.TokenIssuer`.
- **Database**: PostgreSQL 15 running in Docker with automated healthcheck and named volume persistence (`postgres_data`).

---

## 5. Environment Variables Setup

### Backend: `backend-python/.env`
```env
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hospital_management
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hospital_management
DB_USER=postgres
DB_PASSWORD=postgres

# HMS Authentication and Execution Mode
HMS_JWT_SECRET=super_secret_jwt_key_at_least_32_characters_long_for_hms_auth_token_issuance
TOOL_EXECUTION_MODE=shadow

# Python UTF-8 console output for Windows
PYTHONUTF8=1

# Optional AI services (Leave empty for local CRUD & hospital management operations)
OPENAI_API_KEY=
GEMINI_API_KEY=
```

### Frontend: `frontend/.env`
```env
# MCP Backend Server URL
VITE_MCP_BRIDGE_URL=http://localhost:8000

# Optional External AI API Keys (Leave empty for local operations)
VITE_OPENAI_API_KEY=
VITE_CLAUDE_API_KEY=
VITE_GROQ_API_KEY=
VITE_GOOGLE_API_KEY=
```

---

## 6. Option A: Running Locally with PowerShell & Docker Database (Recommended)

This mode gives you the fastest development loop, live reload for both frontend and backend, and native debugging in VS Code.

### Step 1: Start PostgreSQL via Docker Compose
In your root terminal:
```powershell
docker compose -f docker-compose.simple.yml up -d postgres
```
Verify PostgreSQL is healthy:
```powershell
docker ps
```

### Step 2: Initialize Database Tables & Sample Data *(First Time Only)*
```powershell
cd D:\hospital-management-system-main\backend-python
.\.venv\Scripts\python.exe setup_database.py
.\.venv\Scripts\python.exe scripts\reset_dev_users.py --apply
```

### Step 3: Start the Backend Server
```powershell
cd D:\hospital-management-system-main\backend-python
.\.venv\Scripts\python.exe multi_agent_server.py
```
*Expected log output:*
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Step 4: Start the Frontend Dev Server *(In a second terminal)*
```powershell
cd D:\hospital-management-system-main\frontend
npm run dev
```
*Expected log output:*
```
  VITE v7.0.6  ready in 345 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### Step 5: Open in Your Browser
Open [http://localhost:5173](http://localhost:5173) in Chrome, Edge, or Firefox.
Sign in with:
- **Email / Username**: `robert.williams3`
- **Password**: `cGSGg9zArS61ol4yy7aZ`

---

## 7. Option B: Running the Entire Application via Docker Compose

To run all 3 services (PostgreSQL, Backend API, Frontend Web App) fully containerized:

```powershell
cd D:\hospital-management-system-main
docker compose -f docker-compose.simple.yml up -d --build
```

- Frontend container will be accessible at: **`http://localhost:3000`**
- Backend API container will be accessible at: **`http://localhost:8000`**
- PostgreSQL will be running on port **`5432`**

To view container logs:
```powershell
docker compose -f docker-compose.simple.yml logs -f
```

---

## 8. Stopping and Restarting the System

### Safe Stop (Preserves all database data and uploads)
```powershell
# If using Option A (local processes):
# Press CTRL+C in the terminal running backend and frontend.
# Stop the database container safely:
docker compose -f docker-compose.simple.yml stop postgres

# If using Option B (Docker Compose):
docker compose -f docker-compose.simple.yml stop
```

### Restarting
```powershell
docker compose -f docker-compose.simple.yml start
```

> [!CAUTION]
> Never run `docker compose down -v` unless you intentionally want to wipe all database tables and uploaded files. The `-v` flag deletes Docker volumes!
> To stop without deleting data, always use `docker compose stop` or plain `docker compose down` (without `-v`).

---

## 9. Safe Database Backup & Reset

### Backing Up the Database
To create an SQL dump of the current database:
```powershell
docker exec -t hospital_postgres pg_dump -U postgres hospital_management > D:\hospital-management-system-main\backup.sql
```

### Restoring from Backup
```powershell
docker exec -i hospital_postgres psql -U postgres hospital_management < D:\hospital-management-system-main\backup.sql
```

### Resetting to Fresh Sample Data
If you ever want to re-seed the test data:
```powershell
cd D:\hospital-management-system-main\backend-python
.\.venv\Scripts\python.exe setup_database.py
.\.venv\Scripts\python.exe scripts\reset_dev_users.py --apply
```

---

## 10. Troubleshooting & Common Errors

### 1. `ModuleNotFoundError: No module named 'psycopg'`
- **Cause**: SQLAlchemy 2.0 defaults to psycopg 3 when connection strings begin with `postgresql://`.
- **Solution**: We installed `psycopg[binary]` in `.venv` and configured `database.py` to support both `psycopg` and `psycopg2`.

### 2. `UnicodeEncodeError: 'charmap' codec can't encode character ...`
- **Cause**: Windows PowerShell default code page (cp1252) cannot display Unicode emojis (`✅`, `🏥`, `🤖`) printed by the server.
- **Solution**: Both `database.py` and `multi_agent_server.py` reconfigure `sys.stdout` and `sys.stderr` to `utf-8` on Windows startup.

### 3. "OpenAI API key not configured" on Login
- **Cause**: Earlier frontend logic required an OpenAI API key even for non-AI hospital operations.
- **Solution**: `AuthSetup.jsx` was updated so `VITE_OPENAI_API_KEY` is completely optional. Core hospital functions (patients, beds, rooms, staff, departments, inventory) work immediately without any API key.

### 4. Healthcheck Fails on Startup
- Ensure the PostgreSQL container is running:
  ```powershell
  docker ps
  ```
  If it says `starting`, wait 5-10 seconds for PostgreSQL to initialize and report `healthy`.

---

## 🏁 Exact Commands to Run Right Now

Your database and backend are currently running in the background. Simply run:

```powershell
# Open the web app in your browser:
Start-Process "http://localhost:5173"
```

Then sign in using:
- **Username**: `robert.williams3`
- **Password**: `cGSGg9zArS61ol4yy7aZ`
