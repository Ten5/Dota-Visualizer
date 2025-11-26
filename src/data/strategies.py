from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from src.data.api import DotaAPI 

earliest_start_year = 2010

class DataStrategy(ABC):
    @abstractmethod
    def process(self, matches, hero_map):
        pass

    @property
    @abstractmethod
    def name(self):
        pass
    
    def _get_base_df(self, matches, hero_map):
        """Common helper to clean data"""
        df = pd.DataFrame(matches)
        
        if df.empty or 'start_time' not in df.columns:
            return pd.DataFrame(), earliest_start_year # Return empty DataFrame and default start_year

        df['date'] = pd.to_datetime(df['start_time'], unit='s')
        
        earliest = df['date'].dt.year.min()
        start_year = int(earliest) if pd.notna(earliest) else earliest_start_year
        
        df['hero_name'] = df['hero_id'].map(hero_map)
        df = df.dropna(subset=['hero_name'])
        
        df['is_radiant'] = df['player_slot'] < 128
        df['won'] = ((df['is_radiant'] & df['radiant_win']) | 
                     (~df['is_radiant'] & ~df['radiant_win'])).astype(int)
        return df, start_year

    def _filter_static_months(self, df):
        """
        Global filter: Removes months where data is identical to the previous month.
        This makes the video 'fast forward' through breaks in gameplay.
        """
        if df.empty: return df
        
        # Check if current row != previous row (ANY column changed)
        has_changes = (df != df.shift(1)).any(axis=1)
        
        # Always keep the first row so the video starts correctly
        has_changes.iloc[0] = True
        
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
        
        # Clean Calculation
        win_rate = (cum_wins / cum_games) * 100
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
        return self._filter_static_months(win_rate.fillna(0)), start_year

# --- 5. MOST PURCHASED ITEMS ---
class ItemRaceStrategy(DataStrategy):
    @property
    def name(self): return "Most Purchased Items (Top 20)"
    def process(self, matches, hero_map):
        item_map = DotaAPI.get_item_map()
        df = pd.DataFrame(matches)
        if df.empty or 'start_time' not in df.columns:
            return pd.DataFrame(), earliest_start_year
        df['date'] = pd.to_datetime(df['start_time'], unit='s')
        earliest = df['date'].dt.year.min()
        start_year = int(earliest) if pd.notna(earliest) else earliest_start_year

        item_cols = ['item_0', 'item_1', 'item_2', 'item_3', 'item_4', 'item_5']
        melted = df.melt(id_vars=['date'], value_vars=item_cols, value_name='item_id')
        
        melted['item_name'] = melted['item_id'].map(item_map)
        melted = melted.dropna(subset=['item_name'])
        melted['count'] = 1
        
        pivot = melted.pivot_table(index='date', columns='item_name', values='count', aggfunc='sum').fillna(0)
        cumulative = pivot.resample('ME').sum().cumsum().ffill()
        
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
        
        pivot_k = df.pivot_table(index='date', columns='hero_name', values='kills', aggfunc='sum').fillna(0)
        pivot_d = df.pivot_table(index='date', columns='hero_name', values='deaths', aggfunc='sum').fillna(0)
        pivot_a = df.pivot_table(index='date', columns='hero_name', values='assists', aggfunc='sum').fillna(0)
        
        cum_k = pivot_k.resample('ME').sum().cumsum().ffill()
        cum_d = pivot_d.resample('ME').sum().cumsum().ffill()
        cum_a = pivot_a.resample('ME').sum().cumsum().ffill()
        
        cum_d = cum_d.replace(0, 1)
        kda_df = (cum_k + cum_a) / cum_d
        
        return self._filter_static_months(kda_df.fillna(0)), start_year

# --- 8. TOWER DAMAGE ---
class TowerDamageStrategy(DataStrategy):
    @property
    def name(self): return "Tower Damage (Objective Focus)"
    def process(self, matches, hero_map):
        df, start_year = self._get_base_df(matches, hero_map)
        if df.empty:
            return pd.DataFrame(), start_year
        df['td_k'] = df['tower_damage'] / 1000
        pivot = df.pivot_table(index='date', columns='hero_name', values='td_k', aggfunc='sum').fillna(0)
        cumulative = pivot.resample('ME').sum().cumsum().ffill()
        return self._filter_static_months(cumulative), start_year

# --- 9. LANE PREFERENCE ---
class LaneStrategy(DataStrategy):
    @property
    def name(self): return "Laning Preference"
    def process(self, matches, hero_map):
        df, start_year = self._get_base_df(matches, hero_map)
        if df.empty:
            return pd.DataFrame(), start_year
        lane_names = {1: 'Safelane', 2: 'Midlane', 3: 'Offlane', 4: 'Jungle/Roam'}
        
        df['lane_name'] = df['lane_role'].map(lane_names)
        df = df.dropna(subset=['lane_name'])
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
        
        # OpenDota provides 'hero_damage' directly
        # Divide by 1M to keep chart numbers readable (e.g., "1.5M")
        df['damage_mil'] = df['hero_damage'] / 1_000_000
        
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
        
        # Calculate Total Gold: GPM * (Duration in minutes)
        # Duration is usually in seconds from OpenDota
        df['total_gold'] = df['gold_per_min'] * (df['duration'] / 60)
        df['gold_mil'] = df['total_gold'] / 1_000_000
        
        pivot = df.pivot_table(index='date', columns='hero_name', values='gold_mil', aggfunc='sum').fillna(0)
        cumulative = pivot.resample('ME').sum().cumsum().ffill()
        return self._filter_static_months(cumulative), start_year