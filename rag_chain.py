# rag_chain.py — Pinecone + BM25, reranker, строгий промпт

import pickle
import os
from typing import Any, List

import config
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever


class PrefixedEmbeddings:
    def __init__(self, embeddings):
        self.embeddings = embeddings

    def embed_documents(self, texts):
        return self.embeddings.embed_documents(["passage: " + t for t in texts])

    def embed_query(self, text):
        return self.embeddings.embed_query("query: " + text)


embeddings = PrefixedEmbeddings(HuggingFaceEmbeddings(
    model_name=config.EMBEDDING_MODEL,
    encode_kwargs={"normalize_embeddings": True}
))

vector_store = PineconeVectorStore(
    index_name=config.PINECONE_INDEX_NAME,
    embedding=embeddings,
    namespace=config.PINECONE_NAMESPACE or "default",
)
print(f"Pinecone подключён: {config.PINECONE_INDEX_NAME}")

_hybrid_k = getattr(config, "HYBRID_K", 8)
_vector_kwargs = {"k": _hybrid_k}

# Расширенный фильтр по кодексу: ловит все варианты названия (УК РК, Қылмыстық кодекс и т.д.)
_filter_code = getattr(config, "RETRIEVER_FILTER_CODE_RU", None)
_uk_variants = [
    "Уголовный кодекс РК",
    "Уголовный кодекс Республики Казахстан",
    "Қылмыстық кодекс",
    "УК РК",
]
_allowed_code_ru_for_filter = None
if _filter_code:
    # Pinecone не поддерживает $regex — используем $or по известным вариантам
    _variants = list(dict.fromkeys([_filter_code] + [v for v in _uk_variants if v != _filter_code]))
    _allowed_code_ru_for_filter = _variants
    _vector_kwargs["filter"] = {"$or": [{"code_ru": v} for v in _variants]}
    _vector_kwargs["k"] = min(getattr(config, "HYBRID_K", 8) + 4, 15)  # k=12 при HYBRID_K=8 — больше шансов вытащить ст. 136
    print(f"Фильтр Pinecone: $or по code_ru = {_variants}")
_vector_retriever = vector_store.as_retriever(search_kwargs=_vector_kwargs)


class _FilterByCodeRetriever(BaseRetriever):
    """Оставляет только документы с code_ru из разрешённого списка (убирает шум от BM25)."""
    retriever: Any
    allowed_code_ru: List[str]

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun | None = None
    ) -> List[Document]:
        docs = self.retriever.invoke(query)
        allowed = set(self.allowed_code_ru)
        filtered = [d for d in docs if (d.metadata.get("code_ru") or "").strip() in allowed]
        return filtered if filtered else docs[:5]  # fallback: хоть что-то вернуть


base_retriever = _vector_retriever

# Чанки для BM25 (из pickle или prepare_data)
_chunks = None
_pkl = getattr(config, "CHUNKS_PICKLE_PATH", None) or (config.BASE_DIR / "chunks_for_bm25.pkl")
if _pkl and _pkl.exists():
    try:
        with open(_pkl, "rb") as f:
            _chunks = pickle.load(f)
        if _chunks:
            print(f"Чанки для BM25: {len(_chunks)} из {_pkl.name}")
    except Exception as e:
        print(f"Не удалось загрузить {_pkl.name}: {e}")
if _chunks is None and config.DOCUMENTS_DIR.exists():
    try:
        import prepare_data
        _chunks = getattr(prepare_data, "chunks", None)
        if _chunks:
            print(f"Чанки для BM25 из prepare_data: {len(_chunks)}")
    except Exception as e:
        print(f"prepare_data не загружен: {e}")

# BM25 + EnsembleRetriever (критично для ст. 136 УК и каз. терминов: баланы ауыстыру и т.д.)
try:
    from langchain_community.retrievers import BM25Retriever
    try:
        from langchain_classic.retrievers import EnsembleRetriever
    except ImportError:
        from langchain.retrievers.ensemble import EnsembleRetriever

    if not _chunks:
        raise ValueError("Нет чанков. Запустите: python build_vector_db.py")
    bm25_retriever = BM25Retriever.from_documents(_chunks, k=_hybrid_k)
    hybrid_retriever = EnsembleRetriever(
        retrievers=[_vector_retriever, bm25_retriever],
        weights=[getattr(config, "VECTOR_WEIGHT", 0.75), getattr(config, "BM25_WEIGHT", 0.25)],
    )
    base_retriever = hybrid_retriever
    print("Гибридный RAG готов! (BM25 + Pinecone, k=%d)" % _hybrid_k)
