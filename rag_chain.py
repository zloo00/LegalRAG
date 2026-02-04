# rag_chain.py — Pinecone + BM25, reranker, строгий промпт

import pickle
import os
import re
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

_hybrid_k = getattr(config, "RETRIEVER_WIDE_K", getattr(config, "HYBRID_K", 8))
_vector_kwargs = {"k": _hybrid_k}

# Расширенные фильтры Pinecone:
# - по кодексу: ловит варианты названия (УК РК, Қылмыстық кодекс и т.д.)
# - по номеру статьи: например, 136 для кейса акушерки (баланы ауыстыру)
_filter_code = getattr(config, "RETRIEVER_FILTER_CODE_RU", None)
_filter_article = getattr(config, "RETRIEVER_FILTER_ARTICLE_NUMBER", None)
_uk_variants = [
    "Уголовный кодекс РК",
    "Уголовный кодекс Республики Казахстан",
    "Қылмыстық кодекс",
    "УК РК",
]
_allowed_code_ru_for_filter = None
_filter_clauses: list[dict] = []

if _filter_code:
    # Pinecone не поддерживает $regex — используем $or по известным вариантам
    _variants = list(dict.fromkeys([_filter_code] + [v for v in _uk_variants if v != _filter_code]))
    _allowed_code_ru_for_filter = _variants
    _filter_clauses.append({"$or": [{"code_ru": v} for v in _variants]})

if _filter_article:
    # Точный номер статьи хранится как строка в metadata["article_number"]
    _filter_clauses.append({"article_number": _filter_article})

if _filter_clauses:
    if len(_filter_clauses) == 1:
        _vector_kwargs["filter"] = _filter_clauses[0]
    else:
        _vector_kwargs["filter"] = {"$and": _filter_clauses}
    # При включённых фильтрах немного увеличиваем k для надёжности
    _vector_kwargs["k"] = min(getattr(config, "RETRIEVER_WIDE_K", getattr(config, "HYBRID_K", 8)) + 4, 30)
    print(f"Фильтр Pinecone search_kwargs: {_vector_kwargs.get('filter')}")

_vector_retriever = vector_store.as_retriever(search_kwargs=_vector_kwargs)


class _FilterByCodeRetriever(BaseRetriever):
    """Оставляет только документы с разрешённым code_ru и/или article_number (убирает шум от BM25)."""
    retriever: Any
    allowed_code_ru: List[str] | None = None
    article_number: str | None = None

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun | None = None
    ) -> List[Document]:
        docs = self.retriever.invoke(query)
        filtered = docs

        if self.allowed_code_ru:
            allowed = set(self.allowed_code_ru)
            filtered = [d for d in filtered if (d.metadata.get("code_ru") or "").strip() in allowed]

        if self.article_number:
            filtered = [d for d in filtered if (d.metadata.get("article_number") or "").strip() == self.article_number]

        return filtered if filtered else docs[:5]  # fallback: хоть что-то вернуть


def _extract_article_range(query: str) -> tuple[int, int] | None:
    match = re.search(r"(?:статья|ст\.|ст|бап)?\s*(\d+)\s*[-–—]\s*(\d+)", query or "", re.IGNORECASE)
    if not match:
        return None
    start = int(match.group(1))
    end = int(match.group(2))
    return (start, end) if start <= end else (end, start)


