import requests
import json
import time

class DeezerGWClient:
    """
    Unofficial Deezer Client that uses the 'arl' cookie and the internal 'gw-light.php' API.
    Bypasses the need for an App ID/Secret.
    """
    GW_URL = "https://www.deezer.com/ajax/gw-light.php"
    
    def __init__(self, arl):
        self.arl = arl
        self.session = requests.Session()
        # Pretend to be a browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Origin': 'https://www.deezer.com',
            'Referer': 'https://www.deezer.com/en/',
            'Accept-Language': 'en-US,en;q=0.9',
            'X-Requested-With': 'XMLHttpRequest',
        })
        self.session.cookies.set('arl', arl, domain='.deezer.com')
        self.api_token = 'null' # Initial token
        self.user_id = None
        
        # Initialize session and get real CSRF token
        self._init_session()

    def _init_session(self):
        """Get the api_token (CSRF) from getUserData"""
        print("Connecting to Deezer (gw-light)...")
        data = self._call('deezer.getUserData')

        if not data:
            raise Exception("Failed to get user data. Is the ARL cookie valid?")
        
        self.api_token = data.get('checkForm')
        self.user_id = data.get('USER', {}).get('USER_ID')
        
        if not self.api_token:
            raise Exception("Could not find api_token (checkForm) in response.")
            
        print(f"Successfully connected as User ID: {self.user_id}")
        
        if str(self.user_id) == '0':
            print("\n[WARNING] You are connected as Guest (User ID 0).")
            print("This means your ARL cookie is invalid, expired, or not recognized.")
            print("Playlist creation WILL fail.")
            print("Please double-check your 'DEEZER_ARL' in .env")
            print("Make sure you copied the full 192-character string without extra spaces.\n")
            # We raise error here to stop early
            raise Exception("Invalid ARL Cookie (Guest Session)")

    def _call(self, method, params=None):
        """Generic call to gw-light.php"""
        if params is None:
            params = {}
            
        query_params = {
            'method': method,
            'api_version': '1.0',
            'api_token': self.api_token,
            'input': '3'
        }
        
        # Requests sometimes wants json dump in body
        response = self.session.post(self.GW_URL, params=query_params, json=params)
        
        try:
            res_json = response.json()
        except Exception:
            print(f"DEBUG: Failed Raw Response: {response.text[:500]}...")
            raise Exception(f"Failed to parse JSON response from {method}")
            
        if 'error' in res_json and res_json['error']:
            # Sometimes empty list [] is not an error but "no data"
            if isinstance(res_json['error'], list) and not res_json['error']:
                pass
            else:
                raise Exception(f"API Error in {method}: {res_json['error']}")
                
        return res_json.get('results')

    def search_track(self, artist, title):
        """Search for a track. Returns ID."""
        query = f'artist:"{artist}" track:"{title}"'
        # The internal search method might be different, let's use public search API 
        # or the internal 'search.music'
        
        # For robustness, we can typically AUTHENTICATED users can call the public API too?
        """Search for a track. Returns dict {id, artist, title} or None."""
        # Helper to extract Metadata
        def get_meta(item):
            tid = None
            for key in ['id', 'SNG_ID', 'TRACK_ID', 'ID']:
                if key in item:
                    tid = item[key]
                    break
            if not tid: return None
            
            # Artist
            art = item.get('ART_NAME')
            if not art and 'artist' in item: art = item['artist'].get('name')
            if not art: art = "Unknown"
            
            # Title
            ttl = item.get('SNG_TITLE', item.get('title', 'Unknown'))
            
            return {'id': tid, 'artist': art, 'title': ttl}

        params = {
            'query': '',
            'filter': 'ALL',
            'output': 'TRACK',
            'start': 0,
            'nb': 1
        }
        
        # Strategy 1: Strict Metadata Search
        if artist:
            # Reconstruct params for specific call if needed, but search.music takes 'query'
            # We can try to use advanced query syntax if gw-light supports it
            params['query'] = f'artist:"{artist}" track:"{title}"'
            results = self._call('search.music', params)
            if results and 'data' in results and len(results['data']) > 0:
                print(f"DEBUG: Found '{title}' via strict search.")
                return get_meta(results['data'][0])
        
        # Strategy 2: Loose Search (Artist + Title)
        loose_query = f'{artist} {title}'.strip()
        print(f"DEBUG: Trying loose search for '{loose_query}'...", end='\r')
        params['query'] = loose_query
        results = self._call('search.music', params)
        if results and 'data' in results and len(results['data']) > 0:
            return get_meta(results['data'][0])

        # Strategy 3: REMOVED. 
        # We prefer to return None and let the upper layer (server) decide 
        # (e.g. show candidates dropdown instead of auto-picking).
            
        return None

    def search_candidates(self, query, limit=5):
        """Search for candidates and return metadata list."""
        params = {
            'query': query,
            'filter': 'ALL',
            'output': 'TRACK',
            'start': 0,
            'nb': limit
        }
        results = self._call('search.music', params)
        candidates = []
        
        if results and 'data' in results:
            for item in results['data']:
                # Extract ID
                tid = None
                for key in ['id', 'SNG_ID', 'TRACK_ID', 'ID']:
                    if key in item:
                        tid = item[key]
                        break
                if not tid: continue
                
                # Extract Metadata
                # API keys vary (SNG_TITLE vs title, ART_NAME vs artist.name)
                title = item.get('SNG_TITLE', item.get('title', 'Unknown'))
                
                # Artist
                artist_name = item.get('ART_NAME')
                if not artist_name and 'artist' in item:
                    artist_name = item['artist'].get('name')
                if not artist_name: artist_name = "Unknown"
                
                # Album
                album_title = item.get('ALB_TITLE')
                if not album_title and 'album' in item:
                    album_title = item['album'].get('title')
                
                candidates.append({
                    'id': tid,
                    'title': title,
                    'artist': artist_name,
                    'album': album_title
                })
        return candidates
        
    def create_playlist(self, title, track_ids=None):
        """Creates a playlist and optionally adds tracks."""
        songs_payload = []
        if track_ids:
            # Try list of lists format for creation
            songs_payload = [[int(tid), 0] for tid in track_ids]
            
        params = {
            'title': title,
            'status': 0,
            'description': 'Created with Python',
            'songs': songs_payload
        }
        print(f"DEBUG: Creating playlist with params: {json.dumps(params)}")
        result = self._call('playlist.create', params)
        return result

    def add_tracks_to_playlist(self, playlist_id, track_ids):
        """Adds tracks using playlist.addSongs with [[id, 0]] format."""
        # Format: [[id, 0], [id, 0]]
        formatted_songs = [[int(tid), 0] for tid in track_ids]
            
        params = {
            'playlist_id': playlist_id,
            'songs': formatted_songs,
            'offset': -1
        }
        print(f"DEBUG: Adding tracks with params (playlist.addSongs + list): {json.dumps(params)}")
        
        # We need to handle potential JSON parse errors if the endpoint returns HTML
        try:
            result = self._call('playlist.addSongs', params)
            return True
        except Exception as e:
            print(f"DEBUG: add_tracks failed: {e}")
            raise e
