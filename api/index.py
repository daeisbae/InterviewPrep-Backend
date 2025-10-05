import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from mangum import Mangum
from interview_prep_backend.main import app

# Vercel serverless handler
handler = Mangum(app, lifespan="off")
