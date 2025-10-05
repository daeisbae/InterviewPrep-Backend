from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict, Optional

from interview_prep_backend.config import get_settings


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


def generate_presigned_upload_url(file_type: str = "video", content_type: str = "video/webm") -> Dict[str, str]:
    """Generate a presigned URL for uploading a file to S3."""
    settings = get_settings()
    if not settings.aws_s3_bucket:
        raise RuntimeError("AWS S3 bucket is not configured.")
    
    boto3 = _import_boto3()
    if boto3 is None:
        raise RuntimeError("boto3 is not installed. Install with: uv pip install boto3")
    
    s3_client = _build_client("s3")
    if s3_client is None:
        raise RuntimeError("AWS S3 client could not be created.")
    
    file_key = f"uploads/{file_type}/{uuid.uuid4()}.webm"
    
    presigned_url = s3_client.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': settings.aws_s3_bucket,
            'Key': file_key,
            'ContentType': content_type,
        },
        ExpiresIn=3600  # URL expires in 1 hour
    )
    
    return {
        "upload_url": presigned_url,
        "file_key": file_key,
        "bucket": settings.aws_s3_bucket,
    }


def upload_file_to_s3(file_content: bytes, content_type: str, original_filename: str = "interview.webm") -> str:
    """Upload file directly to S3 from server and return the file key."""
    settings = get_settings()
    if not settings.aws_s3_bucket:
        raise RuntimeError("AWS S3 bucket is not configured.")
    
    boto3 = _import_boto3()
    if boto3 is None:
        raise RuntimeError("boto3 is not installed. Install with: uv pip install boto3")
    
    s3_client = _build_client("s3")
    if s3_client is None:
        raise RuntimeError("AWS S3 client could not be created.")
    
    # Generate unique file key
    extension = original_filename.split('.')[-1] if '.' in original_filename else 'webm'
    file_key = f"interviews/{uuid.uuid4()}.{extension}"
    
    # Upload to S3
    s3_client.put_object(
        Bucket=settings.aws_s3_bucket,
        Key=file_key,
        Body=file_content,
        ContentType=content_type,
    )
    
    return file_key



async def get_s3_object(file_key: str) -> bytes:
    """Download a file from S3."""
    settings = get_settings()
    if not settings.aws_s3_bucket:
        raise RuntimeError("AWS S3 bucket is not configured.")
    
    s3_client = _build_client("s3")
    if s3_client is None:
        raise RuntimeError("AWS S3 client could not be created.")
    
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: s3_client.get_object(Bucket=settings.aws_s3_bucket, Key=file_key)
    )
    return response['Body'].read()


async def analyze_video_with_rekognition(file_key: str) -> Optional[Dict[str, float]]:
    """Analyze video from S3 using AWS Rekognition."""
    settings = get_settings()
    if not settings.aws_s3_bucket:
        return None
    
    client = _build_client("rekognition")
    if client is None:
        return None
    
    loop = asyncio.get_event_loop()
    
    # Start face detection job
    job_response = await loop.run_in_executor(
        None,
        lambda: client.start_face_detection(
            Video={'S3Object': {'Bucket': settings.aws_s3_bucket, 'Name': file_key}},
            FaceAttributes='ALL'
        )
    )
    
    job_id = job_response['JobId']
    
    # Poll for completion (simplified - in production, use SNS notifications)
    max_attempts = 60
    for _ in range(max_attempts):
        result = await loop.run_in_executor(
            None,
            lambda: client.get_face_detection(JobId=job_id)
        )
        
        status = result['JobStatus']
        if status == 'SUCCEEDED':
            faces = result.get('Faces', [])
            if not faces:
                return None
            
            # Aggregate emotions across all detected faces
            all_emotions = []
            for face in faces:
                if 'Face' in face and 'Emotions' in face['Face']:
                    all_emotions.extend(face['Face']['Emotions'])
            
            if not all_emotions:
                return None
            
            # Calculate average scores
            happiness = sum(_emotion_score([e], "HAPPY") for e in all_emotions) / len(all_emotions)
            calm = sum(_emotion_score([e], "CALM") for e in all_emotions) / len(all_emotions)
            nervous = sum(_emotion_score([e], "FEAR") + _emotion_score([e], "CONFUSED") for e in all_emotions) / len(all_emotions)
            
            engagement = min(1.0, (happiness + calm) / 200 + 0.3)
            positivity = min(1.0, happiness / 100)
            anxiety_hint = min(1.0, nervous / 100)
            
            return {
                "engagement": engagement,
                "positivity": positivity,
                "anxiety_hint": anxiety_hint,
            }
        elif status == 'FAILED':
            return None
        
        await asyncio.sleep(2)
    
    return None


async def transcribe_audio_from_s3(file_key: str) -> Optional[Dict[str, Any]]:
    """Transcribe audio/video from S3 using AWS Transcribe."""
    settings = get_settings()
    if not settings.aws_s3_bucket:
        return None
    
    client = _build_client("transcribe")
    if client is None:
        return None
    
    job_name = f"transcribe-{uuid.uuid4()}"
    media_uri = f"s3://{settings.aws_s3_bucket}/{file_key}"
    
    loop = asyncio.get_event_loop()
    
    # Start transcription job
    await loop.run_in_executor(
        None,
        lambda: client.start_transcription_job(
            TranscriptionJobName=job_name,
            LanguageCode="en-US",
            MediaFormat="webm",
            Media={"MediaFileUri": media_uri},
        )
    )
    
    # Poll for completion (simplified - in production, use SNS notifications)
    max_attempts = 60
    for _ in range(max_attempts):
        result = await loop.run_in_executor(
            None,
            lambda: client.get_transcription_job(TranscriptionJobName=job_name)
        )
        
        status = result['TranscriptionJob']['TranscriptionJobStatus']
        if status == 'COMPLETED':
            transcript_uri = result['TranscriptionJob']['Transcript']['TranscriptFileUri']
            
            # Download and parse transcript (you'd need to fetch the JSON from the URI)
            # For now, returning a simplified structure
            return {
                "job_name": job_name,
                "status": "COMPLETED",
                "transcript_uri": transcript_uri,
            }
        elif status == 'FAILED':
            return None
        
        await asyncio.sleep(2)
    
    return None


async def fetch_transcript_text(transcript_uri: str) -> str:
    """Fetch and parse the transcript JSON from AWS Transcribe."""
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(transcript_uri)
            response.raise_for_status()
            data = response.json()
            
            # Extract transcript text from AWS Transcribe JSON format
            if 'results' in data and 'transcripts' in data['results']:
                transcripts = data['results']['transcripts']
                if transcripts and len(transcripts) > 0:
                    return transcripts[0].get('transcript', '')
            
            return ""
    except Exception:
        # Fallback if httpx is not available or parsing fails
        return "Transcript could not be fetched"
