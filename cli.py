import argparse
import sys
import os
import re
import traceback

from src.data.api import DotaAPI
from src.data.strategies import (
    MatchesPlayedStrategy, WinsStrategy, WinRateStrategy, Top20WinRateStrategy,
    ItemRaceStrategy, RoleEvolutionStrategy, KDAStrategy, TowerDamageStrategy, 
    LaneStrategy, DamageDealtStrategy, TotalDeathsStrategy, TotalGoldStrategy,
    HeroVersatilityStrategy
)
from src.visualizer.engine import VideoEngine

STRATEGIES = {
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
    "Total Gold (Millions)": TotalGoldStrategy,
    "Hero Versatility": HeroVersatilityStrategy
}

FILENAME_MAP = {
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
    "Total Gold (Millions)": "Gold",
    "Hero Versatility": "Versatility"
}

QUALITY_PRESETS = {
    "Draft":  {"steps": 10, "period": 1000, "dpi": 80},
    "Normal": {"steps": 20, "period": 1500, "dpi": 100},
    "High":   {"steps": 40, "period": 2000, "dpi": 120},
    "Ultra":  {"steps": 60, "period": 2500, "dpi": 144}
}

def print_log(msg):
    print(f"[DOTA-VISUALIZER] {msg}")

def main():
    parser = argparse.ArgumentParser(description="Dota 2 History Visualizer CLI Engine")
    parser.add_argument("--player_id", type=str, required=True, help="32-bit Steam ID (e.g. 70388657)")
    parser.add_argument("--metric", type=str, default="Matches Played", choices=list(STRATEGIES.keys()), help="Visualization metric strategy")
    parser.add_argument("--quality", type=str, default="Normal", choices=list(QUALITY_PRESETS.keys()), help="Render quality preset")
    parser.add_argument("--aspect_ratio", type=str, default="16:9", choices=["16:9", "9:16"], help="Aspect ratio preset")
    parser.add_argument("--theme", type=str, default="Dire Crimson", choices=["Dire Crimson", "Radiant Gold", "Midnight Cyberpunk"], help="UI Theme preset")
    parser.add_argument("--audio_file", type=str, default=None, help="Custom background audio file path")
    parser.add_argument("--output_dir", type=str, default="output", help="Output directory for generated MP4 video")
    
    args = parser.parse_args()

    player_id = args.player_id.strip()
    if not player_id.isdigit():
        print_log(f"Error: Invalid Steam ID '{player_id}'. Must be numeric.")
        sys.exit(1)

    print_log(f"Starting video generation pipeline for Steam ID: {player_id}")
    print_log(f"Metric: {args.metric} | Quality: {args.quality} | Aspect Ratio: {args.aspect_ratio} | Theme: {args.theme}")

    try:
        matches = DotaAPI.fetch_all_matches(player_id, print_log)
        if not matches:
            print_log("Error: No matches found for Steam ID.")
            sys.exit(1)

        hero_map = DotaAPI.get_hero_map()
        DotaAPI.download_hero_images(hero_map)

        profile = DotaAPI.get_player_profile(player_id)
        player_name = profile['name']
        avatar_img = profile['avatar']
        print_log(f"Player: {player_name}")

        strategy_class = STRATEGIES[args.metric]
        strategy = strategy_class()

        df, start_year = strategy.process(matches, hero_map)
        if df.empty or len(df) < 2:
            print_log(f"Notice: Insufficient time-series data for '{args.metric}'. At least 2 active months are required to render an animation.")
            sys.exit(0)

        os.makedirs(args.output_dir, exist_ok=True)

        safe_name = re.sub(r'[^a-zA-Z0-9]', '', player_name)
        if not safe_name: safe_name = f"Player{player_id}"
        
        short_strat = FILENAME_MAP.get(args.metric, "Video")
        base_filename = f"{safe_name}_{short_strat}_{args.aspect_ratio.replace(':', 'x')}"
        temp_path = os.path.join(args.output_dir, f"temp_{base_filename}.mp4")
        final_path = os.path.join(args.output_dir, f"{base_filename}.mp4")

        settings = QUALITY_PRESETS[args.quality]
        video_title = f"{player_name}\n{strategy.name} ({start_year}-Present)"

        def cli_progress(p):
            percent = int(p * 100)
            sys.stdout.write(f"\r[RENDER] Progress: {percent}% ")
            sys.stdout.flush()

        VideoEngine.render_race(
            df, temp_path,
            title=video_title,
            avatar_img=avatar_img,
            progress_callback=cli_progress,
            steps_per_period=settings['steps'],
            period_length=settings['period'],
            dpi=settings['dpi'],
            aspect_ratio=args.aspect_ratio,
            theme_name=args.theme,
            patch_overlay=True
        )
        print()
        print_log("Adding Background Music...")
        VideoEngine.add_audio(temp_path, final_path, music_file=args.audio_file)
        if os.path.exists(temp_path): os.remove(temp_path)

        print_log(f"SUCCESS! Rendered video saved to: {final_path}")

    except Exception as e:
        print_log(f"Error executing CLI pipeline: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
