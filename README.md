# Dota 2 History Visualizer ⚔️📊

A Python desktop application that transforms your Dota 2 match history into sleek, animated **"Bar Chart Race"** videos. Watch your most played heroes, win rates, KDA ratios, damage output, hero pool versatility, and role evolutions unfold from your earliest matches to the present day.

![App Icon](assets/icon.png)

---

## 🚀 Key Features

- **📱 9:16 Vertical Shorts & 16:9 Landscape:** Export videos in standard `16:9` landscape or `9:16` vertical video formatted for **TikTok, YouTube Shorts, and Instagram Reels**.
- **🎨 UI Theme Engine:** Switch between curated color themes (*Dire Crimson*, *Radiant Gold*, *Midnight Cyberpunk*).
- **⚔️ Dota 2 Patch Timeline Overlay:** Displays historical patch release labels (e.g. *PATCH 7.33 - NEW FRONTIERS*, *PATCH 7.36*) alongside monthly date stamps.
- **⚡ Dynamic Period Pacing:** Automatically speeds up during quiet/inactive months (fast-forwarding in ~0.16s) and slows down during intense gaming sprees & rank swaps for cinematic focus.
- **🎵 Custom Background Music Selector:** Select custom `.mp3` or `.wav` audio files directly from the GUI.
- **📊 12 Unique Statistical Metrics:**
  - *Matches Played*, *Total Wins*, *Win Rate %*, *KDA Ratio (Efficiency)*, *Role Evolution (Core vs Support)*, *Laning Preference*, *Tower Damage (Thousands)*, *Total Damage (Millions)*, *Total Gold Farmed (Millions)*, *Total Deaths*, *Most Purchased Items*, and *Hero Versatility (Unique Played)*.
- **⚡ Blazing-Fast OpenCV Rendering Engine:** Custom native 2D canvas drawer rendering videos in seconds (**250+ FPS**) with FFmpeg hardware acceleration (`h264_videotoolbox` / `h264_nvenc`).
- **💾 SQLite Persistent Disk Caching:** Stores full match histories locally (`cache/dota_visualizer.db`) with instant (<0.05s) startup loading.
- **🎬 Direct Media Controls:** Built-in GUI buttons to **Open Output Folder**, **Play Latest Video**, and **Clear Output Videos**.

---

## 🛠️ Requirements & Installation

### 1. Prerequisites
- **Python 3.10+**
- **FFmpeg** (Required for MP4 video encoding)
  - **macOS:** `brew install ffmpeg`
  - **Linux:** `sudo apt install ffmpeg`
  - **Windows:** Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) and add `ffmpeg/bin` to system PATH.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## ▶️ Execution Modes

### Mode 1: Desktop GUI Application (Local UI)
```bash
python main.py
```
1. Enter your 32-bit Steam ID (e.g. `70388657` for Dendi).
2. Select Metric, Aspect Ratio (`16:9 Landscape` or `9:16 Vertical Shorts`), Theme, and Render Quality.
3. (Optional) Select a custom background `.mp3` music file.
4. Click **▶️ Generate Video**.

---

### Mode 2: Headless Command Line Interface (CLI)
Run video generation directly from the terminal with full customization:
```bash
python cli.py --player_id 70388657 --metric "Hero Versatility" --aspect_ratio "9:16" --theme "Midnight Cyberpunk" --quality "Normal"
```
*CLI Flags:*
- `--player_id`: 32-bit Steam ID (required).
- `--metric`: Visualization strategy name.
- `--aspect_ratio`: `16:9` or `9:16`.
- `--theme`: `Dire Crimson`, `Radiant Gold`, or `Midnight Cyberpunk`.
- `--audio_file`: Path to custom `.mp3` audio track.
- `--quality`: `Draft`, `Normal`, `High`, `Ultra`.

---

### Mode 3: Standalone Executable Build (PyInstaller)
Package the application into a standalone desktop application bundle:
```bash
python build.py
```

---

## 🧪 Running Unit Tests

Run the complete automated unit test suite:
```bash
python -m unittest discover tests
```