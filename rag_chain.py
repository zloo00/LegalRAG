# rag_chain.py — Pinecone + BM25, reranker, строгий промпт

import pickle
import os
from typing import Any

import config
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate


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

_hybrid_k = getattr(config, "HYBRID_K", 5)
_vector_retriever = vector_store.as_retriever(search_kwargs={"k": _hybrid_k})

base_retriever = _vector_retriever

# BM25: подключаем гибридный поиск (Pinecone + BM25), если есть чанки
BM25Retriever = None
EnsembleRetriever = None
try:
    from langchain_community.retrievers import BM25Retriever
except ImportError:
    pass

if BM25Retriever is not None:
    for _mod, _name in [
        ("langchain_classic.retrievers", "EnsembleRetriever"),
        ("langchain_classic.retrievers.ensemble", "EnsembleRetriever"),
        ("langchain.retrievers.ensemble", "EnsembleRetriever"),
        ("langchain.retrievers", "EnsembleRetriever"),
        ("langchain_community.retrievers", "EnsembleRetriever"),
    ]:
        try:
            import importlib
            _m = importlib.import_module(_mod)
            EnsembleRetriever = getattr(_m, _name, None)
            if EnsembleRetriever is not None:
                break
        except Exception:
            continue

_chunks = None
_pkl = getattr(config, "CHUNKS_PICKLE_PATH", None) or (config.BASE_DIR / "chunks_for_bm25.pkl")
if _pkl and _pkl.exists():
    try:
        with open(_pkl, "rb") as f:
            _chunks = pickle.load(f)
        if _chunks:
            print(f"Чанки для BM25 загружены: {len(_chunks)} из {_pkl.name}")
    except Exception as e:
        print(f"Не удалось загрузить {_pkl.name}: {e}")

if _chunks is None and config.DOCUMENTS_DIR.exists():
    try:
        import prepare_data
        _chunks = getattr(prepare_data, "chunks", None)
        if _chunks:
            print(f"Чанки для BM25 загружены из prepare_data: {len(_chunks)}")
    except Exception as e:
        print(f"prepare_data не загружен: {e}")

if _chunks and BM25Retriever is not None:
    try:
        bm25_retriever = BM25Retriever.from_documents(_chunks, k=_hybrid_k)
        if EnsembleRetriever is not None:
            base_retriever = EnsembleRetriever(
                retrievers=[_vector_retriever, bm25_retriever],
                weights=[config.VECTOR_WEIGHT, config.BM25_WEIGHT],
            )
            print("Гибридный RAG готов! (BM25 + Pinecone, k=%d)" % _hybrid_k)
        else:
            from langchain_core.retrievers import BaseRetriever

            class _HybridRetriever(BaseRetriever):
                """Гибрид RRF без EnsembleRetriever (аннотации для Pydantic v2)."""
                retriever_a: Any = _vector_retriever
                retriever_b: Any = bm25_retriever
                k: int = _hybrid_k
                c: int = 60

                def _get_relevant_documents(self, query: str, *, run_manager=None):
                    docs_a = self.retriever_a.invoke(query)
                    docs_b = self.retriever_b.invoke(query)
                    seen = {}
                    for rank, doc in enumerate(docs_a, 1):
                        key = (doc.page_content[:200], doc.metadata.get("source", ""))
                        seen[key] = seen.get(key, 0) + config.VECTOR_WEIGHT / (self.c + rank)
                    for rank, doc in enumerate(docs_b, 1):
                        key = (doc.page_content[:200], doc.metadata.get("source", ""))
                        seen[key] = seen.get(key, 0) + config.BM25_WEIGHT / (self.c + rank)
                    sorted_docs = sorted(seen.items(), key=lambda x: -x[1])
                    out = []
                    for (content_prefix, src), _ in sorted_docs[: self.k]:
                        for d in docs_a + docs_b:
                            if (d.page_content[:200], d.metadata.get("source", "")) == (content_prefix, src):
                                out.append(d)
                                break
                    return out[: self.k]

            base_retriever = _HybridRetriever()
            print("Гибридный RAG готов! (BM25 + Pinecone, RRF, k=%d)" % _hybrid_k)
    except Exception as e:
        print(f"BM25 не запустился: {e}. Используется только Pinecone.")
elif _chunks is None:
    print("BM25 отключён: нет чанков. Запустите: python build_vector_db.py")
elif BM25Retriever is None:
    print("BM25 отключён: langchain_community.retrievers.BM25Retriever не найден. Установите: pip install langchain-community rank_bm25")

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

llm = OllamaLLM(
    model=config.LLM_MODEL,
    temperature=config.LLM_TEMPERATURE,
    base_url=config.OLLAMA_BASE_URL,
)

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
    question = "Какие основные принципы трудового законодательства Республики Казахстан?"
    print(f"\nВопрос: {question}\n")
    docs = retriever.invoke(question)
    for i, doc in enumerate(docs[:5], 1):
        print(f"{i}. {doc.metadata.get('source')} | {doc.metadata.get('code_ru', '')} ст.{doc.metadata.get('article_number', '')}")
        print(f"   {doc.page_content[:250].replace(chr(10), ' ')}...\n")
    result = qa_chain.invoke({"query": question})
    print("Ответ:", result["result"][:500])
