import re
from typing import List, Tuple

def parse_description(text: str) -> List[Tuple[str, str]]:
    """
    Parses a text block (YouTube description) and attempts to extract songs.
    Returns a list of (Artist, Title) tuples.
    """
    songs = []
    
    # Common patterns:
    # 1. timestamp Artist - Title (e.g. 02:30 The Beatles - Let It Be)
    # 2. Artist - Title (e.g. Queen - Bohemian Rhapsody)
    # 3. Number. Artist - Title (e.g. 1. Pink Floyd - Time)
    
    # We will process line by line
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Remove timestamps (e.g., 00:00, 1:24:47, [03:45])
        # Regex: optional brackets, optional hour (d:), min:sec
        line_clean = re.sub(r'^\s*[\(\[]?(\d{1,2}:)?\d{1,2}:\d{2}[\)\]]?\s*', '', line)
        line_clean = re.sub(r'^\d+[\.\)]?\s*', '', line_clean) # Remove "1. " or "1) " or "1 " numbering
        
        # Normalize dashes (em-dash, en-dash) to simple hyphen
        line_clean = line_clean.replace('—', '-').replace('–', '-')
        
        # Look for the dash separator

        # We assume "Artist - Title" format which is most common
        # But sometimes it might be "Title - Artist". 
        # It's hard to distinguish programmatically without a database, 
        # so we will default to Artist - Title and let the user correct if needed or search both.
        
        if ' - ' in line_clean:
            parts = line_clean.split(' - ')
            if len(parts) >= 2:
                artist = parts[0].strip()
                title = ' - '.join(parts[1:]).strip()
                
                # Case: "- Title" (Artist is empty)
                if len(artist) == 0 and len(title) > 0:
                     songs.append(("", title))
                # Normal Case: "Artist - Title"
                elif len(artist) > 0 and len(title) > 0:
                    songs.append((artist, title))
        else:
            # No dash separator. Treat whole line as title if it's substantial
            # e.g. "Manhattan Project"
            if len(line_clean) > 3: # Arbitrary min length to avoid noise
                songs.append(("", line_clean))
                    
    return songs

if __name__ == "__main__":
    # Test
    sample = """
    00:00 Intro
    00:15 The Weeknd - Blinding Lights
    03:45 Dua Lipa - Levitating
    Something else here
    5. Michael Jackson - Billie Jean
    """
    print(parse_description(sample))
