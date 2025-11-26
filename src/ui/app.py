import customtkinter as ctk
import threading
import os
import re # For filename sanitization
import traceback
from src.data.api import DotaAPI
from src.data.strategies import (
    MatchesPlayedStrategy, WinsStrategy, WinRateStrategy, Top20WinRateStrategy,
    ItemRaceStrategy, RoleEvolutionStrategy, KDAStrategy, TowerDamageStrategy, 
    LaneStrategy, DamageDealtStrategy, TotalDeathsStrategy, TotalGoldStrategy
)
from src.visualizer.engine import VideoEngine

class DotaRaceApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Dota 2 Visualizer Suite")
        self.geometry("700x700") # Taller for new dropdown
        self.resizable(False, False)
        
        self.strategies = {
            "Matches Played": MatchesPlayedStrategy,
            "Total Wins": WinsStrategy,
            "Win Rate % (Top 20 Mains)": Top20WinRateStrategy,
            "Most Purchased Items": ItemRaceStrategy,
            "Role Evolution": RoleEvolutionStrategy,
            "KDA Ratio (Efficiency)": KDAStrategy,
            "Tower Damage (Thousands)": TowerDamageStrategy,
            "Laning Preference": LaneStrategy,
            "Total Damage (Millions)": DamageDealtStrategy,
            "Total Deaths": TotalDeathsStrategy,
            "Total Gold (Millions)": TotalGoldStrategy
        }
        
        # --- NEW: Short Codes for Filenames ---
        self.filename_map = {
            "Matches Played": "Matches",
            "Total Wins": "Wins",
            "Win Rate % (Top 20 Mains)": "WinRate",
            "Most Purchased Items": "Items",
            "Role Evolution": "Roles",
            "KDA Ratio (Efficiency)": "KDA",
            "Tower Damage (Thousands)": "TowerDmg",
            "Laning Preference": "Lanes",
            "Total Damage (Millions)": "Damage",
            "Total Deaths": "Deaths",
            "Total Gold (Millions)": "Gold"
        }

        # Steps: How many frames per month (Higher = Smoother, Slower)
        # Period: How long a month lasts on screen (Higher = Slower pace)
        # DPI: Resolution (Higher = Sharper text/icons)
        self.quality_presets = {
            "Draft (Fast)":   {"steps": 10, "period": 1000, "dpi": 80},  # ~2-3 mins
            "Normal":         {"steps": 20, "period": 1500, "dpi": 100}, # ~10-15 mins
            "High (Slow)":    {"steps": 50, "period": 2500, "dpi": 120}, # ~45-60 mins
            "Ultra (Cinema)": {"steps": 60, "period": 3000, "dpi": 144}  # ~90+ mins
        }
        
        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(self, text="Dota 2 History Visualizer", font=("Roboto", 24, "bold")).pack(pady=20)
        self.entry_id = ctk.CTkEntry(self, placeholder_text="Enter Steam ID", width=300)
        self.entry_id.pack(pady=10)
        
        # Strategy Selection
        ctk.CTkLabel(self, text="Select Metric:", font=("Roboto", 12)).pack(pady=(10, 0))
        self.strategy_var = ctk.StringVar(value="Matches Played")
        self.dropdown = ctk.CTkOptionMenu(self, values=list(self.strategies.keys()), variable=self.strategy_var, width=200)
        self.dropdown.pack(pady=5)

        # Quality Selection
        ctk.CTkLabel(self, text="Render Quality:", font=("Roboto", 12)).pack(pady=(10, 0))
        self.quality_var = ctk.StringVar(value="Normal")
        self.quality_dropdown = ctk.CTkOptionMenu(
            self, 
            values=list(self.quality_presets.keys()), 
            variable=self.quality_var, 
            width=200
        )
        self.quality_dropdown.pack(pady=5)

        self.btn_run = ctk.CTkButton(self, text="Generate Video", command=self.on_generate, height=40)
        self.btn_run.pack(pady=20)
        
        self.progress_label = ctk.CTkLabel(self, text="Ready", text_color="gray")
        self.progress_label.pack(pady=(10, 0))
        
        self.progress = ctk.CTkProgressBar(self, width=400)
        self.progress.pack(pady=5)
        self.progress.set(0)
        
        self.log_box = ctk.CTkTextbox(self, width=600, height=200)
        self.log_box.pack(pady=10)
        self.log_box.configure(state="disabled")

    def log(self, msg):
        self.after(0, lambda: self._log_impl(msg))
    def _log_impl(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
    
    def update_progress_ui(self, percent_float):
        self.after(0, lambda: self._update_progress_impl(percent_float))
    def _update_progress_impl(self, percent):
        self.progress.set(percent)
        self.progress_label.configure(text=f"Rendering: {int(percent * 100)}%")

    def enable_ui(self):
        self.btn_run.configure(state="normal")
        self.progress_label.configure(text="Generation Complete!", text_color="green")

    def on_generate(self):
        player_id = self.entry_id.get()
        if not player_id: return
        self.btn_run.configure(state="disabled")
        self.progress.set(0)
        self.progress_label.configure(text="Initializing...", text_color="white")
        
        selected_strat_name = self.strategy_var.get()
        
        quality_name = self.quality_var.get()
        settings = self.quality_presets[quality_name]

        thread = threading.Thread(target=self.run_process, args=(player_id, selected_strat_name, settings))
        thread.start()

    def run_process(self, player_id, strat_name, settings):
        try:
            self.log(f"Starting for ID: {player_id}")
            matches = DotaAPI.fetch_all_matches(player_id, self.log)
            if not matches: raise Exception("No matches found")
            
            hero_map = DotaAPI.get_hero_map()
            
            # Ensure icons exist
            DotaAPI.download_hero_images(hero_map)

            profile = DotaAPI.get_player_profile(player_id)
            player_name = profile['name']
            avatar_img = profile['avatar']
            
            self.log(f"Found Player: {player_name}")
            # ----------------------------------------

            strategy_class = self.strategies[strat_name]
            strategy = strategy_class()
            self.log(f"Processing mode: {strategy.name}")
            
            df, start_year = strategy.process(matches, hero_map)

            # --- NEW: Concise Filename Logic ---
            os.makedirs("output", exist_ok=True)
            
            # 1. Sanitize Name (Remove emojis, spaces, slashes)
            safe_name = re.sub(r'[^a-zA-Z0-9]', '', player_name)
            if not safe_name: safe_name = f"Player{player_id}"
            
            # 2. Get Short Strategy Code
            short_strat = self.filename_map.get(strat_name, "Video")
            
            # 3. Form Filename: "Dendi_KDA.mp4"
            base_filename = f"{safe_name}_{short_strat}"
            temp_path = f"output/temp_{base_filename}.mp4"
            final_path = f"output/{base_filename}.mp4"
            # -----------------------------------
            
            self.log(f"Output target: {base_filename}.mp4")
            self.log(f"Rendering ({self.quality_var.get()})...")
            video_title = f"{player_name}\n{strategy.name} ({start_year}-Present)"
            
            VideoEngine.render_race(
                df, temp_path, 
                title=video_title, 
                avatar_img=avatar_img,
                progress_callback=self.update_progress_ui,
                steps_per_period=settings['steps'],
                period_length=settings['period'],
                dpi=settings['dpi']
            )
            
            self.log("Adding Music & Buffer...")
            VideoEngine.add_audio(temp_path, final_path)
            if os.path.exists(temp_path): os.remove(temp_path)
            self.log(f"DONE! Saved to {final_path}")

        except Exception as e:
            self.log(f"Error: {e}")
            self.progress_label.configure(text="Failed", text_color="red")
            traceback.print_exc()
        finally:
            self.after(0, self.enable_ui)