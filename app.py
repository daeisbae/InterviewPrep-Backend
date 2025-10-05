"""
Entry point for deployment platforms that look for app.py
This file imports the FastAPI app from the main module.

Supported platforms:
- Vercel (uses api/index.py instead)
- Railway (uses Procfile)
- Render (uses Procfile)
- Heroku (uses Procfile)
- AWS Elastic Beanstalk
- Generic WSGI servers
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from interview_prep_backend.main import app

# For WSGI servers (Gunicorn, etc.)
# The app variable is automatically discovered
__all__ = ["app"]

if __name__ == "__main__":
    # For local testing: python app.py
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
