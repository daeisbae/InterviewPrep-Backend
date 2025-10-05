from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from interview_prep_backend.config import get_settings
from interview_prep_backend.routers import interview
from interview_prep_backend.schemas import HealthResponse

logging.basicConfig(level=logging.INFO)

settings = get_settings()

app = FastAPI(
    title="Interview Coach Backend",
    version="0.1.0",
    description="Backend services for the browser-only interview coach MVP.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interview.router)


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", environment=settings.environment)


@app.get("/config", tags=["system"])
def config_snapshot() -> Any:
    snapshot = settings.model_dump(exclude={"deepseek_api_key", "aws_access_key_id", "aws_secret_access_key"})
    return snapshot


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("interview_prep_backend.main:app", host="0.0.0.0", port=8000, reload=True)
