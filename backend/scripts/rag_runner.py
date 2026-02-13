import json
import sys

from rag_chain import invoke_qa, validate_answer


def main() -> int:
    raw = sys.stdin.read()
    if not raw:
        print(json.dumps({"error": "missing_input"}))
        return 1
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        print(json.dumps({"error": "invalid_json"}))
        return 1

    prompt = payload.get("prompt", "").strip()
    if not prompt:
        print(json.dumps({"error": "missing_prompt"}))
        return 1

    try:
        result = invoke_qa(prompt)
        response = result["result"]
        sources = result.get("source_documents", [])
        response = validate_answer(prompt, response, sources)
    except Exception as exc:
        print(json.dumps({"error": "rag_exception", "details": str(exc)}))
        return 1

    safe_sources = []
    if response != "Информация не найдена в доступных текстах законов.":
        for doc in sources:
            meta = doc.metadata or {}
            safe_sources.append(
                {
                    "source": meta.get("source", ""),
                    "code_ru": meta.get("code_ru", ""),
                    "article_number": meta.get("article_number", ""),
                    "preview": doc.page_content[:280].replace("\n", " ").strip(),
                }
            )

    print(json.dumps({"response": response, "sources": safe_sources}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
