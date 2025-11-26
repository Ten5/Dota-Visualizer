import requests
import time
from io import BytesIO
from PIL import Image

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
        """
        if player_id in DotaAPI._profile_cache:
            return DotaAPI._profile_cache[player_id]

        profile_data = {'name': f"Player {player_id}", 'avatar': None}

        try:
            url = f"{DotaAPI.BASE_URL}/players/{player_id}"
            data = requests.get(url).json()
            profile = data.get('profile', {})
            
            # 1. Get Name (personaname)
            if 'personaname' in profile:
                profile_data['name'] = profile['personaname']
            
            # 2. Get Avatar
            avatar_url = profile.get('avatarfull')
            if avatar_url:
                resp = requests.get(avatar_url)
                img = Image.open(BytesIO(resp.content))
                profile_data['avatar'] = img
                
            # Save to cache
            DotaAPI._profile_cache[player_id] = profile_data
            
        except Exception as e:
            print(f"Error fetching profile: {e}")

        return profile_data

    @staticmethod
    def fetch_all_matches(player_id, log_callback=None):
        """
        Checks cache first. If found, returns instantly.
        If not, fetches all pages, saves to cache, and returns.
        """
        # 1. CHECK CACHE
        if player_id in DotaAPI._match_cache:
            if log_callback:
                log_callback(f"Using cached data for {player_id} (Instant load)...")
            return DotaAPI._match_cache[player_id]

        # 2. FETCH IF NOT IN CACHE
        all_matches = []
        offset = 0
        
        while True:
            url = f"{DotaAPI.BASE_URL}/players/{player_id}/matches"
            params = {'limit': 1000, 'offset': offset}
            
            try:
                resp = requests.get(url, params=params)
                data = resp.json()
                
                if not data: break
                
                # Check for infinite loops (API safety)
                if all_matches and data[0]['match_id'] == all_matches[0]['match_id']:
                    break

                all_matches.extend(data)
                offset += len(data)

                if log_callback:
                    log_callback(f"Fetching from API: {len(all_matches)} matches...")
                
                if len(data) < 1000:
                    break
                    
                time.sleep(0.5) # Be nice to the API
                
            except Exception as e:
                if log_callback: log_callback(f"API Error: {e}")
                break
        
        # Deduplicate
        unique_matches = list({m['match_id']: m for m in all_matches}.values())
        
        # 3. SAVE TO CACHE
        DotaAPI._match_cache[player_id] = unique_matches
        
        if log_callback:
            log_callback(f"Download complete. Cached {len(unique_matches)} matches in memory.")
            
        return unique_matches

    @staticmethod
    def clear_cache():
        """Optional: Call this if you add a 'Clear Data' button later"""
        DotaAPI._match_cache.clear()
        DotaAPI._avatar_cache.clear()

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