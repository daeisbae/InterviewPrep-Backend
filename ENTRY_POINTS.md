# 🎯 Entry Points Reference

Your project now supports multiple entry points for different deployment scenarios:

## 📁 **Project Structure**

```
interview-prep-backend/
├── app.py                          # ⭐ Root entry point (NEW)
├── api/
│   └── index.py                    # 🔷 Vercel serverless entry
├── src/
│   └── interview_prep_backend/
│       └── main.py                 # 📦 Main FastAPI app
├── Procfile                        # 🚂 Process definition
├── railway.json                    # 🚄 Railway config
├── vercel.json                     # ▲ Vercel config
└── requirements.txt                # 📋 Dependencies
```

---

## 🎯 **Which Entry Point for Which Platform?**

| Platform | Entry Point | Command |
|----------|-------------|---------|
| **Local Development** | `app.py` | `python app.py` |
| **Railway** | `app.py` | `uvicorn app:app --port $PORT` |
| **Render** | `app.py` | `uvicorn app:app --port $PORT` |
| **Heroku** | `app.py` | `uvicorn app:app --port $PORT` |
| **Vercel** | `api/index.py` | Auto-detected |
| **AWS EB** | `app.py` | Auto-detected |
| **Docker** | `main.py` | `uvicorn interview_prep_backend.main:app` |

---

## 📝 **Entry Point Details**

### 1. **`app.py`** (Root Entry) ⭐

**Purpose**: Standard entry point for most platforms

**Run locally**:
```bash
# Method 1: Direct execution
python app.py

# Method 2: Uvicorn
uvicorn app:app --reload

# Method 3: With workers
uvicorn app:app --workers 4
```

### 2. **`api/index.py`** (Vercel) 🔷

**Purpose**: Serverless entry point for Vercel

**Deploy**:
```bash
vercel deploy
```

### 3. **`main.py`** (Core) 📦

**Purpose**: Core FastAPI application

**Run**:
```bash
uvicorn interview_prep_backend.main:app --reload
```

---

## 🚀 **Quick Start**

### Local Development

```bash
# Easiest way
python app.py

# Or with auto-reload
uvicorn app:app --reload --port 8000
```

### Deploy to Railway

```bash
railway login
railway init
railway up
```

### Deploy to Vercel

```bash
vercel deploy
```

---

## ✅ **Summary**

You now have **3 entry points**:

1. **`app.py`** - Use for Railway, Render, Heroku, local dev ⭐
2. **`api/index.py`** - Use for Vercel (serverless)
3. **`main.py`** - Core app (imported by others)

**Most platforms use `app.py` - it's already configured!** 🚀
