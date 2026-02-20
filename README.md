# ⚖️ Legally — AI-Powered Legal Assistant for Kazakhstan

> **Legally** is a full-stack Retrieval-Augmented Generation (RAG) platform for the laws of the Republic of Kazakhstan. It lets legal professionals and citizens analyse PDF contracts, ask legal questions, and receive AI responses grounded in real Kazakhstani legislation — with citations.

---

## 🏗 System Architecture

Legally is a **three-tier platform**, each tier owned by a dedicated technology:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Browser / React UI                           │
│           http://localhost:3000                                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │  REST (JSON)
┌───────────────────────────▼─────────────────────────────────────┐
│              Go / Gin Backend  (Orchestrator)                   │
│           http://localhost:8080                                  │
│  • Auth (JWT)  • Sessions  • MongoDB  • Analysis orchestration  │
└──────────────────────┬──────────────────────────────────────────┘
                       │  Internal REST
┌──────────────────────▼──────────────────────────────────────────┐
│           Python / FastAPI  (AI Engine)                         │
│           http://localhost:8000                                  │
│  • LangChain RAG  • Pinecone vector search  • Groq LLM          │
│  • BAAI/bge reranker  • BM25 hybrid retrieval                   │
└─────────────────────────────────────────────────────────────────┘
```

| Layer | Tech Stack | Port |
|---|---|---|
| **Frontend** | React 18, Material-UI, React Router | 3000 |
| **Backend** | Go 1.20+, Gin, MongoDB | 8080 |
| **AI Engine** | Python 3.10+, FastAPI, LangChain, Pinecone, Groq | 8000 |

---

## 📋 Prerequisites

Install the following before running the project:

| Tool | Minimum Version | Check command |
|---|---|---|
| Python | 3.10+ | `python --version` |
| Go | 1.20+ | `go version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |
| MongoDB | 5.0+ (local or Atlas) | `mongod --version` |