def _augment_retrieval_query(query: str) -> str:
    q = (query or "").lower()
    extras: list[str] = []
    if any(token in q for token in ("баланы ауыстыру", "ауыстыр", "нәресте", "білезік", "подмена ребенка")):
        extras.append("подмена ребенка статья 136 УК РК")
    if any(token in q for token in ("субсид", "субсидия", "гос", "государ", "бюджет", "грант", "инвест", "смет", "договор", "фиктив", "жалған", "құжат", "алаяқ", "мемлекеттік", "қаржы", "ақша")):
        extras.append("алаяқтық 190 УК РК")
        extras.append("қылмыстық жолмен алынған ақшаны заңдастыру 218 УК РК")
        extras.append("субсидия алу үшін жалған құжаттар 190 УК РК")
    if any(token in q for token in ("заңсыз кәсіпкер", "кәсіпкерлік", "лицензиясыз", "тіркеусіз", "незаконн", "без регистрации", "без лицензии", "салық төлем", "налог", "уклонен")):
        extras.append("заңсыз кәсіпкерлік 214 УК РК")
        extras.append("салық төлеуден жалтару 245 УК РК")
    if any(token in q for token in ("пирамида", "пирамид", "қаржылық пирамида", "инвестиция", "инвест", "жоғары пайда", "30-50%")):
        extras.append("қаржылық пирамида құру және басқару 217 УК РК")
        extras.append("финансовая пирамида создание и руководство 217 УК РК")
        extras.append("реклама финансовой пирамиды 217-1 УК РК")
    range_match = _extract_article_range(query)
    if range_match and ("ук" in q or "қылмыстық" in q or "уголов" in q):
        start, end = range_match
        nums = " ".join(str(n) for n in range(start, end + 1))
        extras.append(f"статьи {nums} УК РК")
    return (query + " " + " ".join(extras)).strip() if extras else query


def _is_criminal_query(query: str) -> bool:
    q = (query or "").lower()
    return any(token in q for token in ("қылмыстық", "уголов", "преступ", "ук рк"))


def _focus_articles_from_query(query: str) -> set[str]:
    q = (query or "").lower()
    focus: set[str] = set()
    if any(token in q for token in ("субсид", "субсидия", "гос", "государ", "бюджет", "грант", "инвест", "смет", "договор", "фиктив", "мемлекеттік", "жалған", "алаяқ", "құжат", "қаржы", "ақша")):
        focus.update({"190", "218"})
    if any(token in q for token in ("заңсыз кәсіпкер", "кәсіпкерлік", "лицензиясыз", "тіркеусіз", "незаконн", "без регистрации", "без лицензии", "салық төлем", "налог", "уклонен")):
        focus.update({"214", "245"})
    if any(token in q for token in ("пирамида", "пирамид", "қаржылық пирамида", "инвестиция", "инвест", "жоғары пайда", "30-50%")):
        focus.update({"217", "190"})
    return focus


def _is_subsidy_query(query: str) -> bool:
    q = (query or "").lower()
    return any(token in q for token in ("субсид", "субсидия", "грант", "гос", "государ", "мемлекеттік", "бюджет"))


def _is_illegal_business_query(query: str) -> bool:
    q = (query or "").lower()
    return any(token in q for token in ("заңсыз кәсіпкер", "кәсіпкерлік", "лицензиясыз", "тіркеусіз", "незаконн", "без регистрации", "без лицензии", "салық төлем", "налог", "уклонен"))


def _is_pyramid_query(query: str) -> bool:
    q = (query or "").lower()
    return any(token in q for token in ("пирамида", "пирамид", "қаржылық пирамида", "инвестиция", "инвест", "жоғары пайда", "30-50%"))


def _needs_circumstances_query(query: str) -> bool:
    q = (query or "").lower()
    return any(token in q for token in ("ауырлататын", "жеңілдететін", "смягча", "отягча"))


def _doc_key(doc: Document) -> tuple[str, str]:
    return (
        str(doc.metadata.get("source", "")).strip(),
        str(doc.metadata.get("article_number", "")).strip(),
    )


def _merge_unique(base: List[Document], extra: List[Document]) -> List[Document]:
    seen = {_doc_key(d) for d in base}
    merged = list(base)
    for d in extra:
        key = _doc_key(d)
        if key not in seen:
            merged.append(d)
            seen.add(key)
    return merged


