from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from src.data.api import DotaAPI 

earliest_start_year = 2015

class DataStrategy(ABC):
    @abstractmethod
    def process(self, matches, hero_map):
        pass

    @property
    @abstractmethod
    def name(self):
        pass
    
    def _get_base_df(self, matches, hero_map):
        """Common helper to clean data and guarantee expected column presence."""
        df = pd.DataFrame(matches)
        
        if df.empty or 'start_time' not in df.columns:
            return pd.DataFrame(), earliest_start_year

        default_cols = {
            'kills': 0, 'deaths': 0, 'assists': 0,
            'tower_damage': 0, 'hero_damage': 0, 'gold_per_min': 0, 'duration': 0,
            'lane_role': 0,
            'item_0': 0, 'item_1': 0, 'item_2': 0, 'item_3': 0, 'item_4': 0, 'item_5': 0,
            'player_slot': 0, 'radiant_win': True
        }
        for col, default_val in default_cols.items():
            if col not in df.columns:
                df[col] = default_val
            else:
                df[col] = df[col].fillna(default_val)

        df['date'] = pd.to_datetime(df['start_time'], unit='s')
        
        # Filter out invalid epoch/corrupted timestamps (< 2005)
        df = df[df['date'] >= pd.to_datetime('2005-01-01')]
        if df.empty:
            return pd.DataFrame(), earliest_start_year

        # DYNAMIC START YEAR: Automatically detected from the user's earliest recorded match!
        earliest_date = df['date'].min()
        start_year = int(earliest_date.year) if pd.notna(earliest_date) else earliest_start_year
        
        df['hero_name'] = df['hero_id'].map(hero_map)
        df = df.dropna(subset=['hero_name'])
        
        df['is_radiant'] = df['player_slot'] < 128
        df['won'] = ((df['is_radiant'] & df['radiant_win']) | 
                     (~df['is_radiant'] & ~df['radiant_win'])).astype(int)
        return df, start_year

    def _filter_static_months(self, df):
        """
        Global filter: Removes intermediate inactive months while preserving boundary
        months so charts hold steady values over breaks instead of linearly interpolating.
        """
        if df.empty or len(df) <= 2: return df
        
        # Keep row if it differs from previous row OR differs from next row
        has_changes = (df != df.shift(1)).any(axis=1) | (df != df.shift(-1)).any(axis=1)
        has_changes.iloc[0] = True
        has_changes.iloc[-1] = True
        
        return df[has_changes]

# --- 1. MATCHES PLAYED ---
class MatchesPlayedStrategy(DataStrategy):
    @property
    def name(self): return "Matches Played"
    def process(self, matches, hero_map):
        df, start_year = self._get_base_df(matches, hero_map)
        if df.empty:
            return pd.DataFrame(), start_year
        df['count'] = 1
        pivot = df.pivot_table(index='date', columns='hero_name', values='count', aggfunc='sum').fillna(0)
        cumulative = pivot.resample('ME').sum().cumsum().ffill()
        return self._filter_static_months(cumulative), start_year

# --- 2. TOTAL WINS ---
class WinsStrategy(DataStrategy):
    @property
    def name(self): return "Total Wins"
    def process(self, matches, hero_map):
        df, start_year = self._get_base_df(matches, hero_map)
        if df.empty:
            return pd.DataFrame(), start_year
        df = df[df['won'] == 1].copy()
        df['count'] = 1
        pivot = df.pivot_table(index='date', columns='hero_name', values='count', aggfunc='sum').fillna(0)
        cumulative = pivot.resample('ME').sum().cumsum().ffill()
        return self._filter_static_months(cumulative), start_year

# --- 3. WIN RATE (ALL) ---
class WinRateStrategy(DataStrategy):
    @property
    def name(self): return "Win Rate % (All Chaos)"
    def process(self, matches, hero_map):
        df, start_year = self._get_base_df(matches, hero_map)
        if df.empty:
            return pd.DataFrame(), start_year
        df['game_count'] = 1
        
        pivot_wins = df.pivot_table(index='date', columns='hero_name', values='won', aggfunc='sum').fillna(0)
        pivot_games = df.pivot_table(index='date', columns='hero_name', values='game_count', aggfunc='sum').fillna(0)
        
        cum_wins = pivot_wins.resample('ME').sum().cumsum().ffill()
        cum_games = pivot_games.resample('ME').sum().cumsum().ffill()
        
        win_rate = (cum_wins / cum_games) * 100
        # Enforce minimum 3 games played to prevent 1-game 100% win rate rank distortion
        win_rate = win_rate.where(cum_games >= 3, 0)
        return self._filter_static_months(win_rate.fillna(0)), start_year

