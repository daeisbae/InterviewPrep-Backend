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
        print("Warning: ", settings.aws_s3_bucket)
        print("Warning: ", settings.aws_access_key_id)
        print("Warning: ", settings.aws_secret_access_key)  
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


async def analyze_video_with_rekognition(file_key: str, file_extension: str = "mov") -> Optional[Dict[str, Any]]:
    """Analyze video from S3 using AWS Rekognition.
    
    Supported formats: MOV, MPEG-4, MP4, AVI (WebM is NOT supported)
    """
    settings = get_settings()
    if not settings.aws_s3_bucket:
        import logging
        logger = logging.getLogger(__name__)
        logger.error("AWS S3 bucket not configured for Rekognition")
        return None
    
    # Check for unsupported formats
    unsupported_formats = ['webm', 'ogg', 'flac', 'wav', 'mp3']
    if file_extension.lower() in unsupported_formats:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Rekognition does not support {file_extension.upper()} format. Supported: MOV, MP4, AVI, MPEG-4")
        return None
    
    client = _build_client("rekognition")
    if client is None:
        import logging
        logger = logging.getLogger(__name__)
        logger.error("Failed to build Rekognition client - check boto3 installation and AWS credentials")
        return None
    
    loop = asyncio.get_event_loop()
    
    try:
        # Start face detection job
        def start_detection():
            return client.start_face_detection(
                Video={'S3Object': {'Bucket': settings.aws_s3_bucket, 'Name': file_key}},
                FaceAttributes='ALL'
            )
        
        job_response = await loop.run_in_executor(None, start_detection)
        job_id = job_response['JobId']
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Rekognition job started: {job_id} - Video analysis typically takes 30-120 seconds, please wait...")
        
        # Poll for completion with progressive backoff
        # AWS Rekognition Video typically takes 30-120 seconds for short videos
        max_attempts = 60  # ~4-5 minutes max with progressive intervals
        poll_interval = 4  # Start with 4 seconds
        
        for attempt in range(max_attempts):
            def get_detection():
                return client.get_face_detection(JobId=job_id)
            
            result = await loop.run_in_executor(None, get_detection)
            status = result['JobStatus']
            
            # Log less frequently to reduce noise (every 5 attempts after attempt 5)
            if attempt < 5 or attempt % 5 == 0:
                elapsed_time = attempt * poll_interval
                logger.info(f"Rekognition job status: {status} (elapsed: {elapsed_time}s, attempt {attempt + 1}/{max_attempts})")
            
            if status == 'SUCCEEDED':
                faces = result.get('Faces', [])
                if not faces:
                    logger.warning("Rekognition succeeded but no faces detected")
                    return None
                
                logger.info(f"Found {len(faces)} face detections")
                
                # Aggregate emotions across all detected faces
                all_emotions = []
                for face in faces:
                    if 'Face' in face and 'Emotions' in face['Face']:
                        all_emotions.extend(face['Face']['Emotions'])
                
                if not all_emotions:
                    logger.warning("No emotions found in face detections")
                    return None
                
                # Calculate average scores for all emotion types
                happiness_scores = [_emotion_score([e], "HAPPY") for e in all_emotions]
                calm_scores = [_emotion_score([e], "CALM") for e in all_emotions]
                fear_scores = [_emotion_score([e], "FEAR") for e in all_emotions]
                confused_scores = [_emotion_score([e], "CONFUSED") for e in all_emotions]
                sad_scores = [_emotion_score([e], "SAD") for e in all_emotions]
                angry_scores = [_emotion_score([e], "ANGRY") for e in all_emotions]
                surprised_scores = [_emotion_score([e], "SURPRISED") for e in all_emotions]
                disgusted_scores = [_emotion_score([e], "DISGUSTED") for e in all_emotions]
                
                # Average each emotion type
                happiness = sum(happiness_scores) / len(all_emotions) if all_emotions else 0
                calm = sum(calm_scores) / len(all_emotions) if all_emotions else 0
                fear = sum(fear_scores) / len(all_emotions) if all_emotions else 0
                confused = sum(confused_scores) / len(all_emotions) if all_emotions else 0
                sad = sum(sad_scores) / len(all_emotions) if all_emotions else 0
                angry = sum(angry_scores) / len(all_emotions) if all_emotions else 0
                surprised = sum(surprised_scores) / len(all_emotions) if all_emotions else 0
                disgusted = sum(disgusted_scores) / len(all_emotions) if all_emotions else 0
                
                # Calculate composite metrics for interview performance
                nervous = fear + confused  # Nervousness = fear + confusion
                negative = sad + angry + disgusted  # Negative emotions
                
                # Engagement: High when calm, happy, or surprised (showing interest)
                engagement = min(1.0, (happiness + calm + surprised * 0.5) / 200 + 0.3)
                
                # Positivity: Happy expressions minus negative emotions
                positivity = min(1.0, max(0.0, (happiness - negative * 0.5) / 100))
                
                # Anxiety: Fear + confusion + negative emotions
                anxiety_hint = min(1.0, (nervous + negative * 0.3) / 100)
                
                # Confidence: Inverse of anxiety, boosted by calm and happiness
                confidence = min(1.0, max(0.0, (calm + happiness * 0.5 - nervous * 0.5) / 100))
                
                logger.info(
                    f"Emotion analysis - Happy: {happiness:.1f}%, Calm: {calm:.1f}%, "
                    f"Fear: {fear:.1f}%, Confused: {confused:.1f}%, Sad: {sad:.1f}%"
                )
                logger.info(
                    f"Metrics - Engagement: {engagement:.2f}, Positivity: {positivity:.2f}, "
                    f"Anxiety: {anxiety_hint:.2f}, Confidence: {confidence:.2f}"
                )
                
                return {
                    "engagement": engagement,
                    "positivity": positivity,
                    "anxiety_hint": anxiety_hint,
                    "confidence": confidence,
                    # Include raw emotion scores for detailed analysis
                    "emotions": {
                        "happy": round(happiness, 2),
                        "calm": round(calm, 2),
                        "fear": round(fear, 2),
                        "confused": round(confused, 2),
                        "sad": round(sad, 2),
                        "angry": round(angry, 2),
                        "surprised": round(surprised, 2),
                        "disgusted": round(disgusted, 2),
                    }
                }
            elif status == 'FAILED':
                logger.error(f"Rekognition job failed: {result.get('StatusMessage', 'Unknown error')}")
                return None
            elif status == 'IN_PROGRESS':
                # Progressive backoff: increase wait time after 15 attempts
                if attempt >= 15:
                    poll_interval = 6  # Increase to 6 seconds after ~1 minute
            
            await asyncio.sleep(poll_interval)
        
        logger.error(f"Rekognition job timed out after {max_attempts} attempts")
        return None
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Rekognition analysis error: {type(e).__name__}: {str(e)}")
        return None