class _HeuristicRetriever(BaseRetriever):
    """Лёгкий эвристический слой: расширяет запрос и мягко фильтрует диапазоны статей."""
    base_retriever: Any
    vector_store: Any

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun | None = None
    ) -> List[Document]:
        search_query = _augment_retrieval_query(query)
        docs = self.base_retriever.invoke(search_query)
        uk_filter = {"$or": [{"code_ru": v} for v in _uk_variants]}
        if _is_criminal_query(query):
            allowed = set(_uk_variants)
            filtered = [d for d in docs if (d.metadata.get("code_ru") or "").strip() in allowed]
            if filtered:
                docs = filtered
            else:
                fallback_docs: list[Document] = []
                for code_ru in _uk_variants:
                    try:
                        fallback_docs.extend(
                            self.vector_store.similarity_search(
                                search_query,
                                k=6,
                                filter={"code_ru": code_ru},
                            )
                        )
                    except Exception:
                        continue
                if fallback_docs:
                    docs = fallback_docs
        range_match = _extract_article_range(query)
        if range_match:
            start, end = range_match
            filtered = [
                d for d in docs
                if (d.metadata.get("article_number") or "").strip().isdigit()
                and start <= int(d.metadata.get("article_number")) <= end
            ]
            return filtered if filtered else docs
        focus = _focus_articles_from_query(query)
        if focus:
            focused = [
                d for d in docs
                if (d.metadata.get("article_number") or "").strip() in focus
            ]
            return focused if focused else docs
        return docs


class _LawAwareRetriever(BaseRetriever):
    """Жёсткий law-aware слой: для УК — принудительная подвыборка + добор статей."""
    base_retriever: Any
    vector_store: Any
    min_k_criminal: int = 10

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun | None = None
    ) -> List[Document]:
        search_query = _augment_retrieval_query(query)
        docs = self.base_retriever.invoke(search_query)
        uk_filter = {"$or": [{"code_ru": v} for v in _uk_variants]}

        if _is_criminal_query(query):
            allowed = set(_uk_variants)
            filtered = [d for d in docs if (d.metadata.get("code_ru") or "").strip() in allowed]
            docs = filtered if filtered else docs
            if len(docs) < self.min_k_criminal:
                extra: list[Document] = []
                for code_ru in _uk_variants:
                    try:
                        extra.extend(
                            self.vector_store.similarity_search(
                                search_query,
                                k=self.min_k_criminal,
                                filter={"code_ru": code_ru},
                            )
                        )
                    except Exception:
                        continue
                if extra:
                    docs = _merge_unique(docs, extra)

        if _needs_circumstances_query(query):
            extra_docs: list[Document] = []
            for q in (
                "смягчающие обстоятельства УК РК",
                "отягчающие обстоятельства УК РК",
                "жеңілдететін мән-жайлар Қылмыстық кодекс",
                "ауырлататын мән-жайлар Қылмыстық кодекс",
            ):
                try:
                    extra_docs.extend(
                        self.vector_store.similarity_search(
                            q,
                            k=4,
                            filter=uk_filter,
                        )
                    )
                except Exception:
                    continue
            if extra_docs:
                docs = _merge_unique(docs, extra_docs)

        return docs


class _TrimRetriever(BaseRetriever):
    """Обрезает количество и длину документов перед LLM, чтобы избежать переполнения контекста."""
    base_retriever: Any
    max_docs: int = 8
    max_chars_per_doc: int = 1800

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun | None = None
    ) -> List[Document]:
        docs = self.base_retriever.invoke(query)
        trimmed: list[Document] = []
        for d in docs[: self.max_docs]:
            content = d.page_content
            if len(content) > self.max_chars_per_doc:
                content = content[: self.max_chars_per_doc] + "\n[...текст обрезан...]"
            trimmed.append(Document(page_content=content, metadata=d.metadata))
        return trimmed


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

if _allowed_code_ru_for_filter or _filter_article:
    base_retriever = _FilterByCodeRetriever(
        retriever=base_retriever,
        allowed_code_ru=_allowed_code_ru_for_filter,
        article_number=_filter_article,
    )
    print("Включён пост-фильтр по кодексу/статье (только разрешённые code_ru/article_number).")

