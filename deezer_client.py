import requests
import urllib.parse
from config import APP_ID, APP_SECRET, REDIRECT_URI

class DeezerClient:
    BASE_URL = "https://api.deezer.com"

    def __init__(self, access_token=None):
        self.access_token = access_token
        
    def get_auth_url(self):
        if not APP_ID or not REDIRECT_URI:
            return None
        """Generates the URL for the user to authenticate."""
        perms = "basic_access,manage_library,delete_library" 
        # manage_library is needed to create playlists and add tracks
        params = {
            "app_id": APP_ID,
            "redirect_uri": REDIRECT_URI,
            "perms": perms,
            "response_type": "code",
        }
        query_string = urllib.parse.urlencode(params)
        return f"https://connect.deezer.com/oauth/auth.php?{query_string}"

    def authenticate(self, code):
        """Exchanges the authorization code for an access token."""
        url = f"https://connect.deezer.com/oauth/access_token.php"
        params = {
            "app_id": APP_ID,
            "secret": APP_SECRET,
            "code": code,
            "output": "json" 
        }
        response = requests.get(url, params=params)
        data = response.json()
        
        if "access_token" in data:
            self.access_token = data["access_token"]
            return True, "Authentication successful."
        else:
            return False, f"Authentication failed: {data}"

    def search_track(self, artist, title):
        """Search for a track and return its ID."""
        query = f'artist:"{artist}" track:"{title}"'
        params = {
            "q": query,
            "limit": 1
        }
        response = requests.get(f"{self.BASE_URL}/search", params=params)
        data = response.json()
        
        if "data" in data and len(data["data"]) > 0:
            return data["data"][0]["id"]
        return None

    def create_playlist(self, title):
        """Creates a new playlist and returns its ID."""
        if not self.access_token:
            raise Exception("Not authenticated")
            
        url = f"{self.BASE_URL}/user/me/playlists"
        params = {
            "access_token": self.access_token,
            "title": title
        }
        response = requests.post(url, params=params)
        data = response.json()
        
        if "id" in data:
            return data["id"]
        if "error" in data:
            raise Exception(f"Error creating playlist: {data['error']}")
        return None

    def add_tracks_to_playlist(self, playlist_id, track_ids):
        """Adds specific track IDs to a playlist."""
        if not self.access_token:
            raise Exception("Not authenticated")
            
        url = f"{self.BASE_URL}/playlist/{playlist_id}/tracks"
        # track_ids should be comma separated
        tracks_str = ",".join(map(str, track_ids))
        params = {
            "access_token": self.access_token,
            "songs": tracks_str
        }
        response = requests.post(url, params=params)
        return response.json()
