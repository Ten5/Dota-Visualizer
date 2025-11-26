import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.animation import FuncAnimation
import os
from bar_chart_race._make_chart import _BarChartRace

# ==========================================
# FIX 1: HERO ICONS ON BARS
# ==========================================
def get_hero_image(name, folder="assets/hero_images"):
    """Finds the image file for a given hero name."""
    path = os.path.join(folder, f"{name}.png")
    if os.path.exists(path): return path
    
    safe_name = name.replace("/", "_")
    path = os.path.join(folder, f"{safe_name}.png")
    if os.path.exists(path): return path
    return None

def patched_label_bars(self, ax, curr_vals, curr_ranks):
    font_dict = self.shared_fontdict.copy()
    font_dict['size'] = self.bar_label_size
    
    # 1. Draw Text Labels
    for i, (val, rank) in enumerate(zip(curr_vals, curr_ranks)):
        if rank > self.n_bars: continue
        label_txt = f'{val:,.0f}'
        ax.text(val, rank - 1, f'  {label_txt}', ha='left', va='center', **font_dict)

    # 2. Draw Hero Icons
    yticks = ax.get_yticklabels()
    for label in yticks:
        hero_name = label.get_text()
        y_pos = label.get_position()[1]
        
        if 0 <= y_pos < self.n_bars:
            img_path = get_hero_image(hero_name)
            if img_path:
                try:
                    img = plt.imread(img_path)
                    imagebox = OffsetImage(img, zoom=0.4)
                    imagebox.image.axes = ax
                    ab = AnnotationBbox(imagebox, (0, y_pos), xybox=(-25, 0), 
                                      xycoords='data', boxcoords="offset points", frameon=False)
                    ax.add_artist(ab)
                except Exception: pass

# ==========================================
# FIX 2: MATPLOTLIB COMPATIBILITY (THE CRASH FIX)
# ==========================================
def patched_make_animation(self):
    """
    Replaces the library's default animation loop to fix the
    'RuntimeError: Passing in values for arguments fps...' bug.
    """
    def init():
        self.ax.clear()
        self.ax.set_facecolor(self.fig.get_facecolor())
        
    def update(i):
        # --- FIX: Use 'plot_bars' instead of '_plot_bars' ---
        # The library version installed on this machine uses the public name.
        if hasattr(self, 'plot_bars'):
            self.plot_bars(i)
        elif hasattr(self, '_plot_bars'):
            self._plot_bars(i)
        elif hasattr(self, 'anim_func'):
            self.anim_func(i)
        # ----------------------------------------------------
        
    anim = FuncAnimation(
        self.fig, 
        update, 
        init_func=init, 
        frames=len(self.df_values),
        interval=self.period_length / self.steps_per_period, 
        repeat=False
    )
    
    try:
        if isinstance(self.writer, str):
            ret_val = anim.save(self.filename, fps=self.fps, writer=self.writer)
        else:
            # If writer is an object (Progress Bar), do not pass fps
            ret_val = anim.save(self.filename, writer=self.writer)
            
    except Exception as e:
        print(f"Animation Failed: {e}")
        raise e
        
    return ret_val

# ==========================================
# APPLY PATCHES
# ==========================================
def apply_patches():
    print("Applying Runtime Patches:")
    print("  1. Hero Icons... [OK]")
    print("  2. Matplotlib Fix... [OK]")
    _BarChartRace._label_bars = patched_label_bars
    _BarChartRace.make_animation = patched_make_animation