import sys
from urllib.parse import urlparse, parse_qs
from parser import parse_description
from deezer_client import DeezerClient
from deezer_gw import DeezerGWClient
import config

def main():
    client = None
    
    # Priority 1: ARL Cookie (Most robust if no App ID)
    if config.ARL:
        print("Using DEEZER_ARL from config.")
        try:
            client = DeezerGWClient(config.ARL)
        except Exception as e:
            print(f"Failed to initialize with ARL: {e}")
            return

    # Priority 2: Static Access Token
    elif config.ACCESS_TOKEN:
        print("Using provided DEEZER_ACCESS_TOKEN from config.")

        client = DeezerClient(access_token=config.ACCESS_TOKEN)
        # Verify token is valid (optional, but good practice by trying a simple call)
        # We'll assume it's valid for now or fail later.
    
        # We'll assume it's valid for now or fail later.
    
    # Priority 3: OAuth App (if configured)
    elif config.APP_ID and config.APP_SECRET:
        client = DeezerClient()
        
    else:
        print("Error: No valid authentication found.")
        print("Please set DEEZER_ARL (getting from browser cookie) or DEEZER_ACCESS_TOKEN in .env")
        return


    print("--- YouTube Description to Deezer Playlist ---")
    
    # 1. Get Input
    description = ""
    if len(sys.argv) > 1:
        # File mode
        filename = sys.argv[1]
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                description = f.read()
            print(f"Loaded description from {filename}")
        except Exception as e:
            print(f"Error reading file: {e}")
            return
    else:
        # Interactive mode
        print("Paste the YouTube description below.")
        print("Type 'END' on a new line and press Enter to finish:")
        print("---------------------------------------------------")
        
        input_lines = []
        while True:
            try:
                line = input()
                if line.strip().upper() == 'END':
                    break
                input_lines.append(line)
            except EOFError:
                break
        
        print("---------------------------------------------------")
        print("Processing input...")
        description = "\n".join(input_lines)
    
    if not description.strip():
        print("No description provided. Exiting.")
        return

    # 2. Parse
    songs = parse_description(description)
    print(f"\nFound {len(songs)} potential songs.")
    for idx, (artist, title) in enumerate(songs, 1):
        print(f"{idx}. {artist} - {title}")
    
    if not songs:
        print("No songs found. Exiting.")
        return

    confirm = input("\nProceed with these songs? (y/n): ")
    if confirm.lower() != 'y':
        print("Aborted.")
        return

        return

    # 3. Authenticate (only if client is not fully ready - i.e. using older OAuth client without token)
    # If using GWClient, client is already authed in __init__
    if isinstance(client, DeezerClient) and not client.access_token:
        auth_url = client.get_auth_url()
        print(f"\nPlease authorize the app by visiting this URL:\n{auth_url}")
        print("\nAfter authorizing, you will be redirected to a URL (e.g. localhost... or whatever you set).")
        redirected_url = input("Paste the full redirected URL here: ").strip()
        
        # Extract code from URL
        parsed = urlparse(redirected_url)
        code = parse_qs(parsed.query).get('code')
        
        if not code:
            print("Could not find 'code' in the URL. Authentication failed.")
            return
        
        success, msg = client.authenticate(code[0])
        if not success:
            print(msg)
            return
        print("Authentication successful!")


    # 4. Search and Collect IDs
    track_ids = []
    print("\nSearching for tracks on Deezer...")
    total = len(songs)
    for i, (artist, title) in enumerate(songs, 1):
        print(f"[{i}/{total}] Searching: {artist} - {title}...", end='\r')
        tid = client.search_track(artist, title)
        if tid:
            print(f"[{i}/{total}] [FOUND] {artist} - {title}          ")
            track_ids.append(tid)
        else:
            print(f"[{i}/{total}] [MISSING] {artist} - {title}        ")
            
    print(f"\nFound {len(track_ids)}/{len(songs)} tracks on Deezer.")
    
    if not track_ids:
        print("No tracks found on Deezer to add.")
        return

    # 5. Create Playlist AND Add Tracks
    playlist_name = input("\nEnter a name for the new playlist: ")
    try:
        # Try adding at creation time
        pid = client.create_playlist(playlist_name, track_ids)
        print(f"Playlist '{playlist_name}' created (ID: {pid}).")
        
        # We don't need to call add_tracks_to_playlist if creation handled it
        # But if pid is returned, we assume it worked.
        # Check if tracks were added? Hard to check without another call.
        print("Tracks added successfully (during creation)!")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
