# Legal RAG — законы РК

Retrieval-augmented generation по кодексам РК (ТК, ГК, НК, КоАП, Конституция и др.): локально, мультиязычность (RU/KZ), минимум галлюцинаций, соответствие требованиям к ИИ (прозрачность).

## Цели

- **Точность >95%** — без выдуманных статей
- **Faithfulness >98%** — ответы только из контекста
- **Поддержка казахского** (low-resource)
- **Прозрачность** — дисклеймер, источники, соответствие закону РК об ИИ

## Стек

- **Данные:** кодексы РК в `documents/*.txt`, метаданные (номер статьи, кодекс)
- **Эмбеддинги:** multilingual-e5-large (или Jina v3)
- **Retriever:** гибрид BM25 + семантика, опционально FlashRank reranker
- **Graph RAG:** связи статей (статья X → ст. Y), см. `graph_rag.py`; опционально Neo4j
- **LLM:** Llama 3.1 8B / Gemma2 9B через Ollama (локально)
- **UI:** Streamlit, переключатель RU/KZ

## Запуск

1. Установка зависимостей:
   ```bash
   pip install -r requirements.txt
   ```

2. Сборка векторной базы (один раз):
   ```bash
   python build_vector_db.py
   ```

3. Граф ссылок между статьями (опционально):
   ```bash
   python graph_rag.py
   ```

4. Запуск Ollama и модель, например:
   ```bash
   ollama run llama3.1:8b
   ```

5. Интерфейс:
   ```bash
   streamlit run app.py
   ```

6. Бенчмарк (Accuracy, Faithfulness, ROUGE):
   ```bash
   python benchmark.py
   ```
   Результаты и метрики — в `benchmark_results/`. Для ROUGE добавьте эталоны в `benchmark_references.json` (ключ = номер вопроса, значение = эталонный ответ).

## Настройки

- `config.py` — пути, модели, веса BM25/vector, reranker, дисклеймеры
- Переменные окружения: `LEGAL_RAG_EMBEDDING`, `LEGAL_RAG_LLM`, `LEGAL_RAG_USE_RERANKER`, `LEGAL_RAG_USE_GRAPH`, `OLLAMA_HOST`

## Безопасность

- В ответах всегда присутствует дисклеймер: «Это не официальная юридическая консультация».
- Источники указываются для проверки (требования прозрачности ИИ в РК).

## Структура

- `prepare_data.py` — загрузка и разбиение по статьям, метаданные (code_ru, code_kz, article_number)
- `build_vector_db.py` — Chroma + эмбеддинги
- `rag_chain.py` — гибридный retriever, reranker, промпт, QA-цепочка
- `graph_rag.py` — граф ссылок статей, опционально Neo4j
- `benchmark.py` — вопросы, таймауты, автоматические метрики (trap accuracy, faithfulness, ROUGE-L)
- `app.py` — Streamlit: чат, RU/KZ, дисклеймер, источники
