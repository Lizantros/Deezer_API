from server import app

# Vercel needs a variable named 'app' in the module
# We can just re-export it.
# Note: Vercel Python runtime structure usually expects an 'api' folder or specific config.
# But with the rewrite rule in vercel.json pointing to /api/index.py, we need this file.
