# 📌 Project Current State & Architecture Reference

> **Last Updated:** August 9, 2026  
> **Status:** Phase 4 SDD Completed & Production Ready  
> **Repository:** `Dota-Visualizer` / `Dota Stats Visualizer`

This document serves as the authoritative quick-reference guide for any AI assistant or developer working on the codebase to understand the exact current architecture, components, ports, metrics, security configuration, and deployment setup.

---

## 🏗️ 1. Full-Stack System Architecture

The application is structured into four decoupled production services:

```
                  ┌────────────────────────────────────────┐
                  │ Next.js 15 Web App (Port 3050 / Vercel) │
                  └───────────────────┬────────────────────┘
                                      │ REST API / Media Stream
                                      ▼
             ┌──────────────────────────────────────────────────┐
             │  FastAPI Backend Gateway (Port 8050 / Render.com)  │
             └────────┬─────────────────────────────────┬───────┘
                      │ SQLAlchemy DB                   │ Celery Task Queue
                      ▼                                 ▼
             ┌──────────────────┐            ┌────────────────────────────┐
             │ SQLite / Postgres│            │ Redis 7 (Broker / Upstash) │
             │ Match History DB │            └──────────────┬─────────────┘
             └──────────────────┘                           │
                                                            ▼
                                             ┌────────────────────────────┐
                                             │ Celery Render Worker       │
                                             │ (OpenCV / FFmpeg Engine)   │
                                             └────────────────────────────┘
```

---

## 🔌 2. Service Locations & Port Mappings

To prevent conflicts with common development ports (3000/8000), internal container ports and host exposed ports are synchronized:

| Service Component | Internal Container Port | Host Port | Production Cloud Provider | Entry File / Path |
|---|---|---|---|---|
| **Next.js Web App** | `3050` | `3050` | **Vercel** (`https://*.vercel.app`) | [`frontend/`](file:///Users/ten5/Documents/GitHub/dota_visualizer/frontend) |
| **FastAPI Gateway** | `8050` | `8050` | **Render.com** (`https://*.onrender.com`) | [`src/backend/main.py`](file:///Users/ten5/Documents/GitHub/dota_visualizer/src/backend/main.py) |
| **Celery Render Worker** | N/A | N/A | **Render.com** (Background Worker) | [`src/backend/worker.py`](file:///Users/ten5/Documents/GitHub/dota_visualizer/src/backend/worker.py) |
| **Redis Broker** | `6379` | `6379` | **Upstash Redis** (`rediss://...`) | [`docker-compose.yml`](file:///Users/ten5/Documents/GitHub/dota_visualizer/docker-compose.yml) |

---

## 📊 3. All 17 Visualization Metrics

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

## 🔒 4. Security & Content Security Policy (CSP)

- **Dynamic CSP Header:** Defined in [`frontend/next.config.ts`](file:///Users/ten5/Documents/GitHub/dota_visualizer/frontend/next.config.ts).
  - Dynamically extracts origin from `process.env.NEXT_PUBLIC_API_URL`.
  - Authorizes `connect-src` and `media-src` to stream MP4 videos and fetch APIs from `https://*.onrender.com`, `http://localhost:8050`, and `https://api.opendota.com`.
- **CORS Configuration:** Managed in [`src/backend/core/config.py`](file:///Users/ten5/Documents/GitHub/dota_visualizer/src/backend/core/config.py) allowing frontend origins and wildcards.

---

## 🏃 5. How to Run Locally & Execute Tests

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

## 🚀 6. Cloud Production Deployment Stack

1. **Frontend (Vercel):** Connect `frontend/` directory with environment variable `NEXT_PUBLIC_API_URL=https://dota-backend-gateway.onrender.com/api/v1`.
2. **Backend (Render.com):** Connect `Dockerfile.backend` with environment variables (`REDIS_URL`, `ENVIRONMENT=production`, `JWT_SECRET_KEY`).
3. **Redis (Upstash):** Create free serverless TLS Redis instance.
