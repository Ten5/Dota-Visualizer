import matplotlib
matplotlib.use('Agg') 
import warnings
from src.ui.app import DotaRaceApp

from src.visualizer.library_extensions import apply_patches
apply_patches()

if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    app = DotaRaceApp()
    app.mainloop()