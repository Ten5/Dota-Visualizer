import customtkinter as ctk
import threading
import os
import re
import glob
import platform
import subprocess
import traceback
from tkinter import messagebox
from src.data.api import DotaAPI
from src.data.strategies import (
    MatchesPlayedStrategy, WinsStrategy, WinRateStrategy, Top20WinRateStrategy,
    ItemRaceStrategy, RoleEvolutionStrategy, KDAStrategy, TowerDamageStrategy, 
    LaneStrategy, DamageDealtStrategy, TotalDeathsStrategy, TotalGoldStrategy,
    HeroImpactStrategy, MultiKillStrategy, FarmingEfficiencyStrategy,
    WinStreakStrategy, RoshanClaimsStrategy, BlitzWinsStrategy
)
from src.visualizer.engine import VideoEngine

def open_file_or_folder(path):
    """Cross-platform launcher to open files or folders in native OS applications."""
    if not os.path.exists(path):
        return False
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.call(["open", path])
        elif system == "Windows":
            os.startfile(path)
        else:
            subprocess.call(["xdg-open", path])
        return True
    except Exception as e:
        print(f"Error opening path {path}: {e}")
        return False

class DotaRaceApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Dota 2 History Visualizer - Race Animation Engine")
        self.geometry("960x780")
        try:
            self.minsize(800, 650)
        except Exception:
            pass
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.api = DotaAPI()
        self.is_processing = False
        
        self.strategies = {
            "Hero Impact Score": HeroImpactStrategy,
            "Multi-Kill & Rampage Race": MultiKillStrategy,
            "GPM Farming Efficiency": FarmingEfficiencyStrategy,
            "Win Streak Master": WinStreakStrategy,
            "Roshan & Aegis Claims": RoshanClaimsStrategy,
            "Blitz Stomper (Fastest Victory)": BlitzWinsStrategy,
            "Matches Played": MatchesPlayedStrategy,
            "Hero Masteries": MatchesPlayedStrategy,
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
        
        self.filename_map = {
            "Hero Impact Score": "Impact",
            "Multi-Kill & Rampage Race": "MultiKills",
            "GPM Farming Efficiency": "Farming",
            "Win Streak Master": "Streak",
            "Roshan & Aegis Claims": "Roshan",
            "Blitz Stomper (Fastest Victory)": "Blitz",
            "Matches Played": "Matches",
            "Hero Masteries": "Masteries",
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

        self.quality_presets = {
            "Draft (Fast)":   {"steps": 10, "period": 1000, "dpi": 80},
            "Normal":         {"steps": 20, "period": 1500, "dpi": 100},
            "High (Slow)":    {"steps": 40, "period": 2000, "dpi": 120},
            "Ultra (Cinema)": {"steps": 60, "period": 2500, "dpi": 144}
        }
        
        self.latest_generated_video = None
        self.custom_audio_path = None
        self.create_widgets()

    def create_widgets(self):
        # Header Card
        self.header_card = ctk.CTkFrame(self, corner_radius=12, fg_color="#1e1e2e")
        self.header_card.pack(fill="x", padx=20, pady=(15, 10))
        
        ctk.CTkLabel(
            self.header_card, 
            text="⚔️ Dota 2 History Visualizer 📊", 
            font=("Helvetica", 22, "bold"),
            text_color="#f5c2e7"
        ).pack(pady=(12, 2))
        
        ctk.CTkLabel(
            self.header_card, 
            text="Transform your match history into animated Bar Chart Race videos", 
            font=("Helvetica", 12),
            text_color="#bac2de"
        ).pack(pady=(0, 12))

        # Controls Card
        self.controls_card = ctk.CTkFrame(self, corner_radius=12, fg_color="#1e1e2e")
        self.controls_card.pack(fill="x", padx=20, pady=10)

        # Steam ID Row
        id_frame = ctk.CTkFrame(self.controls_card, fg_color="transparent")
        id_frame.pack(fill="x", padx=15, pady=(12, 4))
        ctk.CTkLabel(id_frame, text="Steam ID (32-bit):", font=("Helvetica", 13, "bold"), width=140, anchor="w").pack(side="left")
        self.entry_id = ctk.CTkEntry(id_frame, placeholder_text="e.g. 70388657", width=340)
        self.entry_id.pack(side="left", fill="x", expand=True)

        # Metric Row
        metric_frame = ctk.CTkFrame(self.controls_card, fg_color="transparent")
        metric_frame.pack(fill="x", padx=15, pady=4)
        ctk.CTkLabel(metric_frame, text="Select Metric:", font=("Helvetica", 13, "bold"), width=140, anchor="w").pack(side="left")
        self.strategy_var = ctk.StringVar(value="Matches Played")
        self.dropdown = ctk.CTkOptionMenu(metric_frame, values=list(self.strategies.keys()), variable=self.strategy_var, width=340)
        self.dropdown.pack(side="left", fill="x", expand=True)

        # Aspect Ratio & Theme Row
        opts_frame = ctk.CTkFrame(self.controls_card, fg_color="transparent")
        opts_frame.pack(fill="x", padx=15, pady=4)
        ctk.CTkLabel(opts_frame, text="Aspect Ratio & Theme:", font=("Helvetica", 13, "bold"), width=140, anchor="w").pack(side="left")
        
        self.aspect_var = ctk.StringVar(value="16:9 Landscape")
        self.aspect_dropdown = ctk.CTkOptionMenu(opts_frame, values=["16:9 Landscape", "9:16 Vertical Shorts"], variable=self.aspect_var, width=165)
        self.aspect_dropdown.pack(side="left", padx=(0, 10))

        self.theme_var = ctk.StringVar(value="Dire Crimson")
        self.theme_dropdown = ctk.CTkOptionMenu(opts_frame, values=["Dire Crimson", "Radiant Gold", "Midnight Cyberpunk"], variable=self.theme_var, width=165)
        self.theme_dropdown.pack(side="left", fill="x", expand=True)

        # Quality & Audio File Row
        quality_frame = ctk.CTkFrame(self.controls_card, fg_color="transparent")
        quality_frame.pack(fill="x", padx=15, pady=(4, 12))
        ctk.CTkLabel(quality_frame, text="Quality & Music:", font=("Helvetica", 13, "bold"), width=140, anchor="w").pack(side="left")
        self.quality_var = ctk.StringVar(value="Normal")
        self.quality_dropdown = ctk.CTkOptionMenu(quality_frame, values=list(self.quality_presets.keys()), variable=self.quality_var, width=165)
        self.quality_dropdown.pack(side="left", padx=(0, 10))

        self.btn_audio = ctk.CTkButton(quality_frame, text="🎵 Select Custom Music", command=self.on_select_music, fg_color="#313244", hover_color="#45475a", height=28, width=165)
        self.btn_audio.pack(side="left", fill="x", expand=True)

        # Generate Button
        self.btn_run = ctk.CTkButton(
            self.controls_card, 
            text="▶️  Generate Video", 
            command=self.on_generate, 
            font=("Helvetica", 14, "bold"),
            height=42,
            fg_color="#89b4fa",
            hover_color="#74c7ec",
            text_color="#11111b"
        )
        self.btn_run.pack(fill="x", padx=15, pady=(0, 12))

        # Media & File Action Card
        self.actions_card = ctk.CTkFrame(self, corner_radius=12, fg_color="#1e1e2e")
        self.actions_card.pack(fill="x", padx=20, pady=10)

        actions_inner = ctk.CTkFrame(self.actions_card, fg_color="transparent")
        actions_inner.pack(fill="x", padx=15, pady=12)

        self.btn_open_folder = ctk.CTkButton(
            actions_inner,
            text="📂 Open Output Folder",
            command=self.on_open_folder,
            fg_color="#313244",
            hover_color="#45475a",
            height=36
        )
        self.btn_open_folder.pack(side="left", expand=True, fill="x", padx=5)

        self.btn_play_latest = ctk.CTkButton(
            actions_inner,
            text="▶️ Play Latest Video",
            command=self.on_play_latest,
            fg_color="#a6e3a1",
            hover_color="#94e2d5",
            text_color="#11111b",
            height=36
        )
        self.btn_play_latest.pack(side="left", expand=True, fill="x", padx=5)

        self.btn_delete_videos = ctk.CTkButton(
            actions_inner,
            text="🗑️ Clear Videos",
            command=self.on_delete_videos,
            fg_color="#f38ba8",
            hover_color="#eba0ac",
            text_color="#11111b",
            height=36
        )
        self.btn_delete_videos.pack(side="left", expand=True, fill="x", padx=5)

        # Progress & Console Card
        self.console_card = ctk.CTkFrame(self, corner_radius=12, fg_color="#1e1e2e")
        self.console_card.pack(fill="both", expand=True, padx=20, pady=(10, 15))

        self.progress_label = ctk.CTkLabel(self.console_card, text="Ready", text_color="#cdd6f4", font=("Helvetica", 12, "bold"))
        self.progress_label.pack(pady=(12, 2))
        
        self.progress = ctk.CTkProgressBar(self.console_card, width=640, height=12)
        self.progress.pack(pady=(0, 10))
        self.progress.set(0)
        
        self.log_box = ctk.CTkTextbox(self.console_card, fg_color="#11111b", text_color="#a6adc8", font=("Courier", 12))
        self.log_box.pack(fill="both", expand=True, padx=15, pady=(0, 15))
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
        self.progress_label.configure(text=f"Rendering: {int(percent * 100)}%", text_color="#89b4fa")

    def enable_ui(self):
        self.btn_run.configure(state="normal")
        self.progress_label.configure(text="Generation Complete!", text_color="#a6e3a1")

    def on_select_music(self):
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="Select Background Music Track",
            filetypes=[("Audio Files", "*.mp3 *.wav *.aac *.m4a")]
        )
        if file_path:
            self.custom_audio_path = file_path
            filename = os.path.basename(file_path)
            self.btn_audio.configure(text=f"🎵 {filename[:15]}...", fg_color="#a6e3a1", text_color="#11111b")
            self.log(f"Selected audio track: {filename}")

    def on_open_folder(self):
        os.makedirs("output", exist_ok=True)
        open_file_or_folder("output")

    def on_play_latest(self):
        os.makedirs("output", exist_ok=True)
        if self.latest_generated_video and os.path.exists(self.latest_generated_video):
            open_file_or_folder(self.latest_generated_video)
            return

        videos = glob.glob("output/*.mp4")
        if not videos:
            messagebox.showinfo("No Videos Found", "No generated videos found in output folder.")
            return

        # Find most recently modified mp4
        latest_mp4 = max(videos, key=os.path.getmtime)
        open_file_or_folder(latest_mp4)

    def on_delete_videos(self):
        os.makedirs("output", exist_ok=True)
        videos = glob.glob("output/*.mp4")
        if not videos:
            messagebox.showinfo("No Videos", "No generated videos to delete in output folder.")
            return

        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete all {len(videos)} video(s) in output/ ?")
        if confirm:
            deleted_count = 0
            for v in videos:
                try:
                    os.remove(v)
                    deleted_count += 1
                except Exception as e:
                    print(f"Error deleting {v}: {e}")
            self.latest_generated_video = None
            self.log(f"Deleted {deleted_count} video file(s) from output/")
            messagebox.showinfo("Deleted", f"Successfully deleted {deleted_count} video file(s).")

    def on_generate(self):
        player_id = self.entry_id.get().strip()
        if not player_id or not player_id.isdigit():
            messagebox.showwarning("Invalid Steam ID", "Please enter a valid numeric 32-bit Steam ID.")
            return

        self.btn_run.configure(state="disabled")
        self.progress.set(0)
        self.progress_label.configure(text="Initializing...", text_color="#f9e2af")
        
        selected_strat_name = self.strategy_var.get()
        quality_name = self.quality_var.get()
        settings = self.quality_presets[quality_name]

        thread = threading.Thread(target=self.run_process, args=(player_id, selected_strat_name, settings), daemon=True)
        thread.start()

    def run_process(self, player_id, strat_name, settings):
        try:
            self.log(f"Starting pipeline for Steam ID: {player_id}")
            matches = DotaAPI.fetch_all_matches(player_id, self.log)
            if not matches:
                raise Exception("No matches found for Steam ID")
            
            hero_map = DotaAPI.get_hero_map()
            DotaAPI.download_hero_images(hero_map)

            profile = DotaAPI.get_player_profile(player_id)
            player_name = profile['name']
            avatar_img = profile['avatar']
            
            self.log(f"Player: {player_name}")

            strategy_class = self.strategies[strat_name]
            strategy = strategy_class()
            self.log(f"Processing metric: {strategy.name}")
            
            df, start_year = strategy.process(matches, hero_map)
            if df.empty or len(df) < 2:
                self.log(f"Notice: Insufficient time-series data for '{strat_name}'. At least 2 active months are required.")
                self.progress_label.configure(text="Insufficient Data", text_color="#f9e2af")
                return

            os.makedirs("output", exist_ok=True)
            
            safe_name = re.sub(r'[^a-zA-Z0-9]', '', player_name)
            if not safe_name: safe_name = f"Player{player_id}"
            
            short_strat = self.filename_map.get(strat_name, "Video")
            aspect_ratio = "9:16" if "Vertical" in self.aspect_var.get() else "16:9"
            theme_name = self.theme_var.get()

            base_filename = f"{safe_name}_{short_strat}_{aspect_ratio.replace(':', 'x')}"
            temp_path = f"output/temp_{base_filename}.mp4"
            final_path = f"output/{base_filename}.mp4"
            
            self.log(f"Target video: {base_filename}.mp4")
            self.log(f"Rendering ({self.quality_var.get()} | {aspect_ratio} | {theme_name})...")
            video_title = f"{player_name}\n{strategy.name} ({start_year}-Present)"
            
            VideoEngine.render_race(
                df, temp_path, 
                title=video_title, 
                avatar_img=avatar_img,
                progress_callback=self.update_progress_ui,
                steps_per_period=settings['steps'],
                period_length=settings['period'],
                dpi=settings['dpi'],
                aspect_ratio=aspect_ratio,
                theme_name=theme_name,
                patch_overlay=True
            )
            
            self.log("Adding Music & Result Buffer...")
            VideoEngine.add_audio(temp_path, final_path, music_file=self.custom_audio_path)
            if os.path.exists(temp_path): os.remove(temp_path)

            self.latest_generated_video = final_path
            self.log(f"DONE! Saved video to {final_path}")

        except Exception as e:
            self.log(f"Error: {e}")
            self.progress_label.configure(text="Failed", text_color="#f38ba8")
            traceback.print_exc()
        finally:
            self.after(0, self.enable_ui)