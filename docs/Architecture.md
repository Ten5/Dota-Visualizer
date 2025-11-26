# ⚙️ Technical Architecture

## 1. System Overview
The application follows a **Model-View-Controller (MVC)** lite pattern:
* **UI (`src/ui`):** Handles user input using `CustomTkinter`.
* **Data (`src/data`):** Fetches, cleans, and processes Dota 2 data.
* **Visualizer (`src/visualizer`):** Renders the video using `Matplotlib`.

## 2. Key Components

### A. The Runtime Patch (`src/visualizer/patch.py`)
The standard `bar_chart_race` library lacks image support and crashes with modern Matplotlib versions. Instead of forking the library, we use **Runtime Monkey Patching**:
1.  **Icon Injection:** We override `_label_bars` to draw `AnnotationBbox` (images) next to the bars.
2.  **Crash Fix:** We override `make_animation` to fix an FPS argument conflict in Matplotlib `FuncAnimation`.
*Benefit:* The app works with standard `pip install` without needing complex custom library builds.

### B. The Strategy Pattern (`src/data/strategies.py`)
We use the **Strategy Design Pattern** for extensibility.
* **`DataStrategy` (Base Class):** Handles common logic like `_filter_static_months`.
* **Concrete Strategies:** Classes like `KDAStrategy` contain specific math.
* **Optimization:** `_filter_static_months` detects rows where data hasn't changed (idle months) and drops them, reducing rendering time by 50-80% for returning players.

### C. In-Memory Caching (`src/data/api.py`)
* **Match Cache:** `_match_cache` stores the full JSON history. Switching from "KDA" to "Gold" is instant.
* **Asset Cache:** Hero Icons are downloaded once to `assets/hero_images` and reused.

## 3. Rendering Engine
* **Headless Mode:** `matplotlib.use('Agg')` prevents macOS freezing by rendering in memory.
* **Progress Tracking:** We inject a custom `ProgressVideoWriter` into Matplotlib to calculate real % completion (Frame N / Total Frames).

## 4. Dependencies
* **CustomTkinter:** UI.
* **Pandas:** Data Processing.
* **Requests:** API.
* **Matplotlib + Bar_Chart_Race:** Visualization.
* **MoviePy:** Post-processing (Audio/Buffers).