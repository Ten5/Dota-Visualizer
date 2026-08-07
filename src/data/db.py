import sqlite3
import os
import io
import json
from PIL import Image

class DotaDB:
    DB_PATH = "cache/dota_visualizer.db"

    @staticmethod
    def _get_connection():
        os.makedirs(os.path.dirname(DotaDB.DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DotaDB.DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def init_db():
        """Initializes SQLite tables for matches and player profiles."""
        with DotaDB._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    match_id INTEGER PRIMARY KEY,
                    player_id INTEGER,
                    start_time INTEGER,
                    hero_id INTEGER,
                    player_slot INTEGER,
                    radiant_win BOOLEAN,
                    kills INTEGER,
                    deaths INTEGER,
                    assists INTEGER,
                    tower_damage INTEGER,
                    hero_damage INTEGER,
                    gold_per_min INTEGER,
                    duration INTEGER,
                    lane_role INTEGER,
                    item_0 INTEGER,
                    item_1 INTEGER,
                    item_2 INTEGER,
                    item_3 INTEGER,
                    item_4 INTEGER,
                    item_5 INTEGER,
                    raw_json TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    player_id INTEGER PRIMARY KEY,
                    personaname TEXT,
                    avatar_blob BLOB,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_player_time ON matches (player_id, start_time)")
            conn.commit()

    @staticmethod
    def save_matches(player_id, matches):
        """Saves or updates a list of match dictionaries into SQLite."""
        if not matches: return
        DotaDB.init_db()
        with DotaDB._get_connection() as conn:
            cursor = conn.cursor()
            for m in matches:
                cursor.execute("""
                    INSERT OR REPLACE INTO matches (
                        match_id, player_id, start_time, hero_id, player_slot, radiant_win,
                        kills, deaths, assists, tower_damage, hero_damage, gold_per_min, duration,
                        lane_role, item_0, item_1, item_2, item_3, item_4, item_5, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    m.get('match_id'),
                    player_id,
                    m.get('start_time'),
                    m.get('hero_id'),
                    m.get('player_slot'),
                    m.get('radiant_win'),
                    m.get('kills', 0),
                    m.get('deaths', 0),
                    m.get('assists', 0),
                    m.get('tower_damage', 0),
                    m.get('hero_damage', 0),
                    m.get('gold_per_min', 0),
                    m.get('duration', 0),
                    m.get('lane_role', 0),
                    m.get('item_0', 0),
                    m.get('item_1', 0),
                    m.get('item_2', 0),
                    m.get('item_3', 0),
                    m.get('item_4', 0),
                    m.get('item_5', 0),
                    json.dumps(m, default=int)
                ))
            conn.commit()

    @staticmethod
    def get_matches(player_id):
        """Returns all cached matches for player_id sorted by start_time ascending."""
        DotaDB.init_db()
        with DotaDB._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT raw_json, match_id, start_time, hero_id, player_slot, radiant_win,
                       kills, deaths, assists, tower_damage, hero_damage, gold_per_min, duration,
                       lane_role, item_0, item_1, item_2, item_3, item_4, item_5
                FROM matches 
                WHERE player_id = ? 
                ORDER BY start_time ASC
            """, (player_id,))
            rows = cursor.fetchall()
            
            matches = []
            for r in rows:
                m_dict = dict(r)
                if r['raw_json']:
                    try:
                        raw = json.loads(r['raw_json'])
                        if isinstance(raw, dict):
                            # Overlay raw_json on top of SQLite row dict so all DB columns exist
                            db_fields = {k: v for k, v in m_dict.items() if k != 'raw_json'}
                            db_fields.update(raw)
                            m_dict = db_fields
                    except Exception:
                        pass
                matches.append(m_dict)
            return matches

    @staticmethod
    def get_latest_match_id(player_id):
        """Returns the highest match_id saved for player_id, or None."""
        DotaDB.init_db()
        with DotaDB._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(match_id) as max_id FROM matches WHERE player_id = ?", (player_id,))
            row = cursor.fetchone()
            return row['max_id'] if row and row['max_id'] else None

    @staticmethod
    def save_profile(player_id, name, avatar_img=None):
        """Saves player name and avatar PNG blob to SQLite."""
        DotaDB.init_db()
        blob = None
        if avatar_img:
            buf = io.BytesIO()
            avatar_img.save(buf, format="PNG")
            blob = buf.getvalue()

        with DotaDB._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO profiles (player_id, personaname, avatar_blob)
                VALUES (?, ?, ?)
            """, (player_id, name, blob))
            conn.commit()

    @staticmethod
    def get_profile(player_id):
        """Returns cached profile dict {'name': ..., 'avatar': PIL_Image} or None."""
        DotaDB.init_db()
        with DotaDB._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT personaname, avatar_blob FROM profiles WHERE player_id = ?", (player_id,))
            row = cursor.fetchone()
            if not row: return None

            img = None
            if row['avatar_blob']:
                img = Image.open(io.BytesIO(row['avatar_blob']))

            return {'name': row['personaname'], 'avatar': img}
