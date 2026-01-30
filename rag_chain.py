# rag_chain.py — гибридный retriever (BM25 + семантика), reranker, строгий промпт

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate

import config

# Та же обёртка с префиксами (E5 instruct)
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

vector_store = Chroma(
    persist_directory=str(config.CHROMA_DIR),
    embedding_function=embeddings,
    collection_name=config.COLLECTION_NAME,
)

def _get_chunk_count():
    try:
        return vector_store._collection.count()
    except Exception:
        return 0

print(f"База подключена. Чанков в коллекции: {_get_chunk_count()}")

# Базовый векторный retriever
vector_retriever = vector_store.as_retriever(
    search_kwargs={"k": config.RETRIEVER_TOP_K}
)

# Гибрид: BM25 + векторный (опционально; чанки из prepare_data)
base_retriever = vector_retriever
try:
    from langchain_community.retrievers import BM25Retriever
    try:
        from langchain.retrievers.ensemble import EnsembleRetriever
    except ImportError:
        try:
            from langchain.retrievers import EnsembleRetriever
        except ImportError:
            EnsembleRetriever = None
    import prepare_data
    _chunks = getattr(prepare_data, "chunks", None)
    if _chunks and EnsembleRetriever is not None:
        bm25_retriever = BM25Retriever.from_documents(
            _chunks,
            k=config.RETRIEVER_TOP_K,
        )
        base_retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, vector_retriever],
            weights=[config.BM25_WEIGHT, config.VECTOR_WEIGHT],
        )
        print("Гибридный retriever (BM25 + семантика) включён.")
    elif _chunks:
        # Fallback: свой гибрид через RRF (reciprocal rank fusion)
        from langchain_core.retrievers import BaseRetriever
        from langchain_core.callbacks import CallbackManagerForRetrieverRun
        from langchain_core.documents import Document
        _bm25 = BM25Retriever.from_documents(_chunks, k=config.RETRIEVER_TOP_K)

        class _HybridRetriever(BaseRetriever):
            retriever_a = vector_retriever
            retriever_b = _bm25
            k = config.RETRIEVER_TOP_K
            c = 60  # RRF constant

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
        print("Гибридный retriever (BM25 + семантика, RRF) включён.")
except Exception as e:
    print(f"BM25/Ensemble недоступен, используется только векторный поиск: {e}")

# Reranker (FlashRank) — опционально
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
                compressor = FlashrankRerank(
                    model=model_name,
                    top_n=config.RETRIEVER_TOP_K_AFTER_RERANK,
                )
                break
            except Exception:
                continue
        if compressor is not None:
            retriever = ContextualCompressionRetriever(
                base_compressor=compressor,
                base_retriever=base_retriever,
            )
            print("Reranker FlashRank включён.")
        else:
            print("FlashRank: не удалось загрузить модель, reranker отключён.")
    except Exception as e:
        print(f"FlashRank недоступен, reranker отключён: {e}")

# Если reranker не использовался, ограничиваем число документов для цепи
if not config.USE_RERANKER and base_retriever is not retriever:
    pass
else:
    # retriever уже возвращает top_n после rerank или просто top_k
    pass

llm = OllamaLLM(
    model=config.LLM_MODEL,
    temperature=config.LLM_TEMPERATURE,
    base_url=config.OLLAMA_BASE_URL,
)

# Строгий промпт: только контекст, запрет галлюцинаций, дисклеймер, прозрачность (AI-закон РК)
prompt_template = """Ты — точный ассистент по законам Республики Казахстан.
ПРАВИЛА (строго):
1. ОТВЕЧАЙ ТОЛЬКО на основе контекста ниже. Не придумывай статей и норм.
2. Если в контексте нет ответа — ответь ровно: "Информация не найдена в доступных текстах законов."
3. Начинай ответ с дисклеймера: "Это не официальная юридическая консультация. Информация только из базы."
4. Указывай номера статей и кодексы из контекста. Не ссылайся на то, чего нет в контексте.
5. Ответ должен быть прозрачным и не манипулятивным (соответствие требованиям к ИИ в РК).

Контекст (выдержки из законов РК):
{context}

Вопрос: {question}

Ответ (с номерами статей и источниками, только по контексту):"""

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
    print("=== Топ документов по запросу ===")
    docs = retriever.invoke(question)
    k_show = min(5, len(docs) if isinstance(docs, list) else 0)
    if isinstance(docs, list) and docs:
        for i, doc in enumerate(docs[:k_show], 1):
            src = doc.metadata.get("source", "?")
            code_ru = doc.metadata.get("code_ru", "")
            art = doc.metadata.get("article_number", "")
            print(f"{i}. {src} | {code_ru} ст.{art}")
            print(f"   {doc.page_content[:280].replace(chr(10), ' ')}...\n")
    result = qa_chain.invoke({"query": question})
    print("\nОтвет модели:")
    print("-" * 80)
    print(result["result"])
    print("-" * 80)
    print("\nИсточники:")
    for i, doc in enumerate(result["source_documents"], 1):
        print(f"  {i}. {doc.metadata.get('source')} | {doc.metadata.get('code_ru', '')} ст.{doc.metadata.get('article_number', '')}")
