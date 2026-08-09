# 🚀 Local Launch & Testing Guide (Phase 4 & Desktop Engine)

This document provides step-by-step instructions for launching, testing, and developing the **Dota 2 History Visualizer** locally.

> [!NOTE]
> This document is updated dynamically throughout the implementation of Phase 4 sub-phases.

## 🐋 0. Single-Command Docker Deployment (Recommended)

To run the entire Phase 4 multi-service stack (Redis, Celery background rendering worker, FastAPI Gateway, and Next.js Web Frontend) using Docker:

```bash
# Build and launch all 4 services in containerized mode
docker-compose up -d --build

# View container logs
docker-compose logs -f

# Services will be accessible at:
# Next.js Web Application:  http://localhost:3050
# FastAPI Backend Gateway:  http://localhost:8050
# Swagger API Documentation: http://localhost:8050/docs
```

---

## 🛠️ 1. Environment & Prerequisites

### Prerequisites
1. **Python 3.10+** (Python 3.14 tested)
2. **FFmpeg** (Required for video encoding & audio mixing)
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg`
   - Windows: Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) and add `bin/` to system PATH.

### Installation
Set up environment and install required Python packages:

```bash
# Activate python virtual environment (or create dota-env)
python3 -m venv dota-env
source dota-env/bin/activate

# Install core desktop & web backend dependencies
pip install -r requirements.txt
pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings httpx slowapi pyjwt celery redis

# Register repository package in editable mode (fixes ModuleNotFoundError)
pip install -e .
```

---

## 🌐 2. Phase 4 Web Architecture: Local Launch & Testing

Phase 4 introduces a decoupled, web-native distributed architecture using FastAPI REST/SSE endpoints.

### Launching the Backend Gateway (`src/backend`)

Run the backend application server locally using Uvicorn (set `PYTHONPATH=.` or run as Python module):

```bash
# Option A: Run via uvicorn with PYTHONPATH=.
PYTHONPATH=. uvicorn src.backend.main:app --reload --host 127.0.0.1 --port 8000

# Option B: Run main module directly with Python
python -m src.backend.main
```

The backend server starts at `http://127.0.0.1:8000`.

### Interactive API Documentation & Health Check

Once the backend is running, access:
- **OpenAPI / Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc Documentation:** `http://127.0.0.1:8000/redoc`
- **Health Check Endpoint:** `http://127.0.0.1:8000/health` or `http://127.0.0.1:8000/api/v1/health`

#### Test Health Endpoint via `curl`:
```bash
curl -i http://127.0.0.1:8000/api/v1/health
```

### Verifying the SQLite Database & ORM Tables

When the backend launches, `init_db()` automatically creates the SQLite database file at `cache/dota_visualizer_v4.db` with all 5 Phase 4 domain tables:

```bash
# Inspect created database tables using sqlite3 CLI
sqlite3 cache/dota_visualizer_v4.db ".tables"
# Output: api_keys  matches  profiles  render_jobs  steam_users

# View complete table schemas
sqlite3 cache/dota_visualizer_v4.db ".schema matches"
```

You can also run a quick Python verification snippet:

```bash
python -c "
from src.backend.core.database import SessionLocal, init_db
from src.backend.models.matches import MatchModel
import json

init_db()
db = SessionLocal()
print('Total matches in database:', db.query(MatchModel).count())
db.close()
"
```

---

## 🚦 3. Phase 4 Sub-Phases Status & Testing Matrix

| Sub-Phase | Component | Status | Launch & Test Instructions |
|---|---|---|---|
| **P4-01** | Backend Infrastructure & Models | **COMPLETED** | Start backend server with `uvicorn src.backend.main:app` and run `./dota-env/bin/python -m unittest discover -s tests/backend`. |
| **P4-02** | Ingestion & 90-Day LRU Pruning | **COMPLETED** | Test OpenDota sync (`POST /api/v1/players/{id}/sync`), match retrieval (`GET /api/v1/players/{id}/matches`), and LRU cache eviction (`POST /api/v1/admin/lru-prune`). |
| **P4-03** | Steam OpenID Auth & JWT Session | **COMPLETED** | Test Steam login URL (`GET /api/v1/auth/steam/login`), mock login (`GET /api/v1/auth/steam/callback`), and user session (`GET /api/v1/auth/me`). |
| **P4-04** | Async Celery Worker Queue | **COMPLETED** | Test video render job submission (`POST /api/v1/render/jobs`), status polling (`GET /api/v1/render/jobs/{job_id}`), and MP4 streaming (`GET /api/v1/render/media/{file}`). |
| **P4-05** | Security, CORS & Rate Limiting | **COMPLETED** | Test developer API key generation (`POST /api/v1/keys`), listing (`GET /api/v1/keys`), revocation (`DELETE /api/v1/keys/{id}`), and SlowAPI rate limiting. |
| **P4-06** | Ephemeral Storage & 1-Hr Auto-Purge | **COMPLETED** | Test automated 1-hour media purge engine and admin purge endpoint (`POST /api/v1/admin/ephemeral-purge`). |
| **P4-07** | Next.js Frontend SPA | *Pending* | *(Will launch frontend web app with `npm run dev`)* |
| **P4-08** | Docker Deployment | *Pending* | *(Will test `docker-compose up` containerization)* |