# Эвристический слой для запроса/пост-фильтра
heuristic_retriever = _HeuristicRetriever(base_retriever=base_retriever, vector_store=vector_store)
# Law-aware слой (для УК и обстоятельств)
law_aware_retriever = _LawAwareRetriever(
    base_retriever=heuristic_retriever,
    vector_store=vector_store,
    min_k_criminal=getattr(config, "RETRIEVER_MIN_K_CRIMINAL", 10),
)
retriever = law_aware_retriever
# ------------------- УЛУЧШЕННЫЙ RERANKER -------------------
if config.USE_RERANKER:
    try:
        try:
            from langchain_community.retrievers import ContextualCompressionRetriever
        except ImportError:
            from langchain_classic.retrievers.contextual_compression import ContextualCompressionRetriever
        from langchain_community.document_compressors import FlashrankRerank

        print("Попытка инициализации FlashRank reranker...")

        # Список моделей по убыванию качества (rank-T5-flan — самая сильная для юридического текста)
        rerank_model_priority = [
            "rank-T5-flan",
            "ms-marco-MiniLM-L-12-v2",
            "ms-marco-TinyBERT-L-2-v2",
        ]

        compressor = None
        used_model = None

        for model_name in rerank_model_priority:
            try:
                compressor = FlashrankRerank(
                    model=model_name,
                    top_n=config.RETRIEVER_TOP_K_AFTER_RERANK or 6,
                    max_length=1024,
                )
                used_model = model_name
                print(f"Успешно запущен FlashRank reranker: {model_name}")
                break
            except Exception as exc:
                print(f"Модель {model_name} не запустилась: {exc}")
                continue

        if compressor is not None:
            retriever = ContextualCompressionRetriever(
                base_compressor=compressor,
                base_retriever=law_aware_retriever,
            )
            print(f"Reranker включён (модель: {used_model}, top_n: {compressor.top_n})")
        else:
            print("Ни одна модель FlashRank не запустилась → reranker отключён.")

    except ImportError as ie:
        print(
            f"Ошибка импорта: {ie}. Установите langchain-community и flashrank "
            f"(и при необходимости langchain-classic): pip install langchain-community flashrank langchain-classic"
        )
    except Exception as e:
        print(f"Reranker полностью отключён из-за ошибки: {e}")
else:
    print("Reranker отключён в config (USE_RERANKER=False)")

# Обрезка контекста перед LLM (для защиты от слишком длинных запросов)
retriever = _TrimRetriever(
    base_retriever=retriever,
    max_docs=getattr(config, "CONTEXT_MAX_DOCS", 8),
    max_chars_per_doc=getattr(config, "CONTEXT_MAX_CHARS_PER_DOC", 1800),
)

# Выбор LLM: локальная Ollama или облачный Groq (\"облачный оллама\")
_llm_backend = os.environ.get("LEGAL_RAG_LLM_BACKEND", "groq").lower()
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
        max_tokens=config.LLM_MAX_TOKENS,
    )
    print(f"LLM: Groq (model={config.LLM_MODEL})")
else:
    from langchain_ollama import OllamaLLM

    llm = OllamaLLM(
        model=config.LLM_MODEL,
        temperature=config.LLM_TEMPERATURE,
        base_url=config.OLLAMA_BASE_URL,
        num_predict=config.LLM_MAX_TOKENS,
    )
    print(f"LLM: Ollama локально (model={config.LLM_MODEL})")

