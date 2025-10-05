from __future__ import annotations

from typing import List

from interview_prep_backend.config import get_settings
from interview_prep_backend.schemas import BrowserSignalPayload, CoachingScore


def compute_scores(payload: BrowserSignalPayload) -> CoachingScore:
    settings = get_settings()
    facial = payload.facial
    voice = payload.voice
    speech_conf = payload.speech_confidence if payload.speech_confidence is not None else 0.7

    confidence_components = [
        facial.positivity * 0.4,
        facial.engagement * 0.2,
        (1 - payload.voice.filler_ratio) * 0.2,
        min(voice.energy + 0.1, 1.0) * 0.1,
        speech_conf * 0.1,
    ]
    confidence = _clamp(sum(confidence_components), 0.0, 1.0)

    anxiety_components = [
        payload.voice.filler_ratio * 0.35,
        (1 - facial.engagement) * 0.25,
        max(voice.pitch_variance - 0.5, 0.0) * 0.2,
        max(0.5 - voice.energy, 0.0) * 0.1,
        _sentiment_penalty(payload.sentiment_score) * 0.1,
    ]
    anxiety = _clamp(sum(anxiety_components), 0.0, 1.0)

    return CoachingScore(confidence=confidence, anxiety=anxiety)


def extract_filler_segments(transcript: List[str]) -> List[str]:
    settings = get_settings()
    lower = [segment.lower() for segment in transcript]
    fillers = []
    for segment in lower:
        for filler in settings.filler_words:
            if filler in segment:
                fillers.append(segment)
                break
    return fillers[:5]


def _sentiment_penalty(score: float | None) -> float:
    if score is None:
        return 0.05
    if score >= 0.2:
        return 0.0
    if score >= 0.0:
        return 0.05
    if score >= -0.4:
        return 0.1
    return 0.15


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))
