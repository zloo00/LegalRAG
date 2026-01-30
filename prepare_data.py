# prepare_data.py — метаданные: номер статьи, кодекс (RU/KZ)

import re
from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import TextSplitter

# Маппинг имя_файла -> название кодекса (рус/каз)
CODE_NAMES = {
    "labor_code.txt": ("Трудовой кодекс РК", "Еңбек кодексі"),
    "civil_code.txt": ("Гражданский кодекс РК (ч. 1)", "Азаматтық кодекс (1-бөлім)"),
    "civil_code2.txt": ("Гражданский кодекс РК (ч. 2)", "Азаматтық кодекс (2-бөлім)"),
    "tax_code.txt": ("Налоговый кодекс РК", "Салық кодексі"),
    "criminal_code.txt": ("Уголовный кодекс РК", "Қылмыстық кодекс"),
    "criminal_procedure_code.txt": ("Уголовно-процессуальный кодекс РК", "Қылмыстық іс жүргізу кодексі"),
    "code_of_administrative_offenses.txt": ("Кодекс об административных правонарушениях РК", "Әкімшілік құқық бұзушылықтар туралы кодекс"),
    "constitution.txt": ("Конституция РК", "ҚР Конституциясы"),
    "code_on_marriage_and_family.txt": ("Кодекс о браке и семье РК", "Неке және отбасы туралы кодекс"),
    "code_on_education.txt": ("Кодекс об образовании РК", "Білім туралы кодекс"),
    "code_on_public_health.txt": ("Кодекс о здоровье народа РК", "Халық денсаулығы туралы кодекс"),
    "entrepreneurial_code.txt": ("Предпринимательский кодекс РК", "Кәсіпкерлік кодекс"),
}

# Regex для извлечения номера статьи из начала чанка
ARTICLE_HEADER = re.compile(
    r'^(?:Статья|Стаття|Мәтін|Article|Section)\s*(\d+[а-яА-Яa-zA-Z]?)\.?\s*',
    re.IGNORECASE
)


def get_article_number(chunk_text: str) -> str | None:
    """Извлекает номер статьи из начала текста чанка."""
    m = ARTICLE_HEADER.match(chunk_text.strip())
    return m.group(1) if m else None


def get_code_name(source_path: str) -> tuple[str, str]:
    """По пути файла возвращает (название_рус, название_каз)."""
    name = Path(source_path).name
    return CODE_NAMES.get(name, (name.replace(".txt", ""), name.replace(".txt", "")))


class ArticleTextSplitter(TextSplitter):
    """Splitter для разделения юридических текстов по статьям."""

    def split_text(self, text: str) -> list[str]:
        article_pattern = re.compile(
            r'(?m)^(Статья|Стаття|Мәтін|Article|Section)\s*(\d+[а-яА-Яa-zA-Z]?)\.?\s*(.*?$)',
            re.IGNORECASE | re.DOTALL
        )
        matches = list(article_pattern.finditer(text))
        if not matches:
            return [text]

        chunks = []
        prev_end = 0
        for match in matches:
            start = match.start()
            if start > prev_end:
                chunks.append(text[prev_end:start].strip())
            idx = matches.index(match)
            next_start = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            article_text = text[start:next_start].strip()
            chunks.append(article_text)
            prev_end = next_start

        return [c for c in chunks if c and len(c) > 50]

    def create_documents(self, texts: list[str], metadatas: list[dict] = None) -> list[Document]:
        """Тексты в Document с метаданными: source, code_ru, code_kz, article_number."""
        _metadatas = metadatas or [{} for _ in texts]
        documents = []
        for i, text in enumerate(texts):
            base_meta = dict(_metadatas[i])
            source = base_meta.get("source", "")
            code_ru, code_kz = get_code_name(source)
            for chunk in self.split_text(text):
                meta = {**base_meta, "code_ru": code_ru, "code_kz": code_kz}
                art_num = get_article_number(chunk)
                if art_num is not None:
                    meta["article_number"] = art_num
                new_doc = Document(page_content=chunk, metadata=meta)
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