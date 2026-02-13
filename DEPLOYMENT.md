## Deployment Guide: Render.com

This guide describes a production-style deployment for the LegalRAG Streamlit app on Render.
It assumes you already have:
- a Git repository with this project,
- a Pinecone index created and populated,
- a Groq (or other LLM) API key,
- optional Hugging Face model cache prepared if you want offline/local-only embeddings.

Notes:
- Render uses ephemeral disks. Do not rely on local files for persistent storage.
- The app reads from Pinecone at runtime; embeddings are only used for query encoding.
- If Hugging Face downloads are blocked or slow, use a cached model and enable local-only mode.

--------------------------------------------------------------------------------
## 1) Prepare the repository

1.1. Ensure `requirements.txt` is complete
Render installs dependencies from `requirements.txt`. If you add new packages, update it.

1.2. Add a start command for Streamlit
Render "Web Service" start command:

    streamlit run app.py --server.port $PORT --server.address 0.0.0.0

1.3. Optional: add a `render.yaml` (Blueprint)
You can deploy via the UI or a Blueprint. If you want a Blueprint, create `render.yaml`:

    services:
      - type: web
        name: legalrag-streamlit
        env: python
        plan: starter
        buildCommand: pip install -r requirements.txt
        startCommand: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
        autoDeploy: true
        envVars:
          - key: PINECONE_API_KEY
            sync: false
          - key: PINECONE_INDEX_NAME
            value: legal-rag
          - key: PINECONE_NAMESPACE
            value: legal_kz
          - key: LEGAL_RAG_LLM
            value: llama-3.3-70b-versatile
          - key: LEGAL_RAG_LLM_MAX_TOKENS
            value: "2048"
          - key: LEGAL_RAG_HF_READ_TIMEOUT_SEC
            value: "60"

--------------------------------------------------------------------------------
## 2) Create the Render Web Service

2.1. In Render Dashboard:
- New + -> Web Service
- Connect your Git repo
- Select the branch to deploy

2.2. Configure the service:
- Environment: Python
- Region: closest to your users
- Build Command: `pip install -r requirements.txt`
- Start Command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

2.3. Set environment variables (see section 3)

2.4. Create service and wait for the first deploy

--------------------------------------------------------------------------------
## 3) Required environment variables

These are mandatory for core functionality:
- `PINECONE_API_KEY`
- `PINECONE_INDEX_NAME` (default: `legal-rag`)
- `PINECONE_NAMESPACE` (default: `legal_kz`)
- `LEGAL_RAG_LLM` (default: `llama-3.3-70b-versatile`)

If using Groq, add:
- `GROQ_API_KEY`

If using another provider, set the relevant API key expected by your LLM integration.

Optional for embeddings and Hugging Face:
- `LEGAL_RAG_HF_READ_TIMEOUT_SEC` (default: 60)
- `LEGAL_RAG_HF_CONNECT_TIMEOUT_SEC` (default: 10)
- `LEGAL_RAG_HF_CACHE_DIR` (if you mount a disk or custom cache path)
- `LEGAL_RAG_HF_LOCAL_ONLY` (set to `1` if you preloaded the model)
- `LEGAL_RAG_HF_OFFLINE` (set to `1` to force HF offline)

--------------------------------------------------------------------------------
## 4) Pinecone prerequisites

4.1. Create and populate the index locally:
You must run the indexing pipeline on a machine with access to the documents:

    export PINECONE_API_KEY="..."
    python build_vector_db.py

4.2. Verify that the index exists and is non-empty:
- In Pinecone console, ensure the index has vectors.

Render does NOT build the index during deploy.

--------------------------------------------------------------------------------
## 5) Embeddings strategy on Render

Option A: Online HF download at runtime
- Simplest, but can fail if HF is slow or blocked.
- Set:
  - `LEGAL_RAG_HF_READ_TIMEOUT_SEC=120`

Option B: Pre-cache the model and use local-only
- Download on your local machine once to cache:

    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/multilingual-e5-large')"

- Upload the cache to a storage solution (Render disk or external bucket).
- Set env vars:
  - `LEGAL_RAG_HF_LOCAL_ONLY=1`
  - `LEGAL_RAG_HF_CACHE_DIR=/path/to/cache`

If you do not provide a cache and enable local-only, the app will fail at startup.

--------------------------------------------------------------------------------
## 6) Streamlit configuration

If you need custom Streamlit settings, add a `.streamlit/config.toml`:

    [server]
    headless = true
    enableCORS = false
    enableXsrfProtection = false

Use this only if you understand the security implications.

--------------------------------------------------------------------------------
## 7) Health checks and logging

- Render shows logs in the dashboard.
- Streamlit logs are printed to stdout/stderr.
- Verify boot sequence:
  - Pinecone connects
  - Embeddings load
  - App starts and listens on `$PORT`

--------------------------------------------------------------------------------
## 8) Common failure modes

8.1. "ReadTimeoutError" from Hugging Face
- Increase `LEGAL_RAG_HF_READ_TIMEOUT_SEC`
- Or use local-only with a cached model

8.2. "Pinecone API key missing"
- Ensure `PINECONE_API_KEY` is set in Render env vars

8.3. "ImportError: invoke_qa not found"
- Ensure `rag_chain.py` exports `invoke_qa`
- Verify no syntax errors during deploy

8.4. "Event loop is closed" during stop
- Usually a shutdown artifact after Ctrl+C. Not a deployment issue.

--------------------------------------------------------------------------------
## 9) Production checklist

- Pinecone index built and current
- Environment variables set
- HF model access strategy chosen
- App starts locally with same env vars
- Render service uses the correct start command

--------------------------------------------------------------------------------
## 10) Rollback and redeploy

- Render supports manual redeploy from the dashboard.
- If a bad commit is deployed, use "Rollback" to a previous deploy.