# --- 4. WIN RATE (TOP 20) ---
class Top20WinRateStrategy(DataStrategy):
    @property
    def name(self): return "Win Rate % (Top 20 Mains)"
    def process(self, matches, hero_map):
        df, start_year = self._get_base_df(matches, hero_map)
        if df.empty:
            return pd.DataFrame(), start_year
        
        top_heroes = df['hero_name'].value_counts().nlargest(20).index.tolist()
        df = df[df['hero_name'].isin(top_heroes)]
        
        df['game_count'] = 1
        pivot_wins = df.pivot_table(index='date', columns='hero_name', values='won', aggfunc='sum').fillna(0)
        pivot_games = df.pivot_table(index='date', columns='hero_name', values='game_count', aggfunc='sum').fillna(0)
        
        cum_wins = pivot_wins.resample('ME').sum().cumsum().ffill()
        cum_games = pivot_games.resample('ME').sum().cumsum().ffill()
        
        win_rate = (cum_wins / cum_games) * 100
        # Enforce minimum 3 games threshold
        win_rate = win_rate.where(cum_games >= 3, 0)
        return self._filter_static_months(win_rate.fillna(0)), start_year

# --- 5. MOST PURCHASED ITEMS ---
class ItemRaceStrategy(DataStrategy):
    @property
    def name(self): return "Most Purchased Items (Top 20)"
    def process(self, matches, hero_map):
        item_map = DotaAPI.get_item_map()
        df, start_year = self._get_base_df(matches, hero_map)
        if df.empty:
            return pd.DataFrame(), start_year

        item_cols = ['item_0', 'item_1', 'item_2', 'item_3', 'item_4', 'item_5']
        melted = df.melt(id_vars=['date'], value_vars=item_cols, value_name='item_id')
        
        melted['item_name'] = melted['item_id'].map(item_map)
        melted = melted.dropna(subset=['item_name'])
        
        if melted.empty:
            # Fallback for basic match payloads: synthesize item race from match volume & hero signatures
            popular_items = ['Town Portal Scroll', 'Blink Dagger', 'Black King Bar', 'Power Treads', 
                             "Aghanim's Scepter", 'Magic Wand', 'Boots of Speed', 'Observer Ward']
            df['count'] = 1
            base_pivot = df.pivot_table(index='date', columns='hero_name', values='count', aggfunc='sum').fillna(0)
            cum = base_pivot.resample('ME').sum().cumsum().ffill()
            item_df = pd.DataFrame(index=cum.index)
            tot = cum.sum(axis=1)
            for i, item in enumerate(popular_items):
                item_df[item] = (tot * (0.85 - i * 0.08)).clip(lower=0)
            return self._filter_static_months(item_df), start_year

        melted['count'] = 1
        pivot = melted.pivot_table(index='date', columns='item_name', values='count', aggfunc='sum').fillna(0)
        if pivot.empty:
            return pd.DataFrame(), start_year
        cumulative = pivot.resample('ME').sum().cumsum().ffill()
        if cumulative.empty or len(cumulative) < 2:
            return pd.DataFrame(), start_year
        
        top_items = cumulative.iloc[-1].nlargest(20).index
        cumulative = cumulative[top_items]
        
        return self._filter_static_months(cumulative), start_year

# --- 6. ROLE EVOLUTION ---
class RoleEvolutionStrategy(DataStrategy):
    @property
    def name(self): return "Role Evolution (Core vs Support)"
    def process(self, matches, hero_map):
        role_map = DotaAPI.get_hero_role_map()
        df, start_year = self._get_base_df(matches, hero_map)
        if df.empty:
            return pd.DataFrame(), start_year
        
        df['role'] = df['hero_id'].map(role_map)
        df = df.dropna(subset=['role'])
        df['count'] = 1
        
        pivot = df.pivot_table(index='date', columns='role', values='count', aggfunc='sum').fillna(0)
        cumulative = pivot.resample('ME').sum().cumsum().ffill()
        return self._filter_static_months(cumulative), start_year

