# build_vector_db.py — версия для langchain-chroma

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from prepare_data import chunks, raw_docs  # твои чанки

embeddings = HuggingFaceEmbeddings(
    model_name="intfloat/multilingual-e5-large",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

vector_store = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db",
    collection_name="kz_laws"
)

print(f"Векторная база создана с помощью langchain-chroma!")
print(f"Документов: {len(raw_docs)}, чанков: {len(chunks)}")
print(f"Проверка количества в базе: {vector_store._collection.count()}")