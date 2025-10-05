from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.schemas import (
    BrowserSignalPayload,
    CoachingResponse,
    CoachingScore,
    SessionCreateRequest,
    SessionCreateResponse,
)
from app.services import aws_providers, deepseek
from app.services.analytics import compute_scores, extract_filler_segments
from app.services.session_store import store
from app.services.state_machine import StateMachine, load_state_machine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["coaching"])
state_machine: StateMachine = load_state_machine()


@router.post("/sessions", response_model=SessionCreateResponse)
async def create_session(payload: SessionCreateRequest | None = None) -> SessionCreateResponse:
    session_id = store.create()
    baseline = CoachingScore(confidence=0.55, anxiety=0.45)
    response = state_machine.evaluate(session_id, baseline)
    store.set_last_response(session_id, response)
    return SessionCreateResponse(
        session_id=session_id,
        state=response.state,
        tip=response.tip,
        subtitle=response.subtitle,
        tts_text=response.tts_text,
    )


@router.post("/sessions/{session_id}/ingest", response_model=CoachingResponse)
async def ingest_signals(session_id: str, payload: BrowserSignalPayload) -> CoachingResponse:
    if not store.has(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    scores = compute_scores(payload)
    speech_texts: List[str] = [segment.text for segment in payload.transcript]

    rule_result = state_machine.evaluate(session_id, scores, latency_ms=payload.latency_ms)
    highlights = extract_filler_segments(speech_texts)

    updated = rule_result.model_copy(update={"transcript_highlights": highlights})
    updated = await _maybe_enrich_with_external(updated, speech_texts)

    store.set_last_response(session_id, updated)
    return updated


async def _maybe_enrich_with_external(response: CoachingResponse, speech_texts: List[str]) -> CoachingResponse:
    settings = get_settings()
    if not settings.enable_external_apis:
        return response

    combined = " ".join(speech_texts[-3:]) if speech_texts else ""
    prompt = (
        f"Confidence={response.scores.confidence:.2f}, Anxiety={response.scores.anxiety:.2f}. "
        f"Recent transcript: {combined}"
    )

    try:
        llm_tip = await deepseek.generate_coaching_line(prompt)
    except Exception as exc:  # pragma: no cover - network failures
        logger.warning("DeepSeek enrichment failed: %s", exc)
        llm_tip = None

    if llm_tip:
        response = response.model_copy(update={"tip": llm_tip, "tts_text": llm_tip})

    if speech_texts:
        analysis = aws_providers.analyze_transcript_locally(" ".join(speech_texts))
        anxiety = max(response.scores.anxiety, float(analysis["mumble_score"]))
        scores = response.scores.model_copy(update={"anxiety": anxiety})
        response = response.model_copy(update={"scores": scores})

    return response
