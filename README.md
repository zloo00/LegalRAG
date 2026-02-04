# Legal RAG — законы РК

Retrieval-augmented generation по кодексам РК: Pinecone, Adilet, 19 документов, мультиязычность (RU/KZ).

## Стек

- **Данные:** 19 кодексов/законов с **adilet.zan.kz** → `documents/*.txt`
- **Векторная БД:** **Pinecone** (облако)
- **Эмбеддинги:** multilingual-e5-large
- **Retriever:** гибрид BM25 + Pinecone, опционально FlashRank reranker
- **LLM:** Groq (Llama 3.3 70B) по умолчанию, можно переключить на Ollama (локально)
- **UI:** Streamlit, переключатель RU/KZ

## Документы (19)

1. Конституция РК  
2. ГК РК (Общая часть)  
3. ГК РК (Особенная часть)  
4. Трудовой кодекс РК  
5. Налоговый кодекс РК  
6. КоАП РК  
7. Уголовный кодекс РК  
8. Кодекс о браке и семье  
9. Кодекс о здоровье народа  
10. Предпринимательский кодекс РК  
11. Кодекс об административных процедурах  
12. Социальный кодекс РК  
13. ГПК РК  
14. УПК РК  
16. Закон о государственных закупках  
17. Закон о противодействии коррупции  
18. Закон об исполнительном производстве  
19. Закон о персональных данных  
20. Закон об искусственном интеллекте  

## Запуск

1. **Установка:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Настройки через `.env` (рекомендуется):**
   ```bash
   cp .env.example .env
   # затем открой .env и заполни PINECONE_API_KEY и (опционально) GROQ_API_KEY
   ```

   Альтернатива: можно продолжать задавать переменные через `export`, но `.env` удобнее.

3. **Pinecone:** создайте индекс на [app.pinecone.io](https://app.pinecone.io) (или используйте существующий).

4. **Загрузка кодексов с Adilet:**
   ```bash
   python fetch_adilet.py
   ```

5. **Сборка базы Pinecone:**
   ```bash
   python build_vector_db.py
   ```

6. **Groq (по умолчанию):**
   ```bash
   export GROQ_API_KEY="gsk_..."
   ```

7. **Интерфейс:**
   ```bash
   streamlit run app.py
   ```

8. **Бенчмарк:**
   ```bash
   python benchmark.py
   ```

## Настройки

- `config.py` — ADILET_SOURCES, Pinecone, веса BM25/vector, HYBRID_K=8
- Переменные (через `.env` или `export`): `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`, `PINECONE_NAMESPACE`, `LEGAL_RAG_LLM_BACKEND`, `LEGAL_RAG_LLM`, `OLLAMA_HOST`, `GROQ_API_KEY`
- **Тест только по УК РК** (напр. ст. 136 «баланы ауыстыру»):  
  `export LEGAL_RAG_FILTER_CODE_RU="Уголовный кодекс РК"` перед запуском app/benchmark

### Облачный LLM (Groq) — теперь по умолчанию

Чтобы включить “облачный оллама” через Groq:

```bash
export LEGAL_RAG_LLM_BACKEND="groq"
export GROQ_API_KEY="gsk_..."
export LEGAL_RAG_LLM="llama-3.3-70b-versatile"

### Локальный LLM (Ollama)

```bash
export LEGAL_RAG_LLM_BACKEND="ollama"
export LEGAL_RAG_LLM="llama3.1:8b"
ollama run llama3.1:8b
```
```
