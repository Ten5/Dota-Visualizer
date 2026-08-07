import warnings
from src.ui.app import DotaRaceApp

if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    app = DotaRaceApp()
    app.mainloop()