# graph_rag.py — связи между статьями (статья X ссылается на ст. Y)
# In-memory граф ссылок; опционально Neo4j для масштабирования.

import re
import json
from pathlib import Path
from typing import Optional

# Паттерны ссылок на статьи в текстах законов РК (рус/каз)
# Примеры: "статья 76", "ст. 4", "согласно статье 15", "статья 4 Трудового кодекса"
ARTICLE_REF = re.compile(
    r"(?:статья|стаття|ст\.|мақала|статье|статьи|статьей)\s*(\d+[а-яА-Яa-zA-Z]?)",
    re.IGNORECASE
)
# Кодексы для нормализации (сокращения)
CODE_ALIASES = {
    "тк": "labor_code", "трудовой": "labor_code", "еңбек": "labor_code",
    "гк": "civil_code", "гражданский": "civil_code", "азаматтық": "civil_code",
    "нк": "tax_code", "налоговый": "tax_code", "салық": "tax_code",
    "ук": "criminal_code", "уголовный": "criminal_code", "қылмыстық": "criminal_code",
    "коап": "code_of_administrative_offenses", "административн": "code_of_administrative_offenses",
    "конституц": "constitution", "брак": "code_on_marriage_and_family", "неке": "code_on_marriage_and_family",
}


def extract_article_refs(text: str) -> list[str]:
    """Извлекает номера статей, на которые есть ссылка в тексте (например '76', '4')."""
    return list(dedupe(ARTICLE_REF.findall(text)))


def dedupe(seq):
    seen = set()
    for x in seq:
        if x not in seen:
            seen.add(x)
            yield x


def build_ref_graph(chunks: list, doc_id_key: str = "source") -> dict:
    """
    Строит граф ссылок: для каждого doc (по source + article_number) — список (code, art_num) на которые ссылается.
    chunks — list of LangChain Document с metadata code_ru/code_kz, article_number, source.
    Возвращает: { "source::article_number": ["code_ru::art_num", ...], ... }
    """
    graph = {}
    for doc in chunks:
        meta = getattr(doc, "metadata", {}) or {}
        source = meta.get("source", "")
        art = meta.get("article_number")
        code_ru = meta.get("code_ru", "")
        if not source:
            continue
        node = f"{source}::{art}" if art else source
        refs = extract_article_refs(doc.page_content)
        # Нормализуем ссылки: оставляем как (code_ru, art_num); тот же кодекс по умолчанию
        ref_list = []
        for r in refs:
            ref_list.append(f"{code_ru}::{r}" if code_ru else r)
        if ref_list:
            graph[node] = ref_list
    return graph


def get_related_refs(
    node: str,
    graph: dict,
    max_refs: int = 5,
) -> list[str]:
    """
    По ключу узла (source::article_number) возвращает список ссылок из графа.
    Можно использовать для расширения контекста: подтянуть текст статей, на которые ссылается найденная статья.
    """
    return list(graph.get(node, []))[:max_refs]


def save_graph(graph: dict, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)


def load_graph(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# Опционально: Neo4j (установи neo4j и задай NEO4J_URI)
def push_graph_to_neo4j(graph: dict, uri: str, user: str, password: str) -> None:
    try:
        from neo4j import GraphDatabase
    except ImportError:
        raise ImportError("Установите neo4j: pip install neo4j")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (a:Article) REQUIRE a.id IS UNIQUE")
        for node, refs in graph.items():
            for ref in refs:
                session.run(
                    "MERGE (a:Article {id: $from}) MERGE (b:Article {id: $to}) MERGE (a)-[:REFERENCES]->(b)",
                    {"from": node, "to": ref},
                )
    driver.close()


if __name__ == "__main__":
    from prepare_data import chunks
    g = build_ref_graph(chunks)
    out = Path(__file__).resolve().parent / "article_ref_graph.json"
    save_graph(g, out)
    print(f"Граф сохранён: {out}, узлов: {len(g)}")
