# Legally — Intelligent Legal Assistant for Kazakhstan

**Legally** is a state-of-the-art Retrieval-Augmented Generation (RAG) platform tailored for the laws and regulations of the Republic of Kazakhstan. It provides legal professionals and citizens with an intuitive interface for legal research, chat-based consultations, and automated document analysis.

---

## 🏗 System Architecture

Legally operates using a modular, three-tier architecture for maximum scalability and performance:

1.  **AI Engine (Python/FastAPI):**
    - **RAG Core:** Powered by `rag_chain.py` using LangChain.
    - **Hybrid Retrieval:** Combined BM25 (lexical) and Pinecone (semantic) search.
    - **Reranking:** Integrated `BAAI/bge-reranker-v2-m3` for high-precision context filtering.
    - **LLM:** Groq-hosted `llama-3.3-70b-versatile` for rapid, high-quality legal reasoning.
    - **Service:** FastAPI (`api.py`) exposing high-performance REST endpoints.

2.  **Core Backend (Go/Gin):**
    - **Orchestration:** Manages user sessions, authentication, and analysis workflows.
    - **Data Persistence:** MongoDB for storing multi-part analysis reports and chat logs.
    - **Integration:** Securely bridges the frontend with the AI service.

3.  **Modern Frontend (React):**
    - **Interface:** Dynamic, responsive UI built for professional workflows.
    - **Capability:** Real-time chat, PDF upload for automated risk assessment, and document export (PDF/DOCX).

---

## 📋 Prerequisites

Required toolchain:
- **Python 3.10+** (with mandatory virtual environment)
- **Go 1.20+**
- **Node.js 18+** & **npm**
- **MongoDB** (Local or Atlas instance)
- **Pinecone** Index (for semantic vector search)
- **Groq API Key**

---

## ⚙️ Configuration

Populate your `.env` file in the root directory with the following keys:

```env
# AI & Vector Store
PINECONE_API_KEY="your_pinecone_key"
PINECONE_INDEX_NAME="legally-index"
GROQ_API_KEY="your_groq_key"

# Database & Infrastructure
MONGO_URI="your_mongodb_uri"
DB_NAME="legally_bot"

# Access Management
ADMIN_IDS="991315506"
```

---

## 🚀 Quick Start Guide

To launch the complete Legally ecosystem, follow these steps in sequential order:

### 1. Launch AI Service (Python)
```bash
# From the project root
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start the AI Gateway
uvicorn api:app --reload --port 8000
```

### 2. Launch Core Backend (Go)
```bash
cd backend/legally
go run main.go
# Operational on http://localhost:8080
```

### 3. Launch UI (React)
```bash
cd frontend/legally-app
npm install
npm start
# Accessible at http://localhost:3000
```

---

## 📜 Key Modules & Documents

### Core Components
- `rag_chain.py`: The "brain" — handles sophisticated retrieval-rerank-generation cycles.
- `api.py`: The interface — exposes AI capabilities via FastAPI.
- `backend/legally/services/analysis_service.go`: Orchestrator for deep document analysis.
- `frontend/legally-app/src/components/ChatSection.js`: Primary interaction layer.

### Coverage
Legally indexes 19 vital laws of Kazakhstan, providing precise citations from:
- **Constitution of RK**
- **Civil, Criminal, and Labor Codes**
- **Tax and Administrative Codes**
- **Specialized Laws** (Procurement, Corruption, AI, etc.)

---

## 📊 Evaluation & Development
Measure performance and retrieval quality:
```bash
python benchmark.py
python test_retrieval.py
```
