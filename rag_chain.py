# rag_chain.py — синхронизировано с build_vector_db.py

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate

# Та же обёртка с префиксами (обязательно!)
class PrefixedEmbeddings:
    def __init__(self, embeddings):
        self.embeddings = embeddings

    def embed_documents(self, texts):
        return self.embeddings.embed_documents(["passage: " + t for t in texts])

    def embed_query(self, text):
        return self.embeddings.embed_query("query: " + text)

embeddings = PrefixedEmbeddings(HuggingFaceEmbeddings(
    model_name="intfloat/multilingual-e5-large",
    encode_kwargs={"normalize_embeddings": True}
))

vector_store = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings,
    collection_name="legal_kz_2026"  # должно быть то же имя, что в build_vector_db.py
)

print(f"База подключена. Чанков в коллекции: {vector_store._collection.count()}")

llm = OllamaLLM(model="llama3.1:8b", temperature=0.0, base_url="http://localhost:11434")

prompt_template = """Ты — точный ассистент по законам РК.
ОТВЕЧАЙ ТОЛЬКО НА ОСНОВЕ КОНТЕКСТА НИЖЕ.
Если контекст пуст — отвечай ровно: "Информация не найдена в доступных текстах законов."

Начинай с: "Это не официальная юридическая консультация. Информация только из базы."

Контекст:
{context}

Вопрос: {question}

Ответ (с номерами статей и источниками):"""

PROMPT = PromptTemplate.from_template(prompt_template)

retriever = vector_store.as_retriever(search_kwargs={"k": 10})

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True,
    chain_type_kwargs={"prompt": PROMPT}
)

if __name__ == "__main__":
    question = "Какие основные принципы трудового законодательства Республики Казахстан?"
    print(f"\nВопрос: {question}\n")

    print("=== Отладка: Топ-5 по запросу ===")
    docs = vector_store.similarity_search(question, k=5)
    if not docs:
        print("НИЧЕГО НЕ НАЙДЕНО")
    else:
        for i, doc in enumerate(docs, 1):
            print(f"{i}. {doc.metadata.get('source')}")
            print(f"   {doc.page_content[:300].replace('\n', ' ')}...\n")

    result = qa_chain.invoke({"query": question})

    print("\nОтвет модели:")
    print("-" * 80)
    print(result["result"])
    print("-" * 80)

    print("\nИсточники:")
    for i, doc in enumerate(result["source_documents"], 1):
        print(f"  {i}. {doc.metadata.get('source')}")
        print(f"     {doc.page_content[:300].replace('\n', ' ')}...\n")