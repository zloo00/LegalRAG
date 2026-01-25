# prepare_data.py (обновлённый)
import re
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import TextSplitter

# Кастомный splitter по статьям
class ArticleTextSplitter(TextSplitter):
    """Splitter для разделения юридических текстов по статьям."""

    def split_text(self, text: str) -> list[str]:
        # Regex для детекции начала статьи: "Статья N." или вариации
        # Адаптировано для русского/казахского: Статья|Мәтін|Article + номер + точка/пробел
        article_pattern = re.compile(
            r'(?m)^(Статья|Стаття|Мәтін|Article|Section)\s*(\d+[а-яА-Яa-zA-Z]?)\.?\s*(.*?$)',
            re.IGNORECASE | re.DOTALL
        )

        # Находим все матчи
        matches = list(article_pattern.finditer(text))
        if not matches:
            # Если нет статей, fallback на весь текст как один чанк
            return [text]

        chunks = []
        prev_end = 0
        for match in matches:
            start = match.start()
            if start > prev_end:
                # Добавляем текст перед первой статьёй (преамбула, заголовок)
                chunks.append(text[prev_end:start].strip())
            # Добавляем саму статью: от начала до следующей
            next_start = matches[matches.index(match) + 1].start() if matches.index(match) + 1 < len(matches) else len(text)
            article_text = text[start:next_start].strip()
            chunks.append(article_text)
            prev_end = next_start

        # Фильтр пустых чанков
        chunks = [c for c in chunks if c and len(c) > 50]  # Минимум 50 символов

        return chunks

    def create_documents(self, texts: list[str], metadatas: list[dict] = None) -> list[Document]:
        """Преобразовать тексты в Document с метаданными."""
        _metadatas = metadatas or [{} for _ in texts]
        documents = []
        for i, text in enumerate(texts):
            for chunk in self.split_text(text):
                new_doc = Document(page_content=chunk, metadata=_metadatas[i])
                documents.append(new_doc)
        return documents

# Загрузка документов (как раньше)
loader = DirectoryLoader(
    "./documents/",
    glob="**/*.txt",
    loader_cls=TextLoader,
    loader_kwargs={"encoding": "utf-8"}
)
raw_docs = loader.load()

# Используем кастомный splitter
article_splitter = ArticleTextSplitter()

# Разделяем
chunks = article_splitter.create_documents([doc.page_content for doc in raw_docs], [doc.metadata for doc in raw_docs])

print(f"Всего документов: {len(raw_docs)}")
print(f"Всего чанков (статей): {len(chunks)}")
# Пример: вывести первую чанку
if chunks:
    print("Пример чанка:\n", chunks[0].page_content[:300], "...")