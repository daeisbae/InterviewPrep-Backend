from typing import List, Optional

from pydantic import BaseModel, Field, NonNegativeFloat, PositiveFloat


class FacialMetrics(BaseModel):
    engagement: float = Field(ge=0.0, le=1.0)
    positivity: float = Field(ge=0.0, le=1.0)
    microexpressions: Optional[List[str]] = None


class VoiceMetrics(BaseModel):
    loudness: float = Field(ge=0.0, le=1.0)
    pitch_variance: float = Field(ge=0.0, le=1.0)
    speech_rate_wpm: PositiveFloat
    filler_ratio: float = Field(ge=0.0, le=1.0)
    energy: float = Field(ge=0.0, le=1.0)


class TranscriptSegment(BaseModel):
    text: str
    start_time: NonNegativeFloat
    end_time: NonNegativeFloat
    confidence: float = Field(ge=0.0, le=1.0)


class BrowserSignalPayload(BaseModel):
    session_id: Optional[str] = None
    facial: FacialMetrics
    voice: VoiceMetrics
    transcript: List[TranscriptSegment]
    sentiment_score: Optional[float] = Field(default=None, ge=-1.0, le=1.0)
    speech_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    latency_ms: Optional[float] = Field(default=None, ge=0.0)


class SessionCreateRequest(BaseModel):
    display_name: Optional[str] = None


class SessionCreateResponse(BaseModel):
    session_id: str
    state: str
    tip: str
    subtitle: str
    tts_text: str


class CoachingScore(BaseModel):
    confidence: float = Field(ge=0.0, le=1.0)
    anxiety: float = Field(ge=0.0, le=1.0)


class CoachingResponse(BaseModel):
    session_id: str
    state: str
    scores: CoachingScore
    subtitle: str
    tip: str
    tts_text: str
    transcript_highlights: List[str]
    latency_ms: Optional[float] = None


class HealthResponse(BaseModel):
    status: str
    environment: str


class UploadUrlRequest(BaseModel):
    file_type: str = Field(description="video or audio")
    content_type: str = Field(default="video/webm", description="MIME type")


class UploadUrlResponse(BaseModel):
    upload_url: str
    file_key: str
    expires_in: int = 3600


class AnalysisRequest(BaseModel):
    file_key: str


class FacialAnalysis(BaseModel):
    engagement: float = Field(ge=0.0, le=1.0)
    positivity: float = Field(ge=0.0, le=1.0)
    anxiety_hint: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0, description="Overall confidence level based on facial expressions")
    emotions: dict = Field(
        default_factory=dict,
        description="Raw emotion scores: happy, calm, fear, confused, sad, angry, surprised, disgusted"
    )


class TranscriptAnalysis(BaseModel):
    full_text: str
    filler_ratio: float = Field(ge=0.0, le=1.0)
    filler_hits: int
    mumble_score: float = Field(ge=0.0, le=1.0)
    segments: List[TranscriptSegment] = Field(default_factory=list)


class CoachingAdvice(BaseModel):
    tip: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    anxiety_score: float = Field(ge=0.0, le=1.0)
    recommendations: List[str]


class AnalysisResponse(BaseModel):
    file_key: str
    status: str
    facial_analysis: Optional[FacialAnalysis] = None
    transcript_analysis: Optional[TranscriptAnalysis] = None
    coaching_advice: Optional[CoachingAdvice] = None
    processing_time_ms: Optional[float] = None
