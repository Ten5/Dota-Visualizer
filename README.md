# Dota Stats Visualizer ⚔️📊

A high-performance cloud visualizer and video rendering platform that transforms Dota 2 match history into sleek, animated **"Bar Chart Race"** videos. Watch your most played heroes, win rates, KDA ratios, damage output, farming efficiency, and multi-kill sprees unfold from your earliest matches to the present day.

---

## 🚀 Key Features & Capabilities

- **🌐 Decoupled Full-Stack Architecture (Phase 4 SDD):**
  - **Frontend:** Next.js 15 App Router, React 19, Tailwind CSS, Lucide icons, glassmorphism UI.
  - **Backend Gateway:** FastAPI (Python 3.11), SQLAlchemy, SlowAPI rate-limiting, OpenID 2.0 Steam Auth, JWT Sessions.
  - **Async Worker Queue:** Celery & Redis task queue for rendering high-FPS MP4 videos in background workers.
  - **Security Engine:** Dynamic Content Security Policy (CSP), CORS protection, API key authentication.

- **📱 9:16 Vertical Shorts & 16:9 Landscape:** Export videos in standard `16:9` landscape or `9:16` vertical video formatted for **TikTok, YouTube Shorts, and Instagram Reels**.
- **🎨 UI Theme Engine:** Switch between curated color themes (*Dire Crimson*, *Radiant Gold*, *Midnight Cyberpunk*) with harmonized typography and clean overlay spacing.
- **🎬 In-Browser MP4 Video Preview & Recent Renders:** View, preview, and download active generated video animations directly inside an interactive HTML5 modal.
- **⚔️ Dota 2 Patch Timeline Overlay:** Displays historical patch release labels (e.g. *PATCH 7.33 - NEW FRONTIERS*, *PATCH 7.36*) alongside monthly date stamps.
- **⚡ Dynamic Period Pacing:** Automatically speeds up during quiet/inactive months (fast-forwarding in ~0.16s) and slows down during intense gaming sprees & rank swaps for cinematic focus.
- **🎵 Custom Background Music Selector:** Select custom `.mp3` or `.wav` audio files directly from the web app or API.

---

## 📊 17 Statistical Visualization Metrics

1. ⚡ **Hero Impact Rating** (`Wins × √(Games)` signature mains score)
2. 🔥 **Multi-Kill & Rampage Race** (High-kill & teamfight slaughter race)
3. 🌾 **GPM Farming Efficiency** (Average Gold Per Min timeline)
4. 🏆 **Win Streak Master** (Longest winning sprees per hero)
5. 🛡️ **Roshan & Aegis Claims** (Objective siege & boss kills)
6. 🚀 **Blitz Stomper** (Fastest push victory duration)
7. 👑 **Hero Masteries** (Most played main heroes race)
8. 🥇 **Total Wins** (Victory milestones per hero)
9. 📈 **Win Rate %** (Win rate percentage for top mains)
10. ⚔️ **Most Purchased Items** (Item purchase race history)
11. 🎭 **Role Evolution** (Core vs Support role balance)
12. 🎯 **KDA Efficiency** (Kill/Death/Assist ratio timeline)
13. 🏰 **Tower Damage** (Objective siege damage)
14. 🗺️ **Laning Preference** (Safe/Mid/Offlane distribution)
15. 💥 **Total Hero Damage** (Combat damage dealt)
16. 💀 **Total Deaths** (Casualty count timeline)
17. 💰 **Total Net Gold** (Farming efficiency race)

---

## 🐋 Production Deployment & Local Launch

### Option A: Local Docker Compose (Single Command)
Run the entire production stack locally on dedicated ports **`3050`** and **`8050`**:

```bash
docker compose up -d --build
```
- 🌐 **Web Application:** [http://localhost:3050](http://localhost:3050)
- ⚡ **FastAPI Backend Gateway:** [http://localhost:8050](http://localhost:8050)
- 📖 **Interactive API Docs:** [http://localhost:8050/docs](http://localhost:8050/docs)

---

### Option B: Free Cloud Hosting Stack (Vercel + Render + Upstash)

1. **Frontend (Vercel):** Deploy `frontend/` directory to Vercel with Environment Variable:
   ```env
   NEXT_PUBLIC_API_URL=https://your-backend.onrender.com/api/v1
   ```
2. **Backend Gateway & Celery Worker (Render.com):** Deploy `Dockerfile.backend` to Render Web Service and Background Worker with Environment Variables:
   ```env
   ENVIRONMENT=production
   REDIS_URL=rediss://default:PASSWORD@endpoint.upstash.io:6379
   JWT_SECRET_KEY=your_secret_key
   ```
3. **Redis Broker (Upstash):** Create free serverless TLS Redis instance on Upstash.com.

---

## 🧪 Running Automated Test Suite

Run the full automated unit test suite:
```bash
./dota-env/bin/python -m unittest discover -s tests
```