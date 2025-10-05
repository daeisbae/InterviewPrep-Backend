# 🎯 Interview Prep Backend - Simple API Guide

## **Single Endpoint - Automatic Analysis**

Upload your interview video/audio and get instant AI-powered feedback!

---

## 📋 API Endpoint

### `POST /api/v1/analyze-interview`

**One endpoint does everything:**
1. ✅ Receives video/audio from client
2. ✅ Uploads to S3 automatically
3. ✅ Triggers AWS Rekognition (facial analysis)
4. ✅ Triggers AWS Transcribe (speech-to-text)
5. ✅ Analyzes filler words & mumbling
6. ✅ Calls AI for personalized coaching
7. ✅ Returns complete analysis

---

## 🚀 Frontend Usage

### JavaScript/React Example

```javascript
async function analyzeInterview(videoBlob) {
  const formData = new FormData();
  formData.append('file', videoBlob, 'interview.webm');
  
  try {
    const response = await fetch('http://localhost:8000/api/v1/analyze-interview', {
      method: 'POST',
      body: formData
    });
    
    const results = await response.json();
    console.log('Analysis:', results);
    
    // Display results
    displayResults(results);
    
  } catch (error) {
    console.error('Error:', error);
  }
}
```

### With MediaRecorder

```javascript
let mediaRecorder;
let chunks = [];

// Start recording
async function startRecording() {
  const stream = await navigator.mediaDevices.getUserMedia({
    video: true,
    audio: true
  });
  
  mediaRecorder = new MediaRecorder(stream);
  
  mediaRecorder.ondataavailable = (e) => {
    if (e.data.size > 0) chunks.push(e.data);
  };
  
  mediaRecorder.onstop = async () => {
    const blob = new Blob(chunks, { type: 'video/webm' });
    await analyzeInterview(blob);
    chunks = [];
  };
  
  mediaRecorder.start();
}

// Stop recording & auto-analyze
function stopRecording() {
  mediaRecorder.stop();
}
```

---

## 📥 Request Format

**Method:** `POST`  
**Content-Type:** `multipart/form-data`  
**Body:** FormData with file upload

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | Video or audio file (webm, mp4, wav, mp3, etc.) |

---

## 📤 Response Format

```json
{
  "file_key": "interviews/abc123-xyz.webm",
  "status": "completed",
  "processing_time_ms": 15234.56,
  
  "facial_analysis": {
    "engagement": 0.78,
    "positivity": 0.85,
    "anxiety_hint": 0.32
  },
  
  "transcript_analysis": {
    "full_text": "Hello, I'm very excited to be here...",
    "filler_ratio": 0.08,
    "filler_hits": 6,
    "mumble_score": 0.21,
    "segments": [
      {
        "text": "Hello",
        "start_time": 0.0,
        "end_time": 0.5,
        "confidence": 0.98
      }
    ]
  },
  
  "coaching_advice": {
    "tip": "Great energy! Try pausing instead of saying 'um' and 'uh'.",
    "confidence_score": 0.89,
    "anxiety_score": 0.32,
    "recommendations": [
      "Reduce filler words by 50%",
      "Maintain excellent eye contact",
      "Keep up the clear articulation"
    ]
  }
}
```

---

## 🔧 Setup Requirements

### Environment Variables

```bash
# Required
ENABLE_EXTERNAL_APIS=true
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
DEEPSEEK_API_KEY=your_deepseek_api_key

# Optional
ENVIRONMENT=development
```

### Install Dependencies

```bash
uv add boto3 httpx
```

---

## 🧪 Testing

### cURL Example

```bash
curl -X POST http://localhost:8000/api/v1/analyze-interview \
  -F "file=@interview.webm" \
  | jq .
```

### Python Example

```python
import requests

with open('interview.webm', 'rb') as f:
    files = {'file': ('interview.webm', f, 'video/webm')}
    response = requests.post(
        'http://localhost:8000/api/v1/analyze-interview',
        files=files
    )
    
print(response.json())
```