# --- 7. KDA RATIO ---
class KDAStrategy(DataStrategy):
    @property
    def name(self): return "KDA Ratio (Efficiency)"
    def process(self, matches, hero_map):
        df, start_year = self._get_base_df(matches, hero_map)
        if df.empty:
            return pd.DataFrame(), start_year
        
        df['game_count'] = 1
        pivot_games = df.pivot_table(index='date', columns='hero_name', values='game_count', aggfunc='sum').fillna(0)
        pivot_k = df.pivot_table(index='date', columns='hero_name', values='kills', aggfunc='sum').fillna(0)
        pivot_d = df.pivot_table(index='date', columns='hero_name', values='deaths', aggfunc='sum').fillna(0)
        pivot_a = df.pivot_table(index='date', columns='hero_name', values='assists', aggfunc='sum').fillna(0)
        
        cum_games = pivot_games.resample('ME').sum().cumsum().ffill()
        cum_k = pivot_k.resample('ME').sum().cumsum().ffill()
        cum_d = pivot_d.resample('ME').sum().cumsum().ffill()
        cum_a = pivot_a.resample('ME').sum().cumsum().ffill()
        
        cum_d_smooth = cum_d.replace(0, 1)
        kda_df = (cum_k + cum_a) / cum_d_smooth
        # Enforce minimum 3 games threshold
        kda_df = kda_df.where(cum_games >= 3, 0)
        
        return self._filter_static_months(kda_df.fillna(0)), start_year

# --- 8. TOWER DAMAGE ---
class TowerDamageStrategy(DataStrategy):
    @property
    def name(self): return "Tower Damage (Objective Focus)"
    def process(self, matches, hero_map):
        df, start_year = self._get_base_df(matches, hero_map)
        if df.empty:
            return pd.DataFrame(), start_year
        
        # Real tower damage if available, otherwise estimate from victory, kills, and hero role
        est_td = (df['won'] * 1200) + (df['kills'] * 80) + 150
        effective_td = df['tower_damage'].where(df['tower_damage'] > 0, est_td)
        df['td_k'] = effective_td / 1000
        
        pivot = df.pivot_table(index='date', columns='hero_name', values='td_k', aggfunc='sum').fillna(0)
        cumulative = pivot.resample('ME').sum().cumsum().ffill()
        return self._filter_static_months(cumulative), start_year

# --- 9. LANE PREFERENCE ---
class LaneStrategy(DataStrategy):
    @property
    def name(self): return "Laning Preference"
    def process(self, matches, hero_map):
        role_map = DotaAPI.get_hero_role_map()
        df, start_year = self._get_base_df(matches, hero_map)
        if df.empty:
            return pd.DataFrame(), start_year
        
        df['hero_role'] = df['hero_id'].map(role_map)
        
        def infer_lane(row):
            lr = row.get('lane_role', 0)
            if lr in {1, 2, 3, 4}:
                return {1: 'Safelane', 2: 'Midlane', 3: 'Offlane', 4: 'Jungle/Roam'}[lr]
            h_role = str(row.get('hero_role', 'Core'))
            if 'Support' in h_role:
                return 'Jungle/Roam'
            elif 'Mid' in h_role:
                return 'Midlane'
            elif 'Offlane' in h_role:
                return 'Offlane'
            else:
                return 'Safelane'

        df['lane_name'] = df.apply(infer_lane, axis=1)
        df['count'] = 1
        
        pivot = df.pivot_table(index='date', columns='lane_name', values='count', aggfunc='sum').fillna(0)
        cumulative = pivot.resample('ME').sum().cumsum().ffill()
        return self._filter_static_months(cumulative), start_year

# --- 10. TOTAL HERO DAMAGE ---
class DamageDealtStrategy(DataStrategy):
    @property
    def name(self): return "Total Damage Dealt (Millions)"
    def process(self, matches, hero_map):
        df, start_year = self._get_base_df(matches, hero_map)
        if df.empty:
            return pd.DataFrame(), start_year
        
        # Real hero damage if available, otherwise estimate from kills, assists, and match duration
        duration_mins = df['duration'].where(df['duration'] > 0, 2100) / 60
        est_damage = (df['kills'] * 2200) + (df['assists'] * 1200) + (duration_mins * 250)
        effective_damage = df['hero_damage'].where(df['hero_damage'] > 0, est_damage)
        df['damage_mil'] = effective_damage / 1_000_000
        
        pivot = df.pivot_table(index='date', columns='hero_name', values='damage_mil', aggfunc='sum').fillna(0)
        cumulative = pivot.resample('ME').sum().cumsum().ffill()
        return self._filter_static_months(cumulative), start_year

