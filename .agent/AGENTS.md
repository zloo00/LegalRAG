---
description: Legally AI Agent — Roles, Workflows, and behaviours
---

# Legally — Agent File

This file documents how the AI features in the Legally platform are structured.
It is meant for developers who need to understand or extend the AI workflows.

---

## Overview

The Legally platform contains two distinct AI agents:

| Agent | Trigger | Technology |
|---|---|---|
| **RAG Chat Agent** | User sends a message in the Chat tab | LangChain + Pinecone + Groq |
| **Contract Analysis Agent** | User uploads a PDF document | LangChain + Groq (streaming) |

Both agents are served by the **Python FastAPI AI Engine** (`api.py`).

---

## Agent 1 — RAG Chat Agent

### Purpose
Answer legal questions using citations from the indexed Kazakhstani legal corpus.

### Trigger
`POST /api/chat` (Go backend) → internally calls `POST /api/v1/internal-chat` (Python engine)

### Pipeline
```
User Question
     │
     ▼
[1] Hybrid Retrieval
     ├── BM25 (lexical) — returns top-10 keyword matches
     └── Pinecone (semantic) — returns top-10 vector matches
     │
     ▼
[2] Reranker  (BAAI/bge-reranker-v2-m3)
     └── Re-scores and filters down to top-5 most relevant chunks
     │
     ▼
[3] Prompt Assembly
     └── Injects top-5 chunks + conversation history into the prompt
     │
     ▼
[4] LLM Generation  (Groq llama-3.3-70b-versatile)
     └── Generates a legal answer with article citations
     │
     ▼
[5] Response
     └── Returns answer + source_documents (for citations in UI)
```

### Key File
`rag_chain.py` — function `invoke_qa(query, history)`

### Configuration
```python
# In rag_chain.py
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"  # 560M multilingual model
LLM_MODEL       = "llama-3.3-70b-versatile"          # via Groq
RERANKER        = "BAAI/bge-reranker-v2-m3"
TOP_K_RETRIEVE  = 10  # per retriever
TOP_K_RERANK    = 5   # after reranking
```

### System Prompt Design
The RAG agent uses a strict legal assistant prompt:
- Responds **only** in the language of the user's question (Russian/Kazakh/English)
- Always cites the article and law name for every factual claim
- Refuses to speculate — if context is insufficient, says "I don't have data on this"
- Never provides financial or personal legal advice — recommends consulting a lawyer

---

## Agent 2 — Contract Analysis Agent

### Purpose
Analyse uploaded PDF contracts for legal risks, clause compliance, and document type classification.

### Trigger
`POST /api/analyze` (Go backend, multipart PDF upload) → analysis service forwards text to `POST /api/v1/analyze`

### Pipeline
```
PDF Upload
     │
     ▼
[1] Text Extraction  (Go backend — analysis_service.go)
     └── Reads raw text from the uploaded PDF
     │
     ▼
[2] Document Classification
     └── LLM determines document type (Lease, Employment, Purchase, etc.)
     │
     ▼
[3] Multi-Part Analysis
     ├── Risk Assessment  (High / Medium / Low per clause)
     ├── Legal Compliance Check  (RK law references)
     ├── Missing Clauses Detection
     └── Document Summary
     │
     ▼
[4] Structured Response
     └── JSON with sections: analysis, document_type, timestamp, filename
     │
     ▼
[5] Persistence
     └── Saved to MongoDB for history access
```

### Key Files
- `backend/legally/services/analysis_service.go` — orchestrates the full flow
- `api.py`, endpoint `POST /api/v1/analyze` — runs the LLM analysis

---

## HITL (Human-In-The-Loop) Evaluation Workflow

Legally includes a full HITL system for evaluating RAG quality.

### Roles
| Role | Dashboard | Responsibilities |
|---|---|---|
| `admin` | `/admin/eval` | Create tasks, assign to reviewers, export results |
| `professor` | `/reviewer/eval` | Rate AI answers, provide written feedback |
| `student` | `/reviewer/eval` | Rate AI answers (limited set) |

### Workflow
```
Admin creates evaluation task (question + AI answer)
          │
          ▼
Admin assigns task to professor or student
          │
          ▼
Reviewer opens task → reads question + AI answer → submits rating (1–5) + comments
          │
          ▼
Admin exports results (CSV) for analysis
```

### API Routes
```
GET  /api/admin/tasks          → list all tasks
POST /api/admin/tasks          → create task
POST /api/admin/tasks/assign   → assign to reviewer
GET  /api/eval/my-tasks        → reviewer sees their assigned tasks
POST /api/eval/submit          → reviewer submits rating
GET  /api/admin/eval/export    → admin exports results
```

---

## Adding New Legal Documents to the Corpus

1. Add the new law as a `.txt` or `.pdf` file to the `/data/laws/` directory.
2. Re-run the vector indexing script:
   ```bash
   python build_vector_db.py
   ```
3. Confirm in Pinecone console that new vectors were added.
4. Restart the AI Engine (`uvicorn api:app --reload --port 8000`).

---

## Extending the RAG Agent

To change the LLM, retriever, or reranker:

1. Open `rag_chain.py`
2. Locate the relevant initialisation block
3. Replace the model name or class
4. Re-run `verify_langchain.py` to confirm everything loads:
   ```bash
   python verify_langchain.py
   ```

---

## Environment Variables Reference (AI Engine)

| Variable | Required | Default | Description |
|---|---|---|---|
| `PINECONE_API_KEY` | ✅ | — | Pinecone authentication |
| `PINECONE_INDEX_NAME` | ✅ | `legally-index` | Name of the vector index |
| `GROQ_API_KEY` | ✅ | — | Groq LLM authentication |
| `LEGAL_RAG_LLM` | ⬜ | `llama-3.3-70b-versatile` | LLM model name |
| `LEGAL_RAG_LLM_MAX_TOKENS` | ⬜ | `2048` | Max response tokens |
| `LEGAL_RAG_HF_LOCAL_ONLY` | ⬜ | `0` | Use cached HF model only |
| `LEGAL_RAG_HF_CACHE_DIR` | ⬜ | default HF cache | Custom HF model cache path |
