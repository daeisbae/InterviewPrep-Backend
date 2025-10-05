# Interview Prep Backend API Documentation

## Overview
This API allows users to upload interview practice videos for AI-powered analysis using AWS services (S3, Transcribe, Rekognition).

## Base URL
```
http://localhost:8000
```

## Endpoints

### 1. Health Check
```
GET /health
```
Check if the API is running.

**Response:**
```json
{
  "status": "ok",
  "environment": "development"
}
```

---

### 2. Get Upload URL
```
POST /api/v1/upload
```
Generate a presigned S3 URL to upload a video file.

**Request:** None required

**Response:**
```json
{
  "upload_url": "https://s3.amazonaws.com/...",
  "video_id": "550e8400-e29b-41d4-a716-446655440000",
  "expires_in": 3600
}
```

**Usage:**
```bash
# Step 1: Get upload URL
curl -X POST http://localhost:8000/api/v1/upload

# Step 2: Upload video to the presigned URL
curl -X PUT -H "Content-Type: video/mp4" \
  --upload-file interview.mp4 \
  "<upload_url_from_step_1>"
```

---

### 3. Start Video Analysis
```
POST /api/v1/analyze/{video_id}
```
Start AWS Transcribe and Rekognition analysis on an uploaded video.

**Path Parameters:**
- `video_id`: UUID from upload response

**Response:**
```json
{
  "video_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PROCESSING",
  "transcript": null,
  "facial_analysis": null,
  "voice_analysis": null,
  "coaching_scores": null,
  "coaching_tips": [],
  "transcript_highlights": [],
  "processing_time_ms": null
}
```

---

### 4. Get Analysis Results
```
GET /api/v1/analyze/{video_id}
```
Poll this endpoint to get analysis results.

**Path Parameters:**
- `video_id`: UUID from upload response

**Response (when COMPLETED):**
```json
{
  "video_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "COMPLETED",
  "transcript": [
    {
      "text": "So, um, I think that I would be a great fit...",
      "start_time": 0.0,
      "end_time": 45.2,
      "confidence": 0.95
    }
  ],
  "facial_analysis": {
    "engagement": 0.72,
    "positivity": 0.68,
    "anxiety": 0.35,
    "dominant_emotions": ["HAPPY", "CALM", "CONFUSED"]
  },
  "voice_analysis": {
    "filler_ratio": 0.18,
    "filler_count": 12,
    "total_words": 67,
    "speaking_time_seconds": 45.2,
    "speech_rate_wpm": 89
  },
  "coaching_scores": {
    "confidence": 0.65,
    "anxiety": 0.42
  },
  "coaching_tips": [
    "Reduce filler words like 'um', 'uh', 'like' - found 18% in your speech",
    "Pause instead of using filler words when thinking",
    "Take deep breaths before answering to calm your nerves"
  ],
  "transcript_highlights": [
    "so um I think",
    "like you know the",
    "basically um what"
  ],
  "processing_time_ms": 12450.5
}
```

**Status Values:**
- `PROCESSING`: Analysis in progress, poll again
- `COMPLETED`: Analysis finished successfully
- `FAILED`: Analysis failed

---

## Complete Workflow

```bash
# 1. Get upload URL
RESPONSE=$(curl -X POST http://localhost:8000/api/v1/upload)
UPLOAD_URL=$(echo $RESPONSE | jq -r '.upload_url')
VIDEO_ID=$(echo $RESPONSE | jq -r '.video_id')

# 2. Upload video
curl -X PUT -H "Content-Type: video/mp4" \
  --upload-file my_interview.mp4 \
  "$UPLOAD_URL"

# 3. Start analysis
curl -X POST "http://localhost:8000/api/v1/analyze/$VIDEO_ID"

# 4. Poll for results (every 5-10 seconds)
while true; do
  RESULT=$(curl "http://localhost:8000/api/v1/analyze/$VIDEO_ID")
  STATUS=$(echo $RESULT | jq -r '.status')
  
  if [ "$STATUS" = "COMPLETED" ]; then
    echo $RESULT | jq
    break
  elif [ "$STATUS" = "FAILED" ]; then
    echo "Analysis failed"
    break
  fi
  
  echo "Still processing..."
  sleep 10
done
```

---

## Environment Variables

Required AWS configuration:
```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET_NAME=interview-prep-videos
```

Optional settings:
```bash
ENABLE_DEEPSEEK=true
DEEPSEEK_API_KEY=your_key
LOW_CONFIDENCE_THRESHOLD=0.45
HIGH_ANXIETY_THRESHOLD=0.6
```

---

## AWS Services Used

1. **S3**: Video storage with presigned URLs
2. **Transcribe**: Speech-to-text transcription
3. **Rekognition**: Facial emotion detection

## Scoring Algorithm

**Confidence Score (0-1):**
- Based on facial emotions (happiness + calmness)
- Higher positive emotions = higher confidence

**Anxiety Score (0-1):**
- Based on fear/confusion emotions + filler word ratio
- Higher negative emotions/fillers = higher anxiety

**Coaching Tips:**
- Generated based on thresholds:
  - Confidence < 0.45: Eye contact and smiling tips
  - Anxiety > 0.6: Breathing and pacing tips
  - Filler ratio > 15%: Filler word reduction tips
