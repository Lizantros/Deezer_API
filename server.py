from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import uvicorn
import time

# Import our existing logic
from parser import parse_description
from deezer_gw import DeezerGWClient

app = FastAPI()

# Serve static files (CSS, JS, HTML)
app.mount("/static", StaticFiles(directory="static"), name="static")

class ParseRequest(BaseModel):
    text: str

class PrepareRequest(BaseModel):
    arl: str
    songs: List[dict] # [{'artist': '...', 'title': '...'}, ...]

class CreateRequest(BaseModel):
    arl: str
    playlist_name: str
    track_ids: List[int]

class SearchCandidatesRequest(BaseModel):
    arl: str
    query: str

class AuthRequest(BaseModel):
    arl: str

@app.get("/")
async def read_root():
    return FileResponse('static/index.html')

@app.post("/api/auth/check")
async def check_auth(request: AuthRequest):
    try:
        # Try to initialize client with the provided ARL
        # The constructor of DeezerGWClient validates the user_id > 0
        client = DeezerGWClient(request.arl)
        print(f"Auth check passed for User ID: {client.user_id}")
        return {"status": "ok", "user_id": client.user_id}
    except Exception as e:
        print(f"Auth check failed: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/parse")
async def parse_text(request: ParseRequest):
    # Reuse our parser logic
    # parse_description returns list of tuples (artist, title)
    try:
        parsed = parse_description(request.text)
        # Convert to list of dicts for JSON
        songs_data = [{"artist": a, "title": t} for a, t in parsed]
        return {"songs": songs_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/prepare")
async def prepare_playlist(request: PrepareRequest):
    try:
        client = DeezerGWClient(request.arl)
        results = []
        
        for song in request.songs:
            artist = song['artist']
            title = song['title']
            
            # Helper to fallback
            def add_ambiguous(candidates=None):
                if not candidates:
                    candidates = client.search_candidates(title, limit=5)
                if candidates:
                    results.append({
                        "status": "ambiguous",
                        "artist": artist,
                        "title": title,
                        "candidates": candidates,
                        "selected_id": candidates[0]['id']
                    })
                else:
                    results.append({"status": "missing", "artist": artist, "title": title})

            if artist:
                # Search returns dict {id, artist, title}
                found = client.search_track(artist, title)
                
                if found:
                    # VALIDATE ARTIST MATCH
                    # If input artist was "8" and found "Ludwig", that's a bad match -> Ambiguous
                    
                    input_art = artist.lower().strip()
                    found_art = found['artist'].lower().strip()
                    
                    # Simple heuristic: is input contained in found? or high similarity?
                    # or if input is very short/numeric and found is different
                    
                    is_suspicious = False
                    if len(input_art) < 3 and input_art != found_art:
                        is_suspicious = True
                    elif input_art not in found_art and found_art not in input_art:
                        # e.g. "Pop" vs "Pop Mage" is OK. "8" vs "Ludwig" is NOT.
                        # Calculate Levenshtein? Or just strict check?
                        # Let's say if no substring match -> suspicious
                         is_suspicious = True
                    
                    if is_suspicious:
                        # It's ambiguous! found['id'] is just one candidate.
                        # We want to show candidates, but ensure 'found' is in the list
                        candidates = client.search_candidates(title, limit=5)
                        add_ambiguous(candidates)
                    else:
                        # Good match
                        results.append({
                            "status": "found",
                            "artist": found['artist'], 
                            "title": found['title'], 
                            "id": found['id']
                        })
                else:
                    # Failed strict search -> Ambiguous fallback
                    add_ambiguous()
            else:
                # No artist -> Ambiguous
                add_ambiguous()
                    
        return {"results": results}
    except Exception as e:
        print(f"Prepare failed: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/create")
async def create_playlist_endpoint(request: CreateRequest):
    try:
        client = DeezerGWClient(request.arl)
        
        track_ids = request.track_ids
        playlist_name = request.playlist_name
        
        if not track_ids:
             return {"status": "error", "message": "No tracks provided."}

        found_count = len(track_ids)
        
        try:
            # Try to create with ALL tracks first
            playlist_id = client.create_playlist(playlist_name, track_ids)
            msg = f"Playlist '{playlist_name}' created with {found_count} songs."
            
        except Exception as e:
            print(f"Creation with tracks failed ({e}). Trying chunked strategy...")
            # Fallback: Create empty, then add in chunks
            playlist_id = client.create_playlist(playlist_name) # Empty
            
            # Chunk size
            chunk_size = 20
            for i in range(0, len(track_ids), chunk_size):
                chunk = track_ids[i:i + chunk_size]
                try:
                    client.add_tracks_to_playlist(playlist_id, chunk)
                    print(f"Added chunk {i}-{i+len(chunk)}")
                    time.sleep(1) # Be nice to API
                except Exception as chunk_e:
                    print(f"Failed to add chunk {i}: {chunk_e}")
            
            msg = f"Playlist '{playlist_name}' created (Chunked mode) with {found_count} songs."

        return {
            "status": "success",
            "message": msg,
            "playlist_id": playlist_id
        }
        
    except Exception as e:
        print(f"Create API failed: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/search_candidates")
async def search_candidates_api(request: SearchCandidatesRequest):
    try:
        client = DeezerGWClient(request.arl)
        candidates = client.search_candidates(request.query, limit=10) # Higher limit for refinement
        return {"candidates": candidates}
    except Exception as e:
        print(f"Search candidates failed: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # Auto-reload for dev
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
