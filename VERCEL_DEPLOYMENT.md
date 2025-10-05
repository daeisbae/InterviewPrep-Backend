# 🚀 Vercel Deployment Guide

## ⚠️ Important Considerations

### **Vercel Limitations for This Project**

Vercel is optimized for **serverless functions** which have some constraints:

| Feature | Vercel Free | Vercel Pro | Your App Needs |
|---------|-------------|------------|----------------|
| **Max Execution Time** | 10 seconds | 60 seconds | 60-120 seconds (Rekognition) |
| **Max Request Size** | 4.5 MB | 4.5 MB | Video files (10-100 MB) |
| **Max Response Size** | 4.5 MB | 4.5 MB | ~1 MB (OK) |
| **Concurrent Executions** | Limited | Higher | AWS handles this |

### 🚨 **Critical Issues**

1. **❌ Video Uploads** - Vercel has 4.5 MB limit, but videos are often 10-100 MB
2. **⚠️ Processing Time** - Rekognition takes 60-120s, Vercel Pro allows 60s max
3. **⚠️ Serverless Cold Starts** - First request can be slow

---

## ✅ **Recommended Approach**

### Option 1: **Hybrid Architecture** (Best)

Use Vercel for API + S3 direct upload:

```
Frontend (Vercel)
    ↓
1. Get presigned URL from API
    ↓
2. Upload video DIRECTLY to S3 (bypasses 4.5 MB limit)
    ↓
3. Trigger analysis via API with file_key
    ↓
4. Poll for results (or use webhooks)
```

### Option 2: **Use Vercel Edge Functions** (Limited)

Edge functions are faster but have same size limits.

### Option 3: **Deploy to AWS/Railway Instead** (Recommended)

For long-running video processing, consider:
- **AWS ECS/Fargate** - Best for AWS integration
- **Railway** - Easy deployment, no time limits
- **Render** - Free tier available
- **Fly.io** - Global edge deployment

---

## 📦 **Vercel Setup (If Proceeding)**

### 1. Install Dependencies

```bash
# Add Mangum (ASGI adapter for serverless)
uv add mangum
```

### 2. Project Structure

```
interview-prep-backend/
├── api/
│   └── index.py          # ✨ Vercel entry point
├── src/
│   └── interview_prep_backend/
│       ├── main.py
│       ├── config.py
│       └── routers/
├── vercel.json           # ✨ Vercel config
├── requirements.txt      # ✨ Python dependencies
└── .env
```

### 3. Configure Environment Variables

In Vercel dashboard:

```bash
# Required
DEEPSEEK_API_KEY=your_key_here
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-bucket-name
ENABLE_EXTERNAL_APIS=true

# Optional
ENVIRONMENT=production
DEEPSEEK_MODEL=deepseek-chat
```

### 4. Deploy

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel
```

---

## 🔧 **Modified API Flow for Vercel**

### Current Flow (Won't Work)
```
POST /analyze-interview
    ↓
Upload 50 MB video → ❌ FAILS (4.5 MB limit)
```

### Modified Flow (Will Work)
```
Step 1: GET /api/v1/upload-url
    ← Returns presigned S3 URL
    
Step 2: Client uploads DIRECTLY to S3
    → Bypasses Vercel size limit ✅
    
Step 3: POST /api/v1/analyze
    → Send file_key to API
    → Start background job
    ← Return job_id immediately
    
Step 4: GET /api/v1/status/{job_id}
    → Poll for results
    ← Return status/results when ready
```

---

## 📝 **Required Code Changes**

### Update `interview.py`

Split into multiple endpoints:

```python
# 1. Get upload URL
@router.get("/upload-url")
async def get_upload_url():
    return aws_providers.generate_presigned_upload_url()

# 2. Start analysis (non-blocking)
@router.post("/analyze")
async def start_analysis(request: AnalysisRequest):
    job_id = str(uuid.uuid4())
    # Store job in database/Redis
    await store_job(job_id, "pending", request.file_key)
    # Process in background or via queue
    return {"job_id": job_id, "status": "pending"}

# 3. Get results
@router.get("/status/{job_id}")
async def get_status(job_id: str):
    return await get_job_results(job_id)
```

### Use Background Workers

Since Vercel functions timeout, use:
- **AWS Lambda** for processing
- **AWS SQS** for job queue
- **Vercel Cron Jobs** for polling

---

## 🚀 **Alternative: Deploy to Railway**

Railway has no time limits and is easier for long-running tasks:

### 1. Create `railway.json`

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn interview_prep_backend.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

### 2. Deploy

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

**Benefits**:
- ✅ No 10-second timeout
- ✅ Handles large file uploads
- ✅ Persistent storage
- ✅ Built-in PostgreSQL/Redis
- ✅ $5/month free credits

---

## 📊 **Platform Comparison**

| Platform | Time Limit | Size Limit | Cost (Free) | Best For |
|----------|------------|------------|-------------|----------|
| **Vercel** | 10s (Free), 60s (Pro) | 4.5 MB | Good | Static sites, APIs |
| **Railway** | None | 100 MB | $5 credits/mo | Full-stack apps |
| **Render** | None | 100 MB | 750 hrs/mo | Web services |
| **AWS ECS** | None | Any | Pay-as-go | Production, scaling |
| **Fly.io** | None | Any | 3 VMs free | Global edge |

---

## ✅ **Recommendation**

### For This Project:

**Don't use Vercel** because:
- ❌ 4.5 MB upload limit kills video uploads
- ❌ 60s timeout too short for Rekognition (60-120s)
- ❌ Requires significant architecture changes

**Use Railway or Render instead**:
- ✅ Deploy in 5 minutes
- ✅ No code changes needed
- ✅ Works with current architecture
- ✅ Free tier available

---

## 🎯 **Quick Deploy to Railway**

```bash
# 1. Install CLI
npm i -g @railway/cli

# 2. Login
railway login

# 3. Initialize
railway init

# 4. Add environment variables
railway variables set DEEPSEEK_API_KEY=xxx
railway variables set AWS_ACCESS_KEY_ID=xxx
railway variables set AWS_SECRET_ACCESS_KEY=xxx
railway variables set AWS_REGION=us-east-1
railway variables set AWS_S3_BUCKET=your-bucket
railway variables set ENABLE_EXTERNAL_APIS=true

# 5. Deploy
railway up

# 6. Get URL
railway domain
```

**Done!** Your API is live at `https://your-app.railway.app` 🚀

---

## 📚 **If You Still Want Vercel**

You'll need to:

1. ✅ Implement presigned URL flow (client uploads directly to S3)
2. ✅ Add job queue system (AWS SQS or Redis)
3. ✅ Split processing into separate Lambda functions
4. ✅ Use polling or webhooks for results
5. ✅ Add database for job tracking (Vercel Postgres/Redis)

This requires **significant refactoring** (~4-6 hours of work).

---

## 💡 **Summary**

| Deployment Option | Setup Time | Code Changes | Works Now |
|-------------------|------------|--------------|-----------|
| **Railway** | 5 minutes | None | ✅ Yes |
| **Render** | 10 minutes | None | ✅ Yes |
| **Fly.io** | 10 minutes | Minimal | ✅ Yes |
| **Vercel** | 4-6 hours | Major refactor | ⚠️ Partial |
| **AWS ECS** | 30-60 minutes | None | ✅ Yes |

**Recommendation**: Deploy to **Railway** for easiest setup with no limitations! 🚀
