# 🧪 Testing Guide

This project uses `unittest` to ensure stability across Data, Logic, and UI layers.

## 📂 Test Structure
```text
tests/
├── data/
│   ├── test_api.py         # Tests Network calls, Caching, and Pagination
│   └── test_strategies.py  # Tests Math Logic (KDA, WinRates) and Filters
├── ui/
│   └── test_app.py         # Tests UI Logic, Button Clicks, and Error Handling
└── visualizer/
    ├── test_engine.py      # Tests Rendering arguments
    └── test_patch.py       # Tests the Runtime Patches (Image finding, etc.)
```

🚀 Running Tests
Run All Tests (Recommended)
From the root directory (dota_visualizer/), run:

```Bash
python -m unittest discover tests
```

Run Specific Modules
```Bash
python -m unittest tests/data/test_strategies.py
python -m unittest tests/ui/test_app.py
```

🛠️ How We Test "Hard" Things
1. Testing the UI without a Window
We use a Fake Library Injection technique in test_app.py.

We create a FakeCTk class that mimics CustomTkinter but does nothing.

We inject this into sys.modules['customtkinter'].

This allows us to test "Button Clicks" and "Log Messages" in the console without opening a GUI.

2. Testing the API without Spamming OpenDota
We use unittest.mock.patch to intercept requests.get.

We feed "Fake JSON" into the system to ensure it handles Wins, Losses, and Empty Histories correctly without touching the internet.