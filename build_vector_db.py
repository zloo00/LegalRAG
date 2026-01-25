# build_vector_db.py — финальная версия с префиксами и проверкой

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from prepare_data import chunks, raw_docs

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

vector_store = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db",
    collection_name="legal_kz_2026"  # уникальное имя, чтобы не путаться
)

print("База создана!")
print(f"Документов: {len(raw_docs)}")
print(f"Чанков: {len(chunks)}")
print(f"Реальное количество в базе: {vector_store._collection.count()}")

# Тестовый поиск сразу после создания
test_query = "принципы трудового законодательства"
test_results = vector_store.similarity_search(test_query, k=3)
print("\nТестовый поиск после создания:")
for i, doc in enumerate(test_results, 1):
    print(f"{i}. {doc.metadata.get('source')}")
    print(f"   {doc.page_content[:200]}...\n")