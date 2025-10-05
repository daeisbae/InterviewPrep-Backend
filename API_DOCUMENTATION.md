# Interview Prep Backend API Documentation

## Overview

This API provides endpoints for analyzing interview performance using AWS Rekognition (facial analysis), AWS Transcribe (speech-to-text), and LLM-based coaching advice.

**Base URL:** `http://localhost:8000`

---

## System Endpoints

### 1. Health Check
**GET** `/health`

Check if the API is running.

**Response:**
```json
{
  "status": "ok",
  "environment": "development"
}
```

---

### 2. Configuration
**GET** `/config`

Get current configuration (excludes sensitive keys).

**Response:**
```json
{
  "environment": "development",
  "deepseek_model": "deepseek-chat",
  "aws_region": "us-east-1",
  "enable_external_apis": true,
  ...
}
```

---

## Interview Analysis Endpoints

### 3. Generate Upload URL
**POST** `/api/v1/upload-url`

Generate a presigned S3 URL for uploading video/audio files.

**Request Body:**
```json
{
  "file_type": "video",
  "content_type": "video/webm"
}
```

**Parameters:**
- `file_type` (string): Type of file - "video" or "audio"
- `content_type` (string): MIME type (default: "video/webm")

**Response:**
```json
{
  "upload_url": "https://s3.amazonaws.com/bucket/uploads/video/uuid.webm?presigned-params",
  "file_key": "uploads/video/uuid.webm",
  "expires_in": 3600
}
```

**Frontend Usage:**
```javascript
// 1. Get upload URL
const response = await fetch('http://localhost:8000/api/v1/upload-url', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    file_type: 'video',
    content_type: 'video/webm'
  })
});
const { upload_url, file_key } = await response.json();

// 2. Upload video to S3
await fetch(upload_url, {
  method: 'PUT',
  headers: { 'Content-Type': 'video/webm' },
  body: videoBlob
});

// 3. Trigger analysis (see next endpoint)
```

---

### 4. Analyze Interview
**POST** `/api/v1/analyze`

Analyze uploaded video/audio and return comprehensive feedback.

**Request Body:**
```json
{
  "file_key": "uploads/video/uuid.webm"
}
```

**Parameters:**
- `file_key` (string): The file key returned from the upload URL endpoint

**Response:**
```json
{
  "file_key": "uploads/video/uuid.webm",
  "status": "completed",
  "facial_analysis": {
    "engagement": 0.75,
    "positivity": 0.82,
    "anxiety_hint": 0.35
  },
  "transcript_analysis": {
    "full_text": "Hello, I'm excited to discuss this opportunity...",
    "filler_ratio": 0.08,
    "filler_hits": 5,
    "mumble_score": 0.25,
    "segments": [
      {
        "text": "Hello, I'm excited",
        "start_time": 0.0,
        "end_time": 2.5,
        "confidence": 0.95
      }
    ]
  },
  "coaching_advice": {
    "tip": "Great job maintaining composure! Try to reduce 'um' and 'uh' fillers.",
    "confidence_score": 0.88,
    "anxiety_score": 0.35,
    "recommendations": [
      "Good control of filler words",
      "Good engagement",
      "Clear speech"
    ]
  },
  "processing_time_ms": 15234.5
}
```

**What This Endpoint Does:**
1. ✅ Triggers **AWS Rekognition** for facial emotion analysis
2. ✅ Triggers **AWS Transcribe** for speech-to-text conversion
3. ✅ Analyzes transcript for filler words (um, uh, like, etc.)
4. ✅ Calculates mumble/clarity scores
5. ✅ Calls **LLM (DeepSeek)** for personalized coaching advice
6. ✅ Returns comprehensive analysis with scores and recommendations

**Error Responses:**
- `400`: External APIs disabled (set `ENABLE_EXTERNAL_APIS=true`)
- `500`: Analysis failed (AWS services error, missing credentials, etc.)

---

## Environment Variables

Create a `.env` file in the project root:

```bash
# Environment
ENVIRONMENT=development

# AWS Configuration (REQUIRED for analysis)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET=your-interview-bucket

# DeepSeek LLM (REQUIRED for coaching)
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_MODEL=deepseek-chat

# Feature Flags
ENABLE_EXTERNAL_APIS=true
```

---

## Complete Frontend Flow

```javascript
// Step 1: Request upload URL
const urlResponse = await fetch('http://localhost:8000/api/v1/upload-url', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    file_type: 'video',
    content_type: 'video/webm'
  })
});
const { upload_url, file_key } = await urlResponse.json();

// Step 2: Upload video directly to S3
const uploadResponse = await fetch(upload_url, {
  method: 'PUT',
  headers: { 'Content-Type': 'video/webm' },
  body: recordedVideoBlob
});

if (!uploadResponse.ok) {
  throw new Error('Upload failed');
}

// Step 3: Trigger analysis
const analysisResponse = await fetch('http://localhost:8000/api/v1/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ file_key })
});
const analysis = await analysisResponse.json();

// Step 4: Display results
console.log('Engagement:', analysis.facial_analysis.engagement);
console.log('Transcript:', analysis.transcript_analysis.full_text);
console.log('Coaching:', analysis.coaching_advice.tip);
```

---

## AWS Services Used

1. **S3**: Store uploaded video/audio files
2. **Rekognition**: Analyze facial emotions and engagement
3. **Transcribe**: Convert speech to text
4. **DeepSeek LLM**: Generate personalized coaching advice

---

## Notes

- Upload URLs expire after 1 hour
- Analysis can take 30-120 seconds depending on video length
- Rekognition and Transcribe jobs poll every 2 seconds (max 60 attempts = 2 minutes)
- In production, use SNS notifications instead of polling

---

## Testing

```bash
# Start the server
uv run uvicorn interview_prep_backend.main:app --reload

# Test health
curl http://localhost:8000/health

# Test upload URL generation
curl -X POST http://localhost:8000/api/v1/upload-url \
  -H "Content-Type: application/json" \
  -d '{"file_type": "video", "content_type": "video/webm"}'
```
