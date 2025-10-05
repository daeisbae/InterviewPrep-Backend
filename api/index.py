from mangum import Mangum
from interview_prep_backend.main import app

# Vercel serverless handler
handler = Mangum(app, lifespan="off")