---

## ⚡ How It Works

```
Client                           Server
  |                                |
  |--POST /analyze-interview-----> |
  |   (multipart/form-data)        |
  |                                |
  |                                |--1. Upload to S3
  |                                |
  |                                |--2. Start Rekognition
  |                                |    (facial analysis)
  |                                |
  |                                |--3. Start Transcribe
  |                                |    (speech-to-text)
  |                                |
  |                                |--4. Analyze transcript
  |                                |    (filler words, clarity)
  |                                |
  |                                |--5. Call DeepSeek LLM
  |                                |    (coaching advice)
  |                                |
  |<-----Complete Analysis---------|
```

---

## 🎯 Response Fields Explained

### Facial Analysis
- **engagement** (0-1): How focused and engaged you appear
- **positivity** (0-1): Positive emotional expressions
- **anxiety_hint** (0-1): Signs of nervousness or anxiety

### Transcript Analysis
- **full_text**: Complete transcript of your speech
- **filler_ratio**: Percentage of filler words (um, uh, like)
- **filler_hits**: Total count of filler words
- **mumble_score** (0-1): Speech clarity (lower is better)
- **segments**: Timestamped transcript pieces

### Coaching Advice
- **tip**: AI-generated personalized coaching tip
- **confidence_score** (0-1): Overall confidence assessment
- **anxiety_score** (0-1): Anxiety level detected
- **recommendations**: List of specific improvement suggestions

---

## ❌ Error Handling

```javascript
try {
  const response = await fetch('/api/v1/analyze-interview', {
    method: 'POST',
    body: formData
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  
  const results = await response.json();
  
} catch (error) {
  if (error.message.includes('External APIs are disabled')) {
    alert('Server not configured. Contact support.');
  } else if (error.message.includes('Invalid file type')) {
    alert('Please upload a video or audio file.');
  } else if (error.message.includes('S3 upload failed')) {
    alert('Upload failed. Try again.');
  } else {
    alert(`Error: ${error.message}`);
  }
}
```

---

## 📊 System Endpoints

### Health Check
```bash
GET /health

Response:
{
  "status": "ok",
  "environment": "development"
}
```

### Configuration
```bash
GET /config

Response:
{
  "environment": "development",
  "enable_external_apis": true,
  "aws_region": "us-east-1"
}
```

---

## 🎨 Example UI Integration

```javascript
// components/InterviewRecorder.jsx
function InterviewRecorder() {
  const [recording, setRecording] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState(null);
  
  const handleStop = async (blob) => {
    setAnalyzing(true);
    
    const formData = new FormData();
    formData.append('file', blob, 'interview.webm');
    
    try {
      const response = await fetch('/api/v1/analyze-interview', {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      setResults(data);
    } catch (error) {
      alert('Analysis failed: ' + error.message);
    } finally {
      setAnalyzing(false);
    }
  };
  
  return (
    <div>
      {analyzing && <Spinner text="Analyzing your interview..." />}
      {results && <ResultsDisplay data={results} />}
    </div>
  );
}
```

---

## 🔥 Why This Approach?

### Advantages
✅ **Simple** - One endpoint, one call  
✅ **Automatic** - No manual S3 upload logic in frontend  
✅ **Secure** - No S3 credentials exposed to client  
✅ **Reliable** - Server handles retries and errors  
✅ **Fast** - Parallel processing (Rekognition + Transcribe)  
✅ **Complete** - Get all results in one response  

### vs Multi-Step Approach
❌ Multiple API calls required  
❌ Frontend manages S3 uploads  
❌ Complex error handling  
❌ More points of failure  
❌ Credentials management  

---

## 🚀 Start the Server

```bash
uv run uvicorn interview_prep_backend.main:app --reload --host 0.0.0.0 --port 8000
```

Visit: `http://localhost:8000/docs` for interactive API documentation!

---

## 📞 Need Help?

- API Docs: `http://localhost:8000/docs`
- Health Check: `GET /health`
- Config Check: `GET /config`
