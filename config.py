import os
from dotenv import load_dotenv

load_dotenv()

# Option 1: ARL Cookie (Best "No App" method)
ARL = os.getenv('DEEZER_ARL')

# Option 2: Manual Access Token (for when App creation is disabled)
ACCESS_TOKEN = os.getenv('DEEZER_ACCESS_TOKEN')

# Option 2: OAuth App (if you have one)
APP_ID = os.getenv('DEEZER_APP_ID')
APP_SECRET = os.getenv('DEEZER_APP_SECRET')
REDIRECT_URI = os.getenv('DEEZER_REDIRECT_URI', 'http://localhost:8080/callback')
