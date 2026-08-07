# ⚙️ Technical Architecture

## 1. System Overview
The application follows a modular **Model-View-Controller (MVC)** architecture with flexible local execution entry points (GUI, CLI, Standalone Bundle):
- **View / UI ([`src/ui/app.py`](file:///Users/ten5/Documents/GitHub/dota_visualizer/src/ui/app.py)):** Desktop GUI built with `CustomTkinter`. Configured with centered window hints, window app icons (`assets/icon.png`), direct file/media launchers, and background thread dispatching.
- **Headless CLI ([`cli.py`](file:///Users/ten5/Documents/GitHub/dota_visualizer/cli.py)):** Command-line entry point for automated headless video rendering.
- **Model / Data ([`src/data`](file:///Users/ten5/Documents/GitHub/dota_visualizer/src/data)):** OpenDota REST API integration (`api.py`), SQLite disk database manager (`db.py`), and 11 statistical strategy implementations (`strategies.py`).
- **Controller / Visualizer ([`src/visualizer/engine.py`](file:///Users/ten5/Documents/GitHub/dota_visualizer/src/visualizer/engine.py)):** Native OpenCV 2D canvas drawing engine with 32-color palette rotation, FFmpeg hardware acceleration piping (`h264_videotoolbox` / `nvenc`), and MoviePy audio/buffer post-processing.
- **Packaging ([`build.py`](file:///Users/ten5/Documents/GitHub/dota_visualizer/build.py)):** PyInstaller standalone packaging build script.

---

## 2. Key Components

### A. Dedicated Window & Application Icon ([`assets/icon.png`](file:///Users/ten5/Documents/GitHub/dota_visualizer/assets/icon.png))
- High-resolution glassmorphism application icon featuring a golden Dota 2 crest integrated with glowing bar chart race lines.
- CustomTkinter window icon bindings (`wm_iconphoto`) and screen-centering calculations (`760x780` geometry).

### B. High-Performance OpenCV Video Engine ([`src/visualizer/engine.py`](file:///Users/ten5/Documents/GitHub/dota_visualizer/src/visualizer/engine.py))
- **32-Color Palette:** Rotates among 32 distinct, vibrant colors for maximum visual contrast.
- **Frame Interpolation:** Linearly interpolates values and continuous Y-position ranks across time periods using Smoothstep easing ($\text{ease}(\alpha) = 3\alpha^2 - 2\alpha^3$).
- **On-Bar Legends:** Draws hero PNG icons and names directly onto horizontal bars with dark text shadows for contrast.
- **Scalable Typography:** Scalable TrueType fonts for title (34pt), subtitle (20pt), date overlay (54pt bold), and metric values (20pt).
- **Hardware Acceleration Pipe:** Pipes raw BGR24 frame bytes directly into FFmpeg subprocess (`h264_videotoolbox` / `nvenc`).

### C. SQLite Caching & Incremental Sync ([`src/data/db.py`](file:///Users/ten5/Documents/GitHub/dota_visualizer/src/data/db.py))
- Stores match history (`matches` table) and player profile avatars (`profiles` table) in `cache/dota_visualizer.db`.
- Loads cached player data in **< 0.05 seconds**.

---

## 3. Deployment & Packaging Architecture

### PyInstaller Build (`build.py`)
Compiles `main.py` into a self-contained executable bundle with embedded `assets/` and `cache/` dependencies.