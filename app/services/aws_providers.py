from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from app.config import get_settings


def _import_boto3():  # pragma: no cover - import side effect
    try:
        import boto3  # type: ignore
    except ModuleNotFoundError:
        return None
    return boto3


def _build_client(service: str):
    boto3 = _import_boto3()
    if boto3 is None:
        return None
    settings = get_settings()
    if not settings.aws_region:
        return None

    common_kwargs = {"region_name": settings.aws_region}
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        common_kwargs.update(
            {
                "aws_access_key_id": settings.aws_access_key_id,
                "aws_secret_access_key": settings.aws_secret_access_key,
            }
        )
    return boto3.client(service, **common_kwargs)


async def detect_face_sentiment(image_bytes: bytes) -> Optional[Dict[str, float]]:
    client = _build_client("rekognition")
    if client is None:
        return None

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: client.detect_faces(Image={"Bytes": image_bytes}, Attributes=["ALL"]),
    )
    details = response.get("FaceDetails", [])
    if not details:
        return None
    emotions = details[0].get("Emotions", [])

    happiness = _emotion_score(emotions, "HAPPY")
    calm = _emotion_score(emotions, "CALM")
    nervous = _emotion_score(emotions, "FEAR") + _emotion_score(emotions, "CONFUSED")

    engagement = min(1.0, (happiness + calm) / 200 + 0.3)
    positivity = min(1.0, happiness / 100)
    anxiety_hint = min(1.0, nervous / 100)

    return {
        "engagement": engagement,
        "positivity": positivity,
        "anxiety_hint": anxiety_hint,
    }


def analyze_transcript_locally(transcript_text: str) -> Dict[str, Any]:
    settings = get_settings()
    words = transcript_text.lower().split()
    total_words = max(len(words), 1)

    filler_hits = sum(1 for word in words if word.strip(",.?!") in settings.filler_words)
    filler_ratio = filler_hits / total_words

    long_pauses = transcript_text.count("...")
    mumble_score = min(1.0, (filler_ratio * 0.5) + (long_pauses * 0.05))

    return {
        "filler_ratio": filler_ratio,
        "filler_hits": filler_hits,
        "mumble_score": mumble_score,
    }


async def start_transcription_job(media_uri: str, job_name: str) -> Dict[str, Any]:
    client = _build_client("transcribe")
    if client is None:
        raise RuntimeError("AWS Transcribe is not configured. Provide credentials or disable external APIs.")

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: client.start_transcription_job(
            TranscriptionJobName=job_name,
            LanguageCode="en-US",
            Media={"MediaFileUri": media_uri},
            OutputBucketName=None,
        ),
    )
    return {"job_name": job_name, "status": "IN_PROGRESS"}


def _emotion_score(emotions: Any, label: str) -> float:
    for emotion in emotions:
        if emotion.get("Type") == label:
            return float(emotion.get("Confidence", 0.0))
    return 0.0