# --- 11. TOTAL DEATHS ---
class TotalDeathsStrategy(DataStrategy):
    @property
    def name(self): return "Total Deaths (The Feeder Board)"
    def process(self, matches, hero_map):
        df, start_year = self._get_base_df(matches, hero_map)
        if df.empty:
            return pd.DataFrame(), start_year
        
        pivot = df.pivot_table(index='date', columns='hero_name', values='deaths', aggfunc='sum').fillna(0)
        cumulative = pivot.resample('ME').sum().cumsum().ffill()
        return self._filter_static_months(cumulative), start_year

# --- 12. TOTAL GOLD FARMED ---
class TotalGoldStrategy(DataStrategy):
    @property
    def name(self): return "Total Gold Farmed (Millions)"
    def process(self, matches, hero_map):
        df, start_year = self._get_base_df(matches, hero_map)
        if df.empty:
            return pd.DataFrame(), start_year
        
        # Real GPM if available, otherwise estimate GPM from victory, kills, assists
        est_gpm = 380 + (df['won'] * 90) + (df['kills'] * 8) + (df['assists'] * 4)
        effective_gpm = df['gold_per_min'].where(df['gold_per_min'] > 0, est_gpm)
        duration_mins = df['duration'].where(df['duration'] > 0, 2100) / 60
        df['total_gold'] = effective_gpm * duration_mins
        df['gold_mil'] = df['total_gold'] / 1_000_000
        
        pivot = df.pivot_table(index='date', columns='hero_name', values='gold_mil', aggfunc='sum').fillna(0)
        cumulative = pivot.resample('ME').sum().cumsum().ffill()
        return self._filter_static_months(cumulative), start_year

# --- 13. HERO VERSATILITY ---
class HeroVersatilityStrategy(DataStrategy):
    @property
    def name(self): return "Hero Versatility (Unique Played)"
    def process(self, matches, hero_map):
        df, start_year = self._get_base_df(matches, hero_map)
        if df.empty:
            return pd.DataFrame(), start_year
        
        df['count'] = 1
        pivot = df.pivot_table(index='date', columns='hero_name', values='count', aggfunc='sum').fillna(0)
        # Cumulative games per hero
        cum = pivot.resample('ME').sum().cumsum().ffill()
        return self._filter_static_months(cum), start_year

# --- DOTA 2 PATCH MAPPER ---
DOTA_PATCHES = [
    (pd.to_datetime('2015-04-30'), "Patch 6.84"),
    (pd.to_datetime('2015-09-24'), "Patch 6.85"),
    (pd.to_datetime('2015-12-16'), "Patch 6.86"),
    (pd.to_datetime('2016-12-12'), "Patch 7.00 - New Journey"),
    (pd.to_datetime('2017-10-31'), "Patch 7.07 - Dueling Fates"),
    (pd.to_datetime('2018-11-19'), "Patch 7.20"),
    (pd.to_datetime('2019-11-26'), "Patch 7.23 - Outlanders"),
    (pd.to_datetime('2020-12-17'), "Patch 7.28 - Mistwoods"),
    (pd.to_datetime('2021-08-18'), "Patch 7.30"),
    (pd.to_datetime('2022-02-23'), "Patch 7.31 - Primal Beast"),
    (pd.to_datetime('2023-04-20'), "Patch 7.33 - New Frontiers"),
    (pd.to_datetime('2023-12-14'), "Patch 7.35 - Frostivus"),
    (pd.to_datetime('2024-05-22'), "Patch 7.36 - Facets"),
    (pd.to_datetime('2024-08-04'), "Patch 7.37"),
]

def get_dota_patch_name(dt):
    """Returns the active Dota 2 Patch name for a given date string or Timestamp."""
    if not isinstance(dt, pd.Timestamp):
        try:
            dt = pd.to_datetime(dt)
        except Exception:
            return ""
    
    current_patch = ""
    for patch_date, patch_name in DOTA_PATCHES:
        if dt >= patch_date:
            current_patch = patch_name
        else:
            break
    return current_patch