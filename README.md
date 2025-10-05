# Interview Coach Backend

FastAPI backend for a browser-only virtual interview coach that processes multimodal cues and produces real-time coaching feedback while keeping media on-device whenever possible.

## Features

- Session management for interview coaching runs.
- Aggregates facial landmarks, vocal metrics, and speech transcripts into confidence/anxiety scores.
- Rule-driven coaching state machine powered by JSON configuration.
- Optional adapters for DeepSeek LLM responses and AWS Rekognition / Transcribe enrichment.
- Returns structured coaching feedback including subtitles, TTS text, and actionable tips.

## Project Layout

- `app/main.py` – FastAPI application entry point.
- `app/config.py` – Environment-driven settings.
- `app/schemas.py` – Pydantic models for request/response payloads.
- `app/services/` – Domain services (state machine, analytics, external APIs).
- `app/routers/` – API routers grouped by domain.
- `data/rules.json` – Sample rule configuration for the coaching state machine.
- `tests/` – Automated tests.

## Getting Started

Create and activate a Python 3.9+ virtual environment, then install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### Environment Variables

Create a `.env` file in the project root to configure external integrations:

```bash
DEEPSEEK_API_KEY=your-key
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
```

All external calls are optional; when credentials are missing, the backend falls back to deterministic local heuristics so you can run locally without cloud access.

### Run the Server

```bash
uvicorn app.main:app --reload
```

### Run Tests

```bash
pytest
```

## API Overview

- `POST /api/v1/sessions` – Create a coaching session and return an identifier.
- `POST /api/v1/sessions/{session_id}/ingest` – Submit the latest multimodal signals; returns updated coaching feedback.
- `GET /health` – Health check for monitoring.

See the inline OpenAPI docs at `/docs` for the full contract.

## Extending the Rule Engine

Update `data/rules.json` to add or tweak coaching states. Each state defines guard thresholds and the response payload (voice line, subtitle, tip). The server reloads rules on startup.

## License

MIT
