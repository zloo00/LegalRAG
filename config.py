# config.py — настройки Legal RAG (локально, без облаков)

import os
from pathlib import Path

# Пути
BASE_DIR = Path(__file__).resolve().parent
DOCUMENTS_DIR = BASE_DIR / "documents"
CHROMA_DIR = BASE_DIR / "chroma_db"
BENCHMARK_DIR = BASE_DIR / "benchmark_results"

# Векторная база
COLLECTION_NAME = "legal_kz_2026"

# Эмбеддинги: multilingual-e5-large (SOTA для RU/KZ) или Jina v3
EMBEDDING_MODEL = os.environ.get("LEGAL_RAG_EMBEDDING", "intfloat/multilingual-e5-large")
# Альтернатива: "jinaai/jina-embeddings-v3" — требует API key

# LLM (Ollama локально)
OLLAMA_BASE_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
LLM_MODEL = os.environ.get("LEGAL_RAG_LLM", "llama3.1:8b")
LLM_TEMPERATURE = 0.0  # минимум креативности, максимум точности

# Retriever
RETRIEVER_TOP_K = 12          # сколько чанков достаём до rerank
RETRIEVER_TOP_K_AFTER_RERANK = 5  # сколько оставляем после rerank
BM25_WEIGHT = 0.4             # гибрид: BM25
VECTOR_WEIGHT = 0.6           # гибрид: семантика

# Reranker (FlashRank)
USE_RERANKER = os.environ.get("LEGAL_RAG_USE_RERANKER", "1") == "1"
FLASHRANK_MODEL = "ms-marco-MiniLM-L-6-v2"  # лёгкий; для качества: "rank-T5-flan"

# Graph RAG (связи статей: ст. X → ст. Y). Файл графа: article_ref_graph.json
USE_GRAPH_RAG = os.environ.get("LEGAL_RAG_USE_GRAPH", "0") == "1"
GRAPH_PATH = BASE_DIR / "article_ref_graph.json"
# Neo4j (опционально): задайте NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD для записи графа в Neo4j

# Бенчмарк
BENCHMARK_TIMEOUT_SEC = 300
BENCHMARK_QUESTIONS_MIN = 100

# Безопасность и AI-закон РК
DISCLAIMER_RU = (
    "Это не официальная юридическая консультация и не заменяет адвоката. "
    "Информация основана исключительно на текстах законов. "
    "Проверяйте актуальные редакции на adilet.zan.kz."
)
DISCLAIMER_KZ = (
    "Бұл ресми заңдық кеңес емес және адвокатты ауыстырмайды. "
    "Ақпарат тек заң мәтініне негізделген. "
    "Актуалды редакцияларды adilet.zan.kz сайтында тексеріңіз."
)
# Соответствие закону РК об ИИ: прозрачность ответов, без манипуляций
AI_LAW_COMPLIANCE_NOTE = (
    "Ответ сформирован автоматически на основе извлечённых статей; "
    "источники указаны для проверки (требования прозрачности)."
)