prompt_template = """Ты — точный юридический ассистент по законам РК.
ОТВЕЧАЙ СТРОГО НА ОСНОВЕ КОНТЕКСТА НИЖЕ.
НИКОГДА НЕ ПРИДУМЫВАЙ номера статей, названия, пункты, даты или выводы, которых нет в контексте.
Если в контексте нет ответа — отвечай ровно одной строкой: "Информация не найдена в доступных текстах законов."
Если вопрос на казахском — отвечай только на казахском, используя точные формулировки НҚА.
Для уголовных дел проверяй УК РК и указывай точную статью и санкцию ТОЛЬКО если они есть в контексте.
Случаи подлога/обмана для получения субсидий, грантов, госфинансирования квалифицируй как алаяқтық (ст. 190 УК РК) и при наличии легализации — ст. 218 УК РК. Не применяй ст. 216 УК РК (счета-фактуры) к таким кейсам.
Случаи заңсыз кәсіпкерлік (тіркеусіз/лицензиясыз кәсіп, үлкен айналым) — ст. 214 УК РК, салық төлеуден жалтару — ст. 245 УК РК. Не путай с мошенничеством (ст. 190 УК РК).
Қаржылық пирамида (жаңа салымшылар есебінен төлем, нақты қызмет жоқ, көп жәбірленуші) — ст. 217 УК РК (құру және басқару); ст. 217-1 — ТЕК жарнама үшін. Негізгі бап ретінде 217-1 қолданба.
Разрешён краткий правовой анализ (объект/объективная сторона/субъект/субъективная сторона, смягчающие/отягчающие), но только если есть опора на извлечённые статьи.
Ответ оформляй по пунктам 1–5, как в вопросе, с короткими заголовками каждого пункта.
Если в вопросе указан номер статьи — цитируй именно эту статью дословно, без пересказа.
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

_KZ_CHARS = set("әғқңөұүһі")
_KZ_COMMON_WORDS = (
    "және", "бойынша", "қылмыстық", "құрамы", "қылмысқа", "бап", "заң", "мән-жай", "ауырлататын", "жеңілдететін"
)


def _is_kz_query(query: str) -> bool:
    return any(ch in (query or "").lower() for ch in _KZ_CHARS)


def _is_kz_response(text: str) -> bool:
    t = (text or "").lower()
    if any(ch in t for ch in _KZ_CHARS):
        return True
    return any(word in t for word in _KZ_COMMON_WORDS)


def _extract_article_numbers_from_docs(docs: List[Document]) -> set[str]:
    nums: set[str] = set()
    for d in docs or []:
        art = (d.metadata.get("article_number") or "").strip()
        if art.isdigit():
            nums.add(art)
    return nums


def _extract_article_numbers_from_text(text: str) -> set[str]:
    nums: set[str] = set()
    if not text:
        return nums
    for m in re.finditer(r"(?:статья|ст\.|ст|бап)\s*(\d{1,4})", text.lower()):
        nums.add(m.group(1))
    return nums


def validate_answer(question: str, response: str, sources: List[Document]) -> str:
    if not sources:
        return "Ақпарат қолжетімді заң мәтіндерінде табылмады." if _is_kz_query(question) else "Информация не найдена в доступных текстах законов."

    if _is_kz_query(question) and not _is_kz_response(response):
        return "Ақпарат қолжетімді заң мәтіндерінде табылмады."

    if _is_criminal_query(question):
        has_uk = any((d.metadata.get("code_ru") or "").strip() in _uk_variants for d in sources)
        if not has_uk:
            return "Ақпарат қолжетімді заң мәтіндерінде табылмады." if _is_kz_query(question) else "Информация не найдена в доступных текстах законов."

    allowed = _extract_article_numbers_from_docs(sources)
    mentioned = _extract_article_numbers_from_text(response or "")
    if allowed and mentioned and not mentioned.issubset(allowed):
        return "Ақпарат қолжетімді заң мәтіндерінде табылмады." if _is_kz_query(question) else "Информация не найдена в доступных текстах законов."

    if _is_subsidy_query(question):
        if "190" not in mentioned and "218" not in mentioned:
            return "Ақпарат қолжетімді заң мәтіндерінде табылмады." if _is_kz_query(question) else "Информация не найдена в доступных текстах законов."

    if _is_illegal_business_query(question):
        if "214" not in mentioned and "245" not in mentioned:
            return "Ақпарат қолжетімді заң мәтіндерінде табылмады." if _is_kz_query(question) else "Информация не найдена в доступных текстах законов."

    if _is_pyramid_query(question):
        if "217" not in mentioned:
            return "Ақпарат қолжетімді заң мәтіндерінде табылмады." if _is_kz_query(question) else "Информация не найдена в доступных текстах законов."

    if _needs_circumstances_query(question):
        r = (response or "").lower()
        if not any(token in r for token in ("ауырлататын", "жеңілдететін", "отягча", "смягча")):
            return "Ақпарат қолжетімді заң мәтіндерінде табылмады." if _is_kz_query(question) else "Информация не найдена в доступных текстах законов."

    return response

if __name__ == "__main__":
    question = "Статья 136 УК РК баланы ауыстыру"
    print(f"\nВопрос: {question}\n")
    docs = retriever.invoke(question)
    for i, doc in enumerate(docs[:5], 1):
        print(f"{i}. {doc.metadata.get('source')} | {doc.metadata.get('code_ru', '')} ст.{doc.metadata.get('article_number', '')}")
        print(f"   {doc.page_content[:250].replace(chr(10), ' ')}...\n")
    result = qa_chain.invoke({"query": question})
    print("Ответ:", result["result"][:500])