except ImportError as e:
    print(f"Ошибка импорта BM25/Ensemble: {e}")
    print("Установите: pip install langchain-community rank_bm25 (и langchain или langchain-classic)")
except Exception as e:
    print(f"BM25 не запустился: {e}. Используется только Pinecone.")

if _allowed_code_ru_for_filter:
    base_retriever = _FilterByCodeRetriever(retriever=base_retriever, allowed_code_ru=_allowed_code_ru_for_filter)
    print("Включён пост-фильтр по кодексу (только разрешённые code_ru).")

retriever = base_retriever
if config.USE_RERANKER:
    try:
        try:
            from langchain_community.retrievers import ContextualCompressionRetriever
        except ImportError:
            from langchain_classic.retrievers.contextual_compression import ContextualCompressionRetriever
        from langchain_community.document_compressors import FlashrankRerank
        compressor = None
        for model_name in (config.FLASHRANK_MODEL, "ms-marco-TinyBERT-L-2-v2", None):
            try:
                compressor = FlashrankRerank(model=model_name, top_n=config.RETRIEVER_TOP_K_AFTER_RERANK)
                break
            except Exception:
                continue
        if compressor is not None:
            retriever = ContextualCompressionRetriever(base_compressor=compressor, base_retriever=base_retriever)
            print("Reranker FlashRank включён.")
    except Exception as e:
        print("FlashRank отключён:", e)

# Выбор LLM: локальная Ollama или облачный Groq (\"облачный оллама\")
_llm_backend = os.environ.get("LEGAL_RAG_LLM_BACKEND", "ollama").lower()
if _llm_backend == "groq":
    try:
        from langchain_groq import ChatGroq  # type: ignore[import]
    except Exception as e:  # pragma: no cover
        raise SystemExit(
            "Для использования облачного Groq установите пакет 'langchain-groq':\n"
            "  pip install langchain-groq\n"
            f"Текущая ошибка импорта: {e}"
        )

    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        raise SystemExit("Задайте GROQ_API_KEY для облачного Groq (gsk_...): export GROQ_API_KEY=...")

    llm = ChatGroq(
        groq_api_key=groq_api_key,
        model_name=config.LLM_MODEL,  # например: llama-3.1-70b-versatile
        temperature=config.LLM_TEMPERATURE,
    )
    print(f"LLM: Groq (model={config.LLM_MODEL})")
else:
    from langchain_ollama import OllamaLLM

    llm = OllamaLLM(
        model=config.LLM_MODEL,
        temperature=config.LLM_TEMPERATURE,
        base_url=config.OLLAMA_BASE_URL,
    )
    print(f"LLM: Ollama локально (model={config.LLM_MODEL})")

prompt_template = """Ты — точный юридический ассистент по законам РК.
ОТВЕЧАЙ ИСКЛЮЧИТЕЛЬНО ТЕКСТОМ ИЗ КОНТЕКСТА НИЖЕ.
НИКОГДА НЕ ПРИДУМЫВАЙ номера статей, названия, пункты, даты или выводы, которых нет в контексте.
Если в контексте нет ответа — отвечай ровно одной строкой: "Информация не найдена в доступных текстах законов."
Если вопрос на казахском — отвечай только на казахском, используя точные формулировки НҚА.
Для уголовных дел всегда проверяй УК РК и указывай точную статью и санкцию.
Если статья содержит список принципов — перечисляй ВСЕ пункты дословно, не сокращай.
Начинай с: "Это не официальная юридическая консультация. Информация только из базы."

Контекст:
{context}

Вопрос: {question}

Ответ (цитируй статьи дословно, указывай номер статьи и источник):"""

PROMPT = PromptTemplate.from_template(prompt_template)

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True,
    chain_type_kwargs={"prompt": PROMPT},
)

if __name__ == "__main__":
    question = "Статья 136 УК РК баланы ауыстыру"
    print(f"\nВопрос: {question}\n")
    docs = retriever.invoke(question)
    for i, doc in enumerate(docs[:5], 1):
        print(f"{i}. {doc.metadata.get('source')} | {doc.metadata.get('code_ru', '')} ст.{doc.metadata.get('article_number', '')}")
        print(f"   {doc.page_content[:250].replace(chr(10), ' ')}...\n")
    result = qa_chain.invoke({"query": question})
    print("Ответ:", result["result"][:500])
