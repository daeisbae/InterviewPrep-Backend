from app.schemas import (
    BrowserSignalPayload,
    FacialMetrics,
    TranscriptSegment,
    VoiceMetrics,
)
from app.services.analytics import compute_scores, extract_filler_segments


def payload_factory(**overrides):
    base = dict(
        facial=FacialMetrics(engagement=0.6, positivity=0.7),
        voice=VoiceMetrics(
            loudness=0.5,
            pitch_variance=0.4,
            speech_rate_wpm=120,
            filler_ratio=0.1,
            energy=0.6,
        ),
        transcript=[
            TranscriptSegment(text="I actually delivered the feature", start_time=0.0, end_time=4.0, confidence=0.9)
        ],
        sentiment_score=0.2,
        speech_confidence=0.8,
    )
    base.update(overrides)
    return BrowserSignalPayload(**base)


def test_compute_scores_balanced():
    payload = payload_factory()
    scores = compute_scores(payload)
    assert 0.0 <= scores.confidence <= 1.0
    assert 0.0 <= scores.anxiety <= 1.0
    assert scores.confidence > scores.anxiety


def test_extract_filler_segments():
    segments = ["Um I think", "We shipped it", "Like overall it was good"]
    highlights = extract_filler_segments(segments)
    assert len(highlights) == 2
