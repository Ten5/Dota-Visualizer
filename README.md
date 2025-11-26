# Dota 2 History Visualizer

A Python application that turns your Dota 2 match history into animated "Bar Chart Race" videos. Watch your most played heroes, win rates, and gameplay habits evolve over the last decade.

## 🚀 Features
- **Dynamic Animations:** Visualize your history from 2015 to present.
- **12 Unique Strategies:** Race by Matches, KDA, Gold Farmed, Tower Damage, Role Evolution, and more.
- **Hero Icons:** Automatically fetches and displays hero icons on the bars (via custom Runtime Patch).
- **Dark Mode:** Sleek "Dota 2" styled dark theme for professional-looking videos.
- **Smart Optimizations:**
    - **Fast Forward:** Automatically skips months where you didn't play.
    - **Caching:** Instant re-runs for different metrics without re-downloading data.
- **Audio Integration:** Adds background music and a 2-second "Result Buffer" at the end.

## 🛠️ Installation

### 1. Prerequisites
- **Python 3.10+**
- **FFmpeg:** Required for video rendering.
    - *Mac:* `brew install ffmpeg`
    - *Windows:* Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) and add to PATH.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

(Dependencies: customtkinter, pandas, requests, bar_chart_race, matplotlib, moviepy, pillow)

▶️ How to Run
Add Music (Optional): Drop any .mp3 files into the assets/music/ folder. The app will pick one at random.

Run the App:

```bash
python main.py
```

Generate:

Enter your Steam ID (32-bit integer).

Select a Metric (e.g., "KDA Ratio" or "Total Gold").

Click Generate Video.

📂 Output
Videos are saved in the output/ folder with concise filenames like Dendi_KDA.mp4.

Running Tests
To ensure everything is working correctly:

```bash
python -m unittest discover tests
```