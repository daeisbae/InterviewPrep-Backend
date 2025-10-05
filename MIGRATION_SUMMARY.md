# API Migration Summary

## What Changed

### ❌ Removed (Session-based architecture)
- `POST /api/v1/sessions` - Create session endpoint
- `POST /api/v1/sessions/{session_id}/ingest` - Real-time signal ingestion
- Session store and state machine
- Browser signal payload processing

### ✅ Added (S3 + AWS Services architecture)

#### New Endpoints:
1. **`POST /api/v1/upload-url`** - Generate presigned S3 upload URL
2. **`POST /api/v1/analyze`** - Analyze uploaded video/audio

#### New AWS Integrations:
- **S3**: Direct file upload from frontend
- **Rekognition**: Facial emotion analysis
- **Transcribe**: Speech-to-text conversion
- **DeepSeek LLM**: Coaching advice generation

#### New Configuration:
- `AWS_S3_BUCKET` environment variable added

---

## Architecture Comparison

### Before (Session-based)
```
Frontend → POST /sessions → Create session ID
Frontend → POST /sessions/{id}/ingest → Send signals
Backend → Process in real-time → Return response
```

### After (S3 + AWS)
```
Frontend → POST /upload-url → Get presigned URL
Frontend → PUT to S3 → Upload video directly
Frontend → POST /analyze → Trigger AWS services
Backend → Rekognition + Transcribe + LLM → Return analysis
```

---

## Benefits

✅ **Scalable**: No session state to manage
✅ **Performant**: AWS services handle heavy processing
✅ **Cost-effective**: Pay only for AWS usage
✅ **Simple**: Frontend uploads directly to S3
✅ **Production-ready**: Uses AWS best practices

---

## Environment Setup

Add to your `.env`:
```bash
AWS_S3_BUCKET=your-interview-bucket
ENABLE_EXTERNAL_APIS=true
```

---

## Frontend Migration Guide

### Old Code (Remove):
```javascript
// Create session
const session = await fetch('/api/v1/sessions', { method: 'POST' });

// Send signals
await fetch(`/api/v1/sessions/${sessionId}/ingest`, {
  method: 'POST',
  body: JSON.stringify({ facial, voice, transcript })
});
```

### New Code (Use):
```javascript
// 1. Get upload URL
const { upload_url, file_key } = await fetch('/api/v1/upload-url', {
  method: 'POST',
  body: JSON.stringify({ file_type: 'video', content_type: 'video/webm' })
}).then(r => r.json());

// 2. Upload to S3
await fetch(upload_url, {
  method: 'PUT',
  headers: { 'Content-Type': 'video/webm' },
  body: videoBlob
});

// 3. Analyze
const analysis = await fetch('/api/v1/analyze', {
  method: 'POST',
  body: JSON.stringify({ file_key })
}).then(r => r.json());
```

---

## Files Modified

1. `schemas.py` - Added new request/response models
2. `config.py` - Added S3 bucket configuration
3. `aws_providers.py` - Added S3, Rekognition, Transcribe functions
4. `routers/interview.py` - Complete rewrite with new endpoints
5. `main.py` - Added `__main__` block for running

## Files You Can Delete (Optional)

- `services/session_store.py` - No longer needed
- `services/state_machine.py` - No longer needed
- `services/analytics.py` - Replaced by AWS services
- `data/rules.json` - No longer needed

---

## Testing

```bash
# Start server
uv run uvicorn interview_prep_backend.main:app --reload

# Test endpoints
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/upload-url \
  -H "Content-Type: application/json" \
  -d '{"file_type":"video"}'
```
