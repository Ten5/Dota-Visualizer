# 📖 User Guide: Execution Modes, Local Testing & Packaging

This guide explains how to run, test, and package the **Dota 2 History Visualizer** across 3 local execution modes (GUI, CLI, and Standalone Executable).

---

## ⚡ 1. Local Desktop GUI (`main.py`)

1. **Launch the application:**
   ```bash
   python main.py
   ```
2. **Features of the GUI:**
   - **Centered Dedicated Window:** Launches centered on screen with custom application icon (`assets/icon.png`).
   - **Steam ID Input:** Enter your 32-bit Steam ID (found in Dotabuff/OpenDota URL, e.g. `70388657`).
   - **Metric Selection:** Choose from 11 statistical strategies.
   - **Render Quality Presets:** Draft (~2-3s), Normal (~5-10s), High (~10-15s), Ultra (~15-25s).
   - **32-Color Dynamic Palette:** Bar colors rotate among 32+ vibrant colors.
   - **Media & Folder Controls:**
     - **`📂 Open Output Folder`**: Opens `output/` in macOS Finder / Windows Explorer.
     - **`▶️ Play Latest Video`**: Opens the latest `.mp4` video in default OS media player.
     - **`🗑️ Clear Videos`**: Safely cleans generated output files.

---

## 💻 2. Headless CLI (`cli.py`)

Generate videos directly from the command line without opening the GUI:

```bash
# Basic run
python cli.py --player_id 70388657

# Custom metric and quality
python cli.py --player_id 70388657 --metric "KDA Ratio (Efficiency)" --quality High

# Show help
python cli.py --help
```

---

## 📦 3. Standalone Application Build (`build.py`)

Package the Python application into a standalone executable app bundle using PyInstaller:

```bash
python build.py
```
- Bundles all required assets (`assets/icon.png`, hero images, music) and SQLite database dependencies.
- Output executable bundle is created at `dist/Dota2Visualizer`.

---

## 🧪 4. Running Automated Unit Tests

Run the full unittest test suite:
```bash
python -m unittest discover tests
```