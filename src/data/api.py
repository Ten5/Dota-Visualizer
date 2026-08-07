import requests
import time
import os
from io import BytesIO
from PIL import Image

from src.data.db import DotaDB

class DotaAPI:
    BASE_URL = "https://api.opendota.com/api"
    
    # --- IN-MEMORY CACHE ---
    _match_cache = {}      # Stores {player_id: [match_list]}
    _hero_map_cache = None # Stores {id: name}
    _item_map_cache = None # Stores {id: name}
    _role_map_cache = None # Stores {id: role}
    _profile_cache = {}    # Stores {player_id: {'name': str, 'avatar': PIL_Image}}

    @staticmethod
    def get_hero_map():
        """Returns cached hero map if available, otherwise fetches it."""
        if DotaAPI._hero_map_cache:
            return DotaAPI._hero_map_cache
            
        url = f"{DotaAPI.BASE_URL}/heroes"
        try:
            resp = requests.get(url)
            data = resp.json()
            DotaAPI._hero_map_cache = {h['id']: h['localized_name'] for h in data}
            return DotaAPI._hero_map_cache
        except Exception as e:
            print(f"API Error (Heroes): {e}")
            return {}

    @staticmethod
    def get_hero_role_map():
        """Returns cached role map if available."""
        if DotaAPI._role_map_cache:
            return DotaAPI._role_map_cache
            
        url = f"{DotaAPI.BASE_URL}/heroes"
        try:
            resp = requests.get(url)
            role_map = {}
            for h in resp.json():
                roles = h.get('roles', [])
                role_map[h['id']] = 'Support' if 'Support' in roles else 'Core'
            
            DotaAPI._role_map_cache = role_map
            return role_map
        except Exception:
            return {}

    @staticmethod
    def get_item_map():
        """Returns cached item map if available."""
        if DotaAPI._item_map_cache:
            return DotaAPI._item_map_cache

        url = "https://api.opendota.com/api/constants/items"
        try:
            resp = requests.get(url)
            data = resp.json()
            item_map = {}
            for key, val in data.items():
                if val and 'id' in val and 'dname' in val:
                    item_map[val['id']] = val['dname']
            
            DotaAPI._item_map_cache = item_map
            return item_map
        except Exception:
            return {}

    @staticmethod
    def get_player_profile(player_id):
        """
        Returns a dict: {'name': 'Dendi', 'avatar': PIL_Image}
        Checks in-memory cache first, then SQLite database, then OpenDota API.
        """
        if player_id in DotaAPI._profile_cache:
            return DotaAPI._profile_cache[player_id]

        # Check SQLite DB
        db_profile = DotaDB.get_profile(player_id)
        if db_profile:
            DotaAPI._profile_cache[player_id] = db_profile
            return db_profile

        profile_data = {'name': f"Player {player_id}", 'avatar': None}

        try:
            url = f"{DotaAPI.BASE_URL}/players/{player_id}"
            data = requests.get(url).json()
            profile = data.get('profile', {})
            
            if 'personaname' in profile:
                profile_data['name'] = profile['personaname']
            
            avatar_url = profile.get('avatarfull')
            if avatar_url:
                resp = requests.get(avatar_url)
                img = Image.open(BytesIO(resp.content))
                profile_data['avatar'] = img
                
            DotaAPI._profile_cache[player_id] = profile_data
            DotaDB.save_profile(player_id, profile_data['name'], profile_data['avatar'])
            
        except Exception as e:
            print(f"Error fetching profile: {e}")

        return profile_data

    @staticmethod
    def fetch_all_matches(player_id, log_callback=None):
        """
        Checks memory cache first, then SQLite disk database.
        Performs incremental fetch for any new matches played since last cache sync.
        """
        # 1. CHECK IN-MEMORY CACHE
        if player_id in DotaAPI._match_cache:
            if log_callback:
                log_callback(f"Using memory-cached data for {player_id}...")
            return DotaAPI._match_cache[player_id]

        # 2. CHECK SQLITE DB
        cached_db_matches = DotaDB.get_matches(player_id)
        latest_match_id = DotaDB.get_latest_match_id(player_id)

        if cached_db_matches and log_callback:
            log_callback(f"Loaded {len(cached_db_matches)} matches from local database. Checking for updates...")

        # 3. INCREMENTAL API FETCH
        new_matches = []
        offset = 0
        should_stop = False
        
        while True:
            url = f"{DotaAPI.BASE_URL}/players/{player_id}/matches"
            params = {'limit': 1000, 'offset': offset}
            
            try:
                resp = requests.get(url, params=params)
                data = resp.json()
                
                if not data or not isinstance(data, list): break
                
                # Check for incremental stop condition or infinite loops
                for match in data:
                    if latest_match_id and match.get('match_id') and match['match_id'] <= latest_match_id:
                        should_stop = True
                        break
                    new_matches.append(match)

                if should_stop: break

                offset += len(data)

                if log_callback and new_matches:
                    log_callback(f"Fetched {len(new_matches)} new matches from API...")
                
                if len(data) < 1000: break
                time.sleep(0.5) # Be nice to OpenDota API
                
            except Exception as e:
                if log_callback: log_callback(f"API Sync Info/Warning: {e}")
                break

        # Save new matches to SQLite database
        if new_matches:
            DotaDB.save_matches(player_id, new_matches)
            if log_callback:
                log_callback(f"Saved {len(new_matches)} new matches to local database.")

        # Reload complete match set from SQLite
        all_matches = DotaDB.get_matches(player_id)
        if not all_matches:
            all_matches = new_matches

        # Save to in-memory cache
        DotaAPI._match_cache[player_id] = all_matches
        
        if log_callback:
            log_callback(f"Ready! Total {len(all_matches)} matches loaded.")
            
        return all_matches

    @staticmethod
    def clear_cache():
        """Clears memory and SQLite disk caches."""
        DotaAPI._match_cache.clear()
        DotaAPI._profile_cache.clear()
        if os.path.exists(DotaDB.DB_PATH):
            os.remove(DotaDB.DB_PATH)

    @staticmethod
    def download_hero_images(hero_map, output_dir="assets/hero_images"):
        """Downloads hero icons and saves them as 'Hero Name.png'"""
        import os
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Get stats which contain the image paths
        try:
            url = f"{DotaAPI.BASE_URL}/heroStats"
            data = requests.get(url).json()
            
            # Create a lookup: ID -> Image URL suffix
            img_lookup = {h['id']: h['img'] for h in data}
            
            downloaded_count = 0
            for hero_id, hero_name in hero_map.items():
                # Clean filename (replace unsafe chars if any, though Dota names are usually fine)
                safe_name = hero_name.replace("/", "_") 
                file_path = f"{output_dir}/{safe_name}.png"
                
                # Skip if already exists (Caching)
                if os.path.exists(file_path):
                    continue
                
                if hero_id in img_lookup:
                    full_img_url = f"https://api.opendota.com{img_lookup[hero_id]}"
                    img_data = requests.get(full_img_url).content
                    with open(file_path, 'wb') as f:
                        f.write(img_data)
                    downloaded_count += 1
            
            if downloaded_count > 0:
                print(f"Downloaded {downloaded_count} new hero icons.")
                
        except Exception as e:
            print(f"Error downloading icons: {e}")