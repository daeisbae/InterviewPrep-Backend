from __future__ import annotations

import logging
import time
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile

from interview_prep_backend.config import get_settings
from interview_prep_backend.schemas import (
    AnalysisResponse,
    CoachingAdvice,
    FacialAnalysis,
    TranscriptAnalysis,
    TranscriptSegment,
)
from interview_prep_backend.services import aws_providers, deepseek

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["interview"])


@router.post("/analyze-interview", response_model=AnalysisResponse)
async def analyze_interview(file: UploadFile = File(...)) -> AnalysisResponse:
    """
    Upload video/audio and automatically analyze it.
    
    This single endpoint:
    1. Receives the video/audio file from client
    2. Uploads to S3
    3. Triggers AWS Rekognition for facial analysis
    4. Triggers AWS Transcribe for speech-to-text
    5. Analyzes transcript for filler words and mumbling
    6. Calls LLM for personalized coaching advice
    7. Returns comprehensive analysis results
    """
    settings = get_settings()
    start_time = time.time()
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith(("video/", "audio/")):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Must be video/* or audio/*"
        )
    
    # Step 1: Upload to S3
    try:
        logger.info(f"Uploading file: {file.filename} ({file.content_type})")
        file_content = await file.read()
        file_key = aws_providers.upload_file_to_s3(
            file_content=file_content,
            content_type=file.content_type or "video/webm",
            original_filename=file.filename or "interview.webm"
        )
        logger.info(f"File uploaded to S3: {file_key}")
    except Exception as e:
        logger.error(f"S3 upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")
    
    facial_result = None
    transcript_result = None
    coaching_result = None
    
    # Step 2: Run facial analysis and transcription in parallel
    try:
        logger.info(f"Starting AWS analysis for {file_key}")
        facial_task = aws_providers.analyze_video_with_rekognition(file_key)
        transcript_task = aws_providers.transcribe_audio_from_s3(file_key)
        
        facial_data = await facial_task
        transcript_data = await transcript_task
        
        logger.info(f"Facial analysis: {facial_data is not None}, Transcript: {transcript_data is not None}")
        
        # Process facial analysis
        if facial_data:
            facial_result = FacialAnalysis(
                engagement=facial_data["engagement"],
                positivity=facial_data["positivity"],
                anxiety_hint=facial_data["anxiety_hint"]
            )
        
        # Process transcript
        if transcript_data and transcript_data.get("status") == "COMPLETED":
            # Fetch the actual transcript from the URI
            full_text = await aws_providers.fetch_transcript_text(transcript_data["transcript_uri"])
            
            text_analysis = aws_providers.analyze_transcript_locally(full_text)
            transcript_result = TranscriptAnalysis(
                full_text=full_text,
                filler_ratio=text_analysis["filler_ratio"],
                filler_hits=text_analysis["filler_hits"],
                mumble_score=text_analysis["mumble_score"],
                segments=[]
            )
            
            # Generate coaching advice using LLM
            confidence = 1.0 - (transcript_result.mumble_score * 0.5)
            anxiety = facial_result.anxiety_hint if facial_result else 0.5
            
            prompt = (
                f"Interview Performance Analysis:\n"
                f"- Confidence Score: {confidence:.2f}\n"
                f"- Anxiety Level: {anxiety:.2f}\n"
                f"- Filler Word Ratio: {transcript_result.filler_ratio:.2%}\n"
                f"- Transcript: {full_text[:500]}\n\n"
                f"Provide specific coaching tips and recommendations."
            )
            
            try:
                llm_tip = await deepseek.generate_coaching_line(prompt)
                coaching_result = CoachingAdvice(
                    tip=llm_tip or "Practice makes perfect! Keep working on your interview skills.",
                    confidence_score=confidence,
                    anxiety_score=anxiety,
                    recommendations=[
                        "Reduce filler words" if transcript_result.filler_ratio > 0.1 else "Good control of filler words",
                        "Maintain eye contact" if facial_result and facial_result.engagement < 0.6 else "Good engagement",
                        "Speak more clearly" if transcript_result.mumble_score > 0.5 else "Clear speech"
                    ]
                )
            except Exception as e:
                logger.warning(f"LLM coaching generation failed: {e}")
                coaching_result = CoachingAdvice(
                    tip="Keep practicing your interview skills!",
                    confidence_score=confidence,
                    anxiety_score=anxiety,
                    recommendations=["Review your performance and try again"]
                )
    
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    processing_time = (time.time() - start_time) * 1000
    
    logger.info(f"Analysis completed in {processing_time:.2f}ms")
    
    return AnalysisResponse(
        file_key=file_key,
        status="completed",
        facial_analysis=facial_result,
        transcript_analysis=transcript_result,
        coaching_advice=coaching_result,
        processing_time_ms=processing_time
    )
