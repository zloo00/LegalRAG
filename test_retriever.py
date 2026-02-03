# test_retriever.py
from rag_chain import retriever

docs = retriever.invoke('баланы ауыстыру УК РК')

for i, d in enumerate(docs[:5], 1):
    print(i, d.metadata.get('source'), d.metadata.get('article_number'), d.page_content[:500].replace('\n',' '))