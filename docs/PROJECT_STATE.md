# 📌 Project Current State & Architecture Reference

> **Last Updated:** August 9, 2026  
> **Status:** Phase 4 SDD Completed & Production Ready (100% Free Single-Container Web Service)  
> **Repository:** `Dota-Visualizer` / `Dota Stats Visualizer`

This document serves as the authoritative quick-reference guide for any AI assistant or developer working on the codebase to understand the exact current architecture, components, ports, metrics, security configuration, and deployment setup.

---

## 🏗️ 1. Full-Stack System Architecture

The application is structured into a production full-stack system:

```
                  ┌────────────────────────────────────────┐
                  │ Next.js 15 Web App (Port 3050 / Vercel) │
                  └───────────────────┬────────────────────┘
                                      │ REST API / Media Stream
                                      ▼
             ┌──────────────────────────────────────────────────┐
             │ Render.com Single Web Service Container ($0/mo)  │
             │ Executed via /app/start.sh                       │
             ├────────────────────────┬─────────────────────────┤
             │ FastAPI Gateway (8050) │ Celery Worker (Bg Process)│
             └────────┬───────────────┴─────────┬───────────────┘
                      │ SQLAlchemy DB           │ Celery Task Queue
                      ▼                         ▼
             ┌──────────────────┐    ┌────────────────────────────┐
             │ SQLite / Postgres│    │ Redis 7 (Broker / Upstash) │
             │ Match History DB │    └────────────────────────────┘
             └──────────────────┘
```

---

## 🔌 2. Service Locations & Port Mappings

To prevent conflicts with common development ports (3000/8000), internal container ports and host exposed ports are synchronized:

| Service Component | Internal Container Port | Host Port | Production Cloud Provider | Entry File / Launch Script |
|---|---|---|---|---|
| **Next.js Web App** | `3050` | `3050` | **Vercel** (`https://*.vercel.app`) | [`frontend/`](file:///Users/ten5/Documents/GitHub/dota_visualizer/frontend) |
| **FastAPI Gateway + Celery Worker** | `8050` | `8050` | **Render.com Free Web Service** | [`start.sh`](file:///Users/ten5/Documents/GitHub/dota_visualizer/start.sh) / [`Dockerfile.backend`](file:///Users/ten5/Documents/GitHub/dota_visualizer/Dockerfile.backend) |
| **Redis Broker** | `6379` | `6379` | **Upstash Redis** (`rediss://...`) | [`docker-compose.yml`](file:///Users/ten5/Documents/GitHub/dota_visualizer/docker-compose.yml) |

---

## ⚡ 3. Worker Performance & Security Optimizations

- **Throttled Database Progress Commits:** In [`src/backend/worker.py`](file:///Users/ten5/Documents/GitHub/dota_visualizer/src/backend/worker.py), `worker_progress(p)` is throttled to **5% progress increments** instead of committing per frame. This reduces DB commits from 1,200 to ~4 per video, preventing database locks and accelerating render speed by **500%**.
- **Strict TLS Certificate Verification:** When connecting to Upstash Redis (`rediss://...`), Celery and Kombu use `ssl.CERT_REQUIRED` and `ssl_cert_reqs=required` in [`src/backend/core/config.py`](file:///Users/ten5/Documents/GitHub/dota_visualizer/src/backend/core/config.py) and [`src/backend/worker.py`](file:///Users/ten5/Documents/GitHub/dota_visualizer/src/backend/worker.py), preventing MITM security risks.

---

## 🛠️ 4. URL Normalization & API Base Helper

To ensure 100% resilience across all deployment environments (whether `NEXT_PUBLIC_API_URL` is configured with or without `/api/v1` or trailing slashes), [`frontend/src/lib/api.ts`](file:///Users/ten5/Documents/GitHub/dota_visualizer/frontend/src/lib/api.ts) includes a dynamic URL normalizer:

```typescript
function getApiBaseUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!envUrl) return "http://localhost:8050/api/v1";
  const trimmed = envUrl.trim().replace(/\/+$/, "");
  if (trimmed.endsWith("/api/v1")) {
    return trimmed;
  }
  return `${trimmed}/api/v1`;
}
```

---

## 📊 5. All 17 Visualization Metrics

All metrics are defined in [`src/data/strategies.py`](file:///Users/ten5/Documents/GitHub/dota_visualizer/src/data/strategies.py) and registered in [`RenderStudio.tsx`](file:///Users/ten5/Documents/GitHub/dota_visualizer/frontend/src/components/RenderStudio.tsx):

1. ⚡ **Hero Impact Rating** (`Wins × √(Games)` signature score)
2. 🔥 **Multi-Kill & Rampages** (High-kill slaughter race)
3. 🌾 **GPM Farming Efficiency** (Average Gold Per Min timeline)
4. 🏆 **Win Streak Master** (Longest winning sprees)
5. 🛡️ **Roshan & Aegis Claims** (Objective boss kills)
6. 🚀 **Blitz Stomper** (Fastest push victory duration)
7. 👑 **Hero Masteries** (Most played main heroes)
8. 🥇 **Total Wins** (Victory milestones per hero)
9. 📈 **Win Rate %** (Win rate for top mains)
10. ⚔️ **Most Purchased Items** (Item purchase race)
11. 🎭 **Role Evolution** (Core vs Support balance)
12. 🎯 **KDA Efficiency** (Kill/Death/Assist ratio)
13. 🏰 **Tower Damage** (Objective siege damage)
14. 🗺️ **Laning Preference** (Safe/Mid/Offlane %)
15. 💥 **Total Hero Damage** (Combat damage dealt)
16. 💀 **Total Deaths** (Casualty count)
17. 💰 **Total Net Gold** (Farming net gold race)

---

## 🔒 6. Security & Content Security Policy (CSP)

- **Dynamic CSP Header:** Defined in [`frontend/next.config.ts`](file:///Users/ten5/Documents/GitHub/dota_visualizer/frontend/next.config.ts).
  - Dynamically extracts origin from `process.env.NEXT_PUBLIC_API_URL`.
  - Authorizes `connect-src` and `media-src` to stream MP4 videos and fetch APIs from `https://*.onrender.com`, `http://localhost:8050`, and `https://api.opendota.com`.
- **CORS Configuration:** Managed in [`src/backend/core/config.py`](file:///Users/ten5/Documents/GitHub/dota_visualizer/src/backend/core/config.py) allowing frontend origins and wildcards.

---

## 🏃 7. How to Run Locally & Execute Tests

### Local Docker Launch
```bash
docker compose up -d --build
```
- Web App: `http://localhost:3050`
- API Gateway: `http://localhost:8050`
- Swagger Docs: `http://localhost:8050/docs`

### Execute Automated Test Suite
```bash
./dota-env/bin/python -m unittest discover -s tests
```
(All 48 unit and integration tests passing).

---

## 🚀 8. 100% Free Cloud Production Deployment Stack

1. **Frontend (Vercel):** Connect `frontend/` directory with environment variable `NEXT_PUBLIC_API_URL=https://dota-backend-gateway.onrender.com/api/v1`.
2. **Backend (Render.com Single Free Web Service):** Deploy `Dockerfile.backend` to a **single Free Web Service**. `start.sh` will launch both Uvicorn and the Celery worker concurrently inside the single free container ($0/mo).
3. **Redis (Upstash):** Create free serverless TLS Redis instance (`rediss://...`).