async def transcribe_audio_from_s3(file_key: str, file_extension: str = "mov") -> Optional[Dict[str, Any]]:
    """Transcribe audio/video from S3 using AWS Transcribe.
    
    Supported formats: MOV, MP4, MP3, WAV, FLAC, WebM, AMR, OGG
    """
    settings = get_settings()
    if not settings.aws_s3_bucket:
        return None
    
    client = _build_client("transcribe")
    if client is None:
        return None
    
    job_name = f"transcribe-{uuid.uuid4()}"
    media_uri = f"s3://{settings.aws_s3_bucket}/{file_key}"
    
    # Map file extensions to AWS Transcribe MediaFormat
    format_mapping = {
        'mp3': 'mp3',
        'mp4': 'mp4',
        'mov': 'mp4',  # MOV uses mp4 format
        'wav': 'wav',
        'flac': 'flac',
        'webm': 'webm',
        'amr': 'amr',
        'ogg': 'ogg'
    }
    media_format = format_mapping.get(file_extension.lower(), 'mp4')
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Starting transcription with MediaFormat={media_format} for file extension={file_extension}")
    
    loop = asyncio.get_event_loop()
    
    # Start transcription job
    await loop.run_in_executor(
        None,
        lambda: client.start_transcription_job(
            TranscriptionJobName=job_name,
            LanguageCode="en-US",
            MediaFormat=media_format,
            Media={"MediaFileUri": media_uri},
        )
    )
    
    logger.info(f"Transcription job started: {job_name}")
    
    # Poll for completion with progressive backoff
    # AWS Transcribe typically takes 30-180 seconds depending on audio length
    max_attempts = 60  # ~4-5 minutes max with progressive intervals
    poll_interval = 4  # Start with 4 seconds
    
    for attempt in range(max_attempts):
        result = await loop.run_in_executor(
            None,
            lambda: client.get_transcription_job(TranscriptionJobName=job_name)
        )
        
        status = result['TranscriptionJob']['TranscriptionJobStatus']
        
        # Log less frequently to reduce noise
        if attempt < 5 or attempt % 5 == 0:
            elapsed_time = attempt * poll_interval
            logger.info(f"Transcription job status: {status} (elapsed: {elapsed_time}s, attempt {attempt + 1}/{max_attempts})")
        
        if status == 'COMPLETED':
            transcript_uri = result['TranscriptionJob']['Transcript']['TranscriptFileUri']
            logger.info(f"Transcription completed successfully")
            
            # Download and parse transcript (you'd need to fetch the JSON from the URI)
            # For now, returning a simplified structure
            return {
                "job_name": job_name,
                "status": "COMPLETED",
                "transcript_uri": transcript_uri,
            }
        elif status == 'FAILED':
            logger.error(f"Transcription job failed: {result['TranscriptionJob'].get('FailureReason', 'Unknown error')}")
            return None
        elif status == 'IN_PROGRESS':
            # Progressive backoff: increase wait time after 15 attempts
            if attempt >= 15:
                poll_interval = 6  # Increase to 6 seconds after ~1 minute
        
        await asyncio.sleep(poll_interval)
    
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