**External Services:**
- [Pinecone](https://pinecone.io) — vector index for semantic search
- [Groq](https://console.groq.com) — hosted LLM (`llama-3.3-70b-versatile`)

---

## ⚙️ Configuration

Create a `.env` file in the **project root** directory:

```env
# ── AI & Vector Store ─────────────────────────────────────────
PINECONE_API_KEY="your_pinecone_api_key"
PINECONE_INDEX_NAME="legally-index"

GROQ_API_KEY="your_groq_api_key"

# ── Database ──────────────────────────────────────────────────
MONGO_URI="mongodb://localhost:27017"
DB_NAME="legally_bot"

# ── Access Management ─────────────────────────────────────────
# JWT secret for token signing (choose any long random string)
JWT_SECRET="your_super_secret_jwt_key"

# Comma-separated list of admin user IDs
ADMIN_IDS="991315506"
```

> ⚠️ **Never commit your `.env` file.** It is listed in `.gitignore`.

---

## 🚀 Quick Start — Step-by-Step

Run each service **in a separate terminal**, in this exact order.

---

### Step 1 — Build the Vector Database *(first time only)*

This indexes the Kazakhstani legal corpus into Pinecone.

```bash
# From the project root
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

python build_vector_db.py
```

**Expected output:**
```
[INFO] Connecting to Pinecone index: legally-index
[INFO] Loading documents from /data/laws/...
[INFO] Chunking 19 legal documents...
[INFO] Uploading 4,200 vectors to Pinecone...
[SUCCESS] Vector database ready. Total vectors: 4200
```

> ✅ Only needs to run once unless the legal corpus is updated.

---

### Step 2 — Launch the AI Engine (Python / FastAPI)

```bash
# From the project root, with venv active
uvicorn api:app --reload --port 8000
```

**✅ Healthy startup looks like this:**
```
INFO:     Will watch for changes in these directories: ['/path/to/LegalRAG']
INFO:     Loading embedding model: intfloat/multilingual-e5-large...
INFO:     Connecting to Pinecone index 'legally-index'...
INFO:     Pinecone connected. Index has 4200 vectors.
INFO:     BM25 retriever initialized with 19 documents.
INFO:     Reranker loaded: BAAI/bge-reranker-v2-m3
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**❌ Common errors:**
| Error | Fix |
|---|---|
| `PINECONE_API_KEY not set` | Check your `.env` file |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `ReadTimeoutError` (HuggingFace) | Check internet or increase timeout |

---

### Step 3 — Launch the Core Backend (Go / Gin)

```bash
cd backend/legally
go run main.go
```

**✅ Healthy startup looks like this:**
```
[GIN-debug] [WARNING] Creating an Engine instance with the Logger and Recovery middleware already attached.
[LEGALLY] Connecting to MongoDB at mongodb://localhost:27017...
[LEGALLY] ✅ MongoDB connected. Database: legally_bot
[LEGALLY] Registering routes...
[GIN-debug] GET    /health
[GIN-debug] POST   /api/register
[GIN-debug] POST   /api/login
[GIN-debug] POST   /api/analyze
[GIN-debug] POST   /api/chat
[GIN-debug] GET    /api/chat/history
[LEGALLY] ✅ Server is live at http://localhost:8080
```

**❌ Common errors:**
| Error | Fix |
|---|---|
| `connection refused` (MongoDB) | Start `mongod` or check `MONGO_URI` |
| `port already in use: 8080` | Kill the process: `lsof -i:8080` |
| `JWT_SECRET not set` | Add it to your `.env` |

---

### Step 4 — Launch the Frontend (React)

```bash
cd frontend/legally-app
npm install        # First time only
npm start
```

**✅ Healthy startup looks like this:**
```
Compiled successfully!

You can now view legally-app in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000

Note that the development build is not optimized.
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## ✅ Verifying the Full Stack

After all three services are running, verify the system health:

```bash
# 1. Check AI Engine
curl http://localhost:8000/docs
# → Should open Swagger UI at that URL

# 2. Check Go Backend health
curl http://localhost:8080/health
# → Expected: {"status":"healthy"}

# 3. Check Frontend
# Open http://localhost:3000 in browser
# → Should show the Legally login page
```

---

## 🔑 API Reference

### Public Endpoints (No Auth)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/register` | Register a new user |
| `POST` | `/api/login` | Login, returns JWT tokens |
| `POST` | `/api/refresh` | Refresh access token |
| `GET` | `/api/stats` | Get system stats (vector count, etc.) |
| `GET` | `/api/laws` | List indexed laws |
| `GET` | `/health` | Backend health check |

### Private Endpoints (JWT Required)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/analyze` | Upload & analyze a PDF contract |
| `GET` | `/api/history` | Get user's analysis history |
| `POST` | `/api/chat` | Send a chat message to the AI |
| `GET` | `/api/chat/history` | Retrieve current session chat |
| `DELETE` | `/api/chat/history` | Clear current session chat |
| `GET` | `/api/chat/export` | Export chat as text/PDF |
| `POST` | `/api/logout` | Invalidate session |

### Admin Endpoints (Admin Role Required)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/admin/users` | List all users |
| `POST` | `/api/admin/users/role` | Update user role |
| `GET` | `/api/admin/tasks` | List HITL evaluation tasks |
| `POST` | `/api/admin/tasks` | Create evaluation task |
| `POST` | `/api/admin/tasks/assign` | Assign task to reviewer |
| `GET` | `/api/admin/eval/export` | Export rated results |

### AI Engine Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/internal-chat` | Chat with RAG (called by Go backend) |
| `POST` | `/api/v1/analyze` | Analyse legal text (called by Go backend) |

---

## 📜 Key Modules

| File | Purpose |
|---|---|
| `rag_chain.py` | Core RAG pipeline — hybrid retrieval → rerank → LLM generation |
| `api.py` | FastAPI gateway exposing AI capabilities |
| `build_vector_db.py` | One-time script to index legal documents into Pinecone |
| `backend/legally/services/analysis_service.go` | Orchestrates PDF upload → AI analysis → MongoDB save |
| `backend/legally/api/routes.go` | All Go API route definitions |
| `frontend/legally-app/src/components/ChatSection.js` | Main chat interface |
| `frontend/legally-app/src/components/UploadSection.js` | PDF upload & analysis trigger |
| `frontend/legally-app/src/components/ResultSection.js` | Renders analysis results with risk indicators |

---

## 📚 Legal Corpus Coverage

Legally indexes **19 core laws** of the Republic of Kazakhstan:

- 🏛 Constitution of the Republic of Kazakhstan
- ⚖️ Civil Code (General & Special Parts)
- 🔒 Criminal Code
- 👷 Labour Code
- 💰 Tax Code
- 🏢 Administrative Code
- 📜 Laws on Procurement, Anti-Corruption, AI Regulation, and more

---

## 👥 User Roles

| Role | Access |
|---|---|
| `user` | Upload documents, use chat |
| `admin` | Full access + user management + HITL admin |
| `professor` | HITL evaluation tasks |
| `student` | HITL evaluation tasks (limited) |

---

## 📊 Development & Evaluation

```bash
# Benchmark retrieval quality
python benchmark.py

# Test retrieval pipeline manually
python test_retrieval.py

# Verify LangChain configuration
python verify_langchain.py
```

---

## 🩺 Troubleshooting Quick Reference

| Symptom | Likely Cause | Fix |
|---|---|---|
| Login page shows but login fails | Go backend not running | Check Step 3 |
| Chat returns empty response | AI Engine not running or Groq key missing | Check Step 2 |
| PDF upload hangs | AI Engine unreachable from Go backend | Both must be running |
| Images/logos not loading | Wrong `src/images` path | Assets are in `frontend/legally-app/src/images/` |
| `no-unused-vars` ESLint warning | Stale import | Remove unused import |
| `$dragactive` React warning | Missing `shouldForwardProp` | Already fixed in current version |
