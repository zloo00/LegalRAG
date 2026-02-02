# Legal RAG — законы РК

Retrieval-augmented generation по кодексам РК: Pinecone, Adilet, 19 документов, мультиязычность (RU/KZ).

## Стек

- **Данные:** 19 кодексов/законов с **adilet.zan.kz** → `documents/*.txt`
- **Векторная БД:** **Pinecone** (облако)
- **Эмбеддинги:** multilingual-e5-large
- **Retriever:** гибрид BM25 + Pinecone, опционально FlashRank reranker
- **LLM:** Llama 3.1 8B через Ollama (локально)
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

2. **Pinecone:** создайте индекс на [app.pinecone.io](https://app.pinecone.io), задайте:
   ```bash
   export PINECONE_API_KEY=...
   export PINECONE_INDEX_NAME=legal-rag-kz  # опционально
   ```

3. **Загрузка кодексов с Adilet:**
   ```bash
   python fetch_adilet.py
   ```

4. **Сборка базы Pinecone:**
   ```bash
   python build_vector_db.py
   ```

5. **Ollama:**
   ```bash
   ollama run llama3.1:8b
   ```

6. **Интерфейс:**
   ```bash
   streamlit run app.py
   ```

7. **Бенчмарк:**
   ```bash
   python benchmark.py
   ```

## Настройки

- `config.py` — ADILET_SOURCES, Pinecone, веса BM25/vector
- Переменные: `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`, `PINECONE_NAMESPACE`, `LEGAL_RAG_LLM`, `OLLAMA_HOST`