### 📋 Ready-to-Run API Verification Script

Run all API tests automatically against a live local server:

```bash
bash scripts/test_api_endpoints.sh
```

---

### 🧪 Complete cURL Cheat Sheet (All Implemented Endpoints)

Make sure the server is running (`PYTHONPATH=. uvicorn src.backend.main:app --reload`):

#### 1. Top-Level System Health Check
```bash
curl -X GET "http://127.0.0.1:8000/health"
```

#### 2. API v1 Health Check
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/health"
```

#### 3. Player Match & Profile Sync (OpenDota Incremental Fetch)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/players/70388657/sync"
```
*Sample Response:*
```json
{
  "player_id": 70388657,
  "player_name": "Dendi",
  "total_matches": 21494,
  "new_matches_synced": 0,
  "last_synced_at": "2026-08-07T10:24:40.123456+00:00",
  "message": "Successfully synced 0 new matches."
}
```

#### 4. Get Player Profile & Cached Match History
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/players/70388657/matches"
```

#### 5. Trigger 90-Day LRU Cache Eviction Task
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/admin/lru-prune?days_inactive=90"
```
*Sample Response:*
```json
{
  "status": "success",
  "days_inactive_threshold": 90,
  "cutoff_date": "2026-05-09T10:24:40.123456+00:00",
  "pruned_matches": 0,
  "pruned_profiles": 0,
  "message": "Evicted 0 inactive matches and 0 profiles."
}
```

#### 6. Get Steam OpenID Login URL
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/auth/steam/login"
```

#### 7. Steam Callback & JWT Token Generation (Development Mock)
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/auth/steam/callback?mock_steam_id64=76561197960265728"
```
*Sample Response:*
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 604800,
  "user_id": 1,
  "steam_id64": "76561197960265728",
  "display_name": "SteamUser_70388657"
}
```

#### 8. Get Authenticated User Profile (`/auth/me`)
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/auth/me" \
  -H "Authorization: Bearer <access_token>"
```

#### 9. Enqueue Async Video Render Job
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/render/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "player_id": 70388657,
    "metric": "Hero Versatility",
    "quality": "Draft",
    "aspect_ratio": "9:16",
    "theme": "Midnight Cyberpunk"
  }'
```
*Sample Response:*
```json
{
  "job_id": "job_a1b2c3d4e5f6",
  "player_id": 70388657,
  "metric": "Hero Versatility",
  "aspect_ratio": "9:16",
  "theme": "Midnight Cyberpunk",
  "quality": "Draft",
  "status": "PENDING",
  "progress": 0,
  "created_at": "2026-08-07T10:48:00.123456+00:00"
}
```

#### 10. Poll Render Job Status and Progress
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/render/jobs/job_a1b2c3d4e5f6"
```
*Sample Response:*
```json
{
  "job_id": "job_a1b2c3d4e5f6",
  "status": "COMPLETED",
  "progress": 100,
  "video_url": "/api/v1/render/media/job_a1b2c3d4e5f6.mp4",
  "expires_at": "2026-08-07T11:48:00.123456+00:00",
  "error_message": null
}
```

#### 12. Create Developer API Key
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/keys" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "CLI App Key"}'
```
*Sample Response:*
```json
{
  "id": 1,
  "name": "CLI App Key",
  "key": "dota_live_a1b2c3d4e5f6...",
  "is_active": true,
  "created_at": "2026-08-08T09:30:00.123456+00:00"
}
```

#### 13. List Authenticated User API Keys
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/keys" \
  -H "Authorization: Bearer <access_token>"
```

#### 15. Trigger 1-Hour Ephemeral Media Purge Task
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/admin/ephemeral-purge?ttl_seconds=3600"
```
*Sample Response:*
```json
{
  "status": "success",
  "ttl_seconds": 3600,
  "cutoff_time": "2026-08-08T08:58:00.123456+00:00",
  "purged_jobs_count": 0,
  "orphaned_files_count": 0,
  "freed_bytes": 0,
  "message": "Successfully purged 0 expired jobs and 0 orphan files."
}
```

---

## 💻 4. Desktop Engine Execution Modes (Legacy / Standalone)

In addition to the Phase 4 Web Backend, local execution modes for desktop and CLI remain fully functional:

### Mode A: Desktop CustomTkinter GUI
Launch desktop window interface:
```bash
python main.py
```

### Mode B: Headless CLI
Generate videos directly from terminal:
```bash
python cli.py --player_id 70388657 --metric "Hero Versatility" --aspect_ratio "9:16" --quality "Normal"
```

### Mode C: PyInstaller Standalone Executable
Build standalone executable bundle:
```bash
python build.py
```

---

## 🧪 5. Automated Test Suite Execution

Run automated unit and integration tests using Python's `unittest` test runner:

### Run Complete Test Suite (Desktop + Backend):
```bash
./dota-env/bin/python -m unittest discover -s tests
```

### Run Backend Tests Only (Phase 4):
```bash
./dota-env/bin/python -m unittest discover -s tests/backend
```

### Run Desktop Data & Strategy Tests:
```bash
./dota-env/bin/python -m unittest discover -s tests/data
```

### Run Desktop Visualizer Tests:
```bash
./dota-env/bin/python -m unittest discover -s tests/visualizer
```
